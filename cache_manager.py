"""
Cache Manager for DICOM files and processed images
Provides in-memory and disk-based caching for better performance
"""

import os
import json
import hashlib
import pickle
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DicomCacheManager:
    def __init__(self, 
                 cache_dir: str = "cache",
                 max_memory_items: int = 100,
                 max_disk_size_mb: int = 500):
        """
        Initialize DICOM cache manager
        
        Args:
            cache_dir: Directory for disk cache
            max_memory_items: Maximum items in memory cache
            max_disk_size_mb: Maximum disk cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.max_memory_items = max_memory_items
        self.max_disk_size_mb = max_disk_size_mb
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        
        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_metadata()
    
    def _generate_cache_key(self, file_path: str, operation: str = "raw") -> str:
        """Generate unique cache key for file and operation"""
        file_stat = os.stat(file_path)
        key_data = f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}_{operation}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def load_metadata(self):
        """Load cache metadata from disk"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.disk_metadata = json.load(f)
            else:
                self.disk_metadata = {}
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
            self.disk_metadata = {}
    
    def save_metadata(self):
        """Save cache metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.disk_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _cleanup_memory_cache(self):
        """Remove oldest items from memory cache if it exceeds limit"""
        if len(self.memory_cache) <= self.max_memory_items:
            return
        
        # Sort by access time and remove oldest
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
        items_to_remove = len(self.memory_cache) - self.max_memory_items
        
        for key, _ in sorted_items[:items_to_remove]:
            self.memory_cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def get_from_memory(self, cache_key: str) -> Optional[Any]:
        """Get item from memory cache"""
        if cache_key in self.memory_cache:
            self.access_times[cache_key] = datetime.now()
            return self.memory_cache[cache_key]['data']
        return None
    
    def store_in_memory(self, cache_key: str, data: Any, metadata: Dict[str, Any] = None):
        """Store item in memory cache"""
        self.memory_cache[cache_key] = {
            'data': data,
            'metadata': metadata or {},
            'cached_at': datetime.now().isoformat()
        }
        self.access_times[cache_key] = datetime.now()
        self._cleanup_memory_cache()
    
    def get_from_disk(self, cache_key: str) -> Optional[Any]:
        """Get item from disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Update access time in metadata
                if cache_key in self.disk_metadata:
                    self.disk_metadata[cache_key]['last_accessed'] = datetime.now().isoformat()
                    self.save_metadata()
                
                return data
            except Exception as e:
                logger.error(f"Failed to load from disk cache: {e}")
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def store_on_disk(self, cache_key: str, data: Any, metadata: Dict[str, Any] = None):
        """Store item on disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Update metadata
            file_size = cache_file.stat().st_size
            self.disk_metadata[cache_key] = {
                'file_size': file_size,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self.save_metadata()
            
            # Cleanup if cache is too large
            self._cleanup_disk_cache()
            
        except Exception as e:
            logger.error(f"Failed to store on disk cache: {e}")
    
    def _cleanup_disk_cache(self):
        """Remove old items if disk cache exceeds size limit"""
        total_size = sum(item['file_size'] for item in self.disk_metadata.values())
        max_size_bytes = self.max_disk_size_mb * 1024 * 1024
        
        if total_size <= max_size_bytes:
            return
        
        # Sort by last accessed time and remove oldest
        sorted_items = sorted(
            self.disk_metadata.items(),
            key=lambda x: x[1]['last_accessed']
        )
        
        for cache_key, metadata in sorted_items:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            cache_file.unlink(missing_ok=True)
            
            total_size -= metadata['file_size']
            del self.disk_metadata[cache_key]
            
            if total_size <= max_size_bytes:
                break
        
        self.save_metadata()
    
    def get(self, file_path: str, operation: str = "raw") -> Optional[Any]:
        """Get cached data for file and operation"""
        cache_key = self._generate_cache_key(file_path, operation)
        
        # Try memory cache first
        data = self.get_from_memory(cache_key)
        if data is not None:
            return data
        
        # Try disk cache
        data = self.get_from_disk(cache_key)
        if data is not None:
            # Store in memory for faster future access
            self.store_in_memory(cache_key, data)
            return data
        
        return None
    
    def store(self, file_path: str, data: Any, operation: str = "raw", 
              metadata: Dict[str, Any] = None, disk_cache: bool = True):
        """Store data in cache"""
        cache_key = self._generate_cache_key(file_path, operation)
        
        # Always store in memory
        self.store_in_memory(cache_key, data, metadata)
        
        # Store on disk for larger items or if requested
        if disk_cache:
            self.store_on_disk(cache_key, data, metadata)
    
    def clear_cache(self, file_path: Optional[str] = None):
        """Clear cache for specific file or all cache"""
        if file_path:
            # Clear cache for specific file
            for operation in ["raw", "processed", "thumbnail"]:
                cache_key = self._generate_cache_key(file_path, operation)
                self.memory_cache.pop(cache_key, None)
                self.access_times.pop(cache_key, None)
                
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                cache_file.unlink(missing_ok=True)
                self.disk_metadata.pop(cache_key, None)
        else:
            # Clear all cache
            self.memory_cache.clear()
            self.access_times.clear()
            
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
            
            self.disk_metadata.clear()
        
        self.save_metadata()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_size = len(self.memory_cache)
        disk_size = len(self.disk_metadata)
        total_disk_size_mb = sum(item['file_size'] for item in self.disk_metadata.values()) / (1024 * 1024)
        
        return {
            'memory_cache_items': memory_size,
            'disk_cache_items': disk_size,
            'disk_cache_size_mb': round(total_disk_size_mb, 2),
            'max_memory_items': self.max_memory_items,
            'max_disk_size_mb': self.max_disk_size_mb
        }

# Global cache instance
dicom_cache = DicomCacheManager()