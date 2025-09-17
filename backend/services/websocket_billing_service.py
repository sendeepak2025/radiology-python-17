"""
WebSocket service for real-time billing code suggestions.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import uuid

from services.realtime_billing_service import RealtimeBillingService

logger = logging.getLogger(__name__)

class WebSocketBillingService:
    """WebSocket service for real-time billing interactions."""
    
    def __init__(self):
        self.realtime_billing_service = RealtimeBillingService()
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.suggestion_debounce_delay = 0.5  # 500ms debounce
        
    async def connect(self, websocket: WebSocket, user_id: str = None) -> str:
        """Accept WebSocket connection and return session ID."""
        
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "current_exam_type": None,
            "current_findings": "",
            "debounce_task": None
        }
        
        logger.info(f"WebSocket connected: session {session_id}, user {user_id}")
        
        # Send welcome message
        await self.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return session_id
    
    def disconnect(self, session_id: str):
        """Handle WebSocket disconnection."""
        
        if session_id in self.active_connections:
            # Cancel any pending debounce tasks
            session = self.user_sessions.get(session_id, {})
            debounce_task = session.get("debounce_task")
            if debounce_task and not debounce_task.done():
                debounce_task.cancel()
            
            del self.active_connections[session_id]
            del self.user_sessions[session_id]
            
            logger.info(f"WebSocket disconnected: session {session_id}")
    
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
                logger.error(f"Error sending WebSocket message to {session_id}: {e}")
                # Remove broken connection
                self.disconnect(session_id)
    
    async def broadcast_message(self, message: Dict[str, Any], user_filter: Set[str] = None):
        """Broadcast message to all or filtered connections."""
        
        for session_id, session_data in self.user_sessions.items():
            if user_filter is None or session_data.get("user_id") in user_filter:
                await self.send_message(session_id, message)
    
    async def handle_message(self, session_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        
        try:
            message_type = message.get("type")
            
            if message_type == "findings_update":
                await self._handle_findings_update(session_id, message)
            elif message_type == "validate_codes":
                await self._handle_code_validation(session_id, message)
            elif message_type == "get_suggestions":
                await self._handle_get_suggestions(session_id, message)
            elif message_type == "set_exam_type":
                await self._handle_set_exam_type(session_id, message)
            elif message_type == "ping":
                await self._handle_ping(session_id, message)
            else:
                await self.send_message(session_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            })
    
    async def _handle_findings_update(self, session_id: str, message: Dict[str, Any]):
        """Handle real-time findings text updates with debouncing."""
        
        findings_text = message.get("findings", "")
        exam_type = message.get("exam_type")
        
        # Update session data
        session = self.user_sessions.get(session_id, {})
        session["current_findings"] = findings_text
        if exam_type:
            session["current_exam_type"] = exam_type
        
        # Cancel previous debounce task
        debounce_task = session.get("debounce_task")
        if debounce_task and not debounce_task.done():
            debounce_task.cancel()
        
        # Create new debounced suggestion task
        async def debounced_suggestions():
            await asyncio.sleep(self.suggestion_debounce_delay)
            await self._generate_and_send_suggestions(session_id, findings_text, exam_type)
        
        session["debounce_task"] = asyncio.create_task(debounced_suggestions())
    
    async def _generate_and_send_suggestions(
        self, 
        session_id: str, 
        findings_text: str, 
        exam_type: str
    ):
        """Generate and send code suggestions."""
        
        try:
            if not findings_text.strip() or not exam_type:
                return
            
            # Get session context
            session = self.user_sessions.get(session_id, {})
            user_context = {"user_id": session.get("user_id")}
            
            # Generate suggestions
            suggestions = await self.realtime_billing_service.suggest_codes_realtime(
                findings_text=findings_text,
                exam_type=exam_type,
                user_context=user_context
            )
            
            # Send suggestions
            await self.send_message(session_id, {
                "type": "code_suggestions",
                "suggestions": suggestions["suggestions"][:10],  # Top 10 suggestions
                "exam_type": exam_type,
                "findings_length": len(findings_text),
                "generated_at": suggestions["generated_at"]
            })
            
        except Exception as e:
            logger.error(f"Error generating suggestions for {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Error generating suggestions: {str(e)}"
            })
    
    async def _handle_code_validation(self, session_id: str, message: Dict[str, Any]):
        """Handle real-time code validation requests."""
        
        try:
            cpt_codes = message.get("cpt_codes", [])
            icd10_codes = message.get("icd10_codes", [])
            exam_type = message.get("exam_type", "unknown")
            patient_context = message.get("patient_context")
            
            # Perform validation
            validation = await self.realtime_billing_service.validate_codes_realtime(
                cpt_codes=cpt_codes,
                icd10_codes=icd10_codes,
                exam_type=exam_type,
                patient_context=patient_context
            )
            
            # Send validation result
            await self.send_message(session_id, {
                "type": "validation_result",
                "validation": validation,
                "request_id": message.get("request_id")
            })
            
        except Exception as e:
            logger.error(f"Error validating codes for {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Error validating codes: {str(e)}",
                "request_id": message.get("request_id")
            })
    
    async def _handle_get_suggestions(self, session_id: str, message: Dict[str, Any]):
        """Handle explicit suggestion requests."""
        
        try:
            findings_text = message.get("findings", "")
            exam_type = message.get("exam_type")
            measurements = message.get("measurements")
            
            session = self.user_sessions.get(session_id, {})
            user_context = {"user_id": session.get("user_id")}
            
            suggestions = await self.realtime_billing_service.suggest_codes_realtime(
                findings_text=findings_text,
                exam_type=exam_type,
                measurements=measurements,
                user_context=user_context
            )
            
            await self.send_message(session_id, {
                "type": "suggestions_response",
                "suggestions": suggestions,
                "request_id": message.get("request_id")
            })
            
        except Exception as e:
            logger.error(f"Error getting suggestions for {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "message": f"Error getting suggestions: {str(e)}",
                "request_id": message.get("request_id")
            })
    
    async def _handle_set_exam_type(self, session_id: str, message: Dict[str, Any]):
        """Handle exam type updates."""
        
        exam_type = message.get("exam_type")
        
        if session_id in self.user_sessions:
            self.user_sessions[session_id]["current_exam_type"] = exam_type
            
            await self.send_message(session_id, {
                "type": "exam_type_updated",
                "exam_type": exam_type
            })
            
            # If there are current findings, regenerate suggestions
            current_findings = self.user_sessions[session_id].get("current_findings", "")
            if current_findings.strip():
                await self._generate_and_send_suggestions(session_id, current_findings, exam_type)
    
    async def _handle_ping(self, session_id: str, message: Dict[str, Any]):
        """Handle ping messages for connection keepalive."""
        
        await self.send_message(session_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": message.get("request_id")
        })
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """Clean up inactive WebSocket connections."""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        inactive_sessions = []
        
        for session_id, session_data in self.user_sessions.items():
            last_activity = session_data.get("last_activity")
            if last_activity and last_activity < cutoff_time:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive WebSocket session: {session_id}")
            self.disconnect(session_id)
        
        return len(inactive_sessions)
    
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
            "average_session_duration": self._calculate_average_session_duration(),
            "stats_generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_average_session_duration(self) -> float:
        """Calculate average session duration in minutes."""
        
        if not self.user_sessions:
            return 0.0
        
        total_duration = 0.0
        current_time = datetime.utcnow()
        
        for session_data in self.user_sessions.values():
            connected_at = session_data.get("connected_at")
            if connected_at:
                duration = (current_time - connected_at).total_seconds() / 60
                total_duration += duration
        
        return total_duration / len(self.user_sessions)

# Global WebSocket service instance
websocket_billing_service = WebSocketBillingService()