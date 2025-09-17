"""
WebSocket service for real-time DICOM updates and notifications.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import uuid

logger = logging.getLogger(__name__)

class DicomWebSocketService:
    """WebSocket service for real-time DICOM interactions."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.study_subscribers: Dict[str, Set[str]] = {}  # study_uid -> session_ids
        self.user_studies: Dict[str, Set[str]] = {}  # user_id -> study_uids
        
    async def connect(self, websocket: WebSocket, user_id: str = None) -> str:
        """Accept WebSocket connection and return session ID."""
        
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "subscribed_studies": set(),
        }
        
        logger.info(f"DICOM WebSocket connected: session {session_id}, user {user_id}")
        
        # Send welcome message
        await self.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return session_id
    
    def disconnect(self, session_id: str):
        """Disconnect WebSocket session."""
        
        if session_id in self.user_sessions:
            # Unsubscribe from all studies
            subscribed_studies = self.user_sessions[session_id].get("subscribed_studies", set())
            for study_uid in subscribed_studies:
                self._unsubscribe_from_study(session_id, study_uid)
            
            del self.user_sessions[session_id]
        
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        logger.info(f"DICOM WebSocket disconnected: session {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific WebSocket connection."""
        
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if session_id in self.user_sessions:
                    self.user_sessions[session_id]["last_activity"] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error sending DICOM WebSocket message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast_to_study_subscribers(self, study_uid: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a specific study."""
        
        if study_uid in self.study_subscribers:
            for session_id in self.study_subscribers[study_uid].copy():
                await self.send_message(session_id, message)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all sessions of a specific user."""
        
        for session_id, session_data in self.user_sessions.items():
            if session_data.get("user_id") == user_id:
                await self.send_message(session_id, message)
    
    async def broadcast_system_notification(self, message: Dict[str, Any], user_filter: Set[str] = None):
        """Broadcast system notification to all or filtered connections."""
        
        for session_id, session_data in self.user_sessions.items():
            if user_filter is None or session_data.get("user_id") in user_filter:
                await self.send_message(session_id, {
                    "type": "system_notification",
                    **message
                })
    
    async def handle_message(self, session_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe_study":
                await self._handle_subscribe_study(session_id, message)
            elif message_type == "unsubscribe_study":
                await self._handle_unsubscribe_study(session_id, message)
            elif message_type == "subscribe_user_studies":
                await self._handle_subscribe_user_studies(session_id, message)
            elif message_type == "request_preload":
                await self._handle_request_preload(session_id, message)
            elif message_type == "user_activity":
                await self._handle_user_activity(session_id, message)
            elif message_type == "request_ai_processing":
                await self._handle_request_ai_processing(session_id, message)
            elif message_type == "ping":
                await self._handle_ping(session_id, message)
            else:
                await self.send_message(session_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
        except Exception as e:
            logger.error(f"Error handling DICOM WebSocket message from {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            })
    
    async def _handle_subscribe_study(self, session_id: str, message: Dict[str, Any]):
        """Handle study subscription."""
        
        study_uid = message.get("study_uid")
        if not study_uid:
            return
        
        self._subscribe_to_study(session_id, study_uid)
        
        await self.send_message(session_id, {
            "type": "study_subscribed",
            "study_uid": study_uid
        })
    
    async def _handle_unsubscribe_study(self, session_id: str, message: Dict[str, Any]):
        """Handle study unsubscription."""
        
        study_uid = message.get("study_uid")
        if not study_uid:
            return
        
        self._unsubscribe_from_study(session_id, study_uid)
        
        await self.send_message(session_id, {
            "type": "study_unsubscribed",
            "study_uid": study_uid
        })
    
    async def _handle_subscribe_user_studies(self, session_id: str, message: Dict[str, Any]):
        """Handle subscription to all user studies."""
        
        user_id = message.get("user_id")
        if not user_id:
            return
        
        # In a real implementation, you would fetch user's studies from database
        # For now, we'll just acknowledge the subscription
        await self.send_message(session_id, {
            "type": "user_studies_subscribed",
            "user_id": user_id
        })
    
    async def _handle_request_preload(self, session_id: str, message: Dict[str, Any]):
        """Handle image preload request."""
        
        study_uid = message.get("study_uid")
        series_uid = message.get("series_uid")
        
        # Trigger background preloading
        asyncio.create_task(self._simulate_image_preload(study_uid, series_uid))
        
        await self.send_message(session_id, {
            "type": "preload_started",
            "study_uid": study_uid,
            "series_uid": series_uid
        })
    
    async def _handle_user_activity(self, session_id: str, message: Dict[str, Any]):
        """Handle user activity reporting."""
        
        activity = message.get("activity")
        study_uid = message.get("study_uid")
        
        # Broadcast activity to other users if relevant
        if study_uid and activity in ["study_opened", "report_started", "report_finalized"]:
            await self.broadcast_to_study_subscribers(study_uid, {
                "type": "user_activity",
                "user_id": self.user_sessions[session_id].get("user_id"),
                "activity": activity,
                "study_uid": study_uid,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_request_ai_processing(self, session_id: str, message: Dict[str, Any]):
        """Handle AI processing request."""
        
        study_uid = message.get("study_uid")
        processing_type = message.get("processing_type")
        
        # Simulate AI processing
        job_id = str(uuid.uuid4())
        asyncio.create_task(self._simulate_ai_processing(study_uid, processing_type, job_id))
        
        await self.send_message(session_id, {
            "type": "ai_processing_started",
            "job_id": job_id,
            "study_uid": study_uid,
            "processing_type": processing_type
        })
    
    async def _handle_ping(self, session_id: str, message: Dict[str, Any]):
        """Handle ping messages for connection keepalive."""
        
        await self.send_message(session_id, {
            "type": "pong",
            "timestamp": message.get("timestamp", datetime.utcnow().timestamp() * 1000)
        })
    
    def _subscribe_to_study(self, session_id: str, study_uid: str):
        """Subscribe session to study updates."""
        
        if study_uid not in self.study_subscribers:
            self.study_subscribers[study_uid] = set()
        
        self.study_subscribers[study_uid].add(session_id)
        
        if session_id in self.user_sessions:
            self.user_sessions[session_id]["subscribed_studies"].add(study_uid)
    
    def _unsubscribe_from_study(self, session_id: str, study_uid: str):
        """Unsubscribe session from study updates."""
        
        if study_uid in self.study_subscribers:
            self.study_subscribers[study_uid].discard(session_id)
            
            if not self.study_subscribers[study_uid]:
                del self.study_subscribers[study_uid]
        
        if session_id in self.user_sessions:
            self.user_sessions[session_id]["subscribed_studies"].discard(study_uid)
    
    async def _simulate_image_preload(self, study_uid: str, series_uid: str = None):
        """Simulate image preloading with progress updates."""
        
        total_images = 50  # Simulate 50 images
        
        for i in range(total_images + 1):
            progress = (i / total_images) * 100
            
            await self.broadcast_to_study_subscribers(study_uid, {
                "type": "image_loading",
                "study_uid": study_uid,
                "series_uid": series_uid,
                "progress": progress,
                "loaded_images": i,
                "total_images": total_images,
                "cache_status": "loading" if i < total_images else "cached"
            })
            
            await asyncio.sleep(0.1)  # Simulate loading time
    
    async def _simulate_ai_processing(self, study_uid: str, processing_type: str, job_id: str):
        """Simulate AI processing with progress updates."""
        
        stages = ["Preprocessing", "Feature extraction", "Analysis", "Post-processing"]
        
        for i, stage in enumerate(stages):
            progress = ((i + 1) / len(stages)) * 100
            
            await self.broadcast_to_study_subscribers(study_uid, {
                "type": "ai_processing",
                "job_id": job_id,
                "study_uid": study_uid,
                "status": "processing",
                "progress": progress,
                "stage": stage
            })
            
            await asyncio.sleep(2)  # Simulate processing time
        
        # Send completion
        await self.broadcast_to_study_subscribers(study_uid, {
            "type": "ai_processing",
            "job_id": job_id,
            "study_uid": study_uid,
            "status": "completed",
            "progress": 100,
            "stage": "Complete",
            "confidence_score": 0.92,
            "processing_time": 8.5
        })
    
    # Public methods for external services to trigger notifications
    async def notify_study_processing(self, study_uid: str, status: str, progress: int, stage: str, error_message: str = None):
        """Notify about study processing updates."""
        
        message = {
            "type": "study_processing",
            "study_uid": study_uid,
            "status": status,
            "progress": progress,
            "stage": stage
        }
        
        if error_message:
            message["error_message"] = error_message
        
        await self.broadcast_to_study_subscribers(study_uid, message)
    
    async def notify_workflow_update(self, workflow_id: str, study_uid: str, status: str, elapsed_time: int, target_time: int, on_track: bool):
        """Notify about workflow updates."""
        
        await self.broadcast_to_study_subscribers(study_uid, {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "study_uid": study_uid,
            "status": status,
            "elapsed_time": elapsed_time,
            "target_time": target_time,
            "on_track": on_track
        })
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        
        active_count = len(self.active_connections)
        user_count = len(set(
            session.get("user_id") for session in self.user_sessions.values()
            if session.get("user_id")
        ))
        
        return {
            "active_connections": active_count,
            "unique_users": user_count,
            "total_sessions": len(self.user_sessions),
            "subscribed_studies": len(self.study_subscribers),
            "stats_generated_at": datetime.utcnow().isoformat()
        }

# Global DICOM WebSocket service instance
dicom_websocket_service = DicomWebSocketService()