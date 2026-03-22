"""
Audio Cache Manager - Grade S++
Temporary storage for downloaded audio files (debug mode only)
"""

import os
import shutil
import tempfile
from typing import Dict, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class AudioCacheManager:
    """Manages temporary audio files for debugging"""
    
    def __init__(self):
        """Initialize audio cache manager"""
        self._cache: Dict[str, dict] = {}  # job_id -> {path, expires_at, metadata}
        self._cache_dir = os.path.join(tempfile.gettempdir(), "saas_ia_audio_cache")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self._cache_dir, exist_ok=True)
        
        logger.info("audio_cache_initialized", cache_dir=self._cache_dir)
    
    def store_audio(
        self,
        job_id: str,
        audio_file_path: str,
        metadata: dict,
        ttl_minutes: int = 30
    ) -> str:
        """
        Store audio file in cache
        
        Args:
            job_id: Unique job identifier
            audio_file_path: Path to the audio file
            metadata: Audio metadata (title, duration, etc.)
            ttl_minutes: Time to live in minutes (default: 30)
        
        Returns:
            str: Cached file path
        """
        try:
            # Create job-specific directory
            job_cache_dir = os.path.join(self._cache_dir, job_id)
            os.makedirs(job_cache_dir, exist_ok=True)
            
            # Copy audio file to cache
            filename = os.path.basename(audio_file_path)
            cached_path = os.path.join(job_cache_dir, filename)
            shutil.copy2(audio_file_path, cached_path)
            
            # Store cache entry
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            self._cache[job_id] = {
                "path": cached_path,
                "filename": filename,
                "expires_at": expires_at,
                "metadata": metadata,
                "size_bytes": os.path.getsize(cached_path)
            }
            
            logger.info(
                "audio_cached",
                job_id=job_id,
                cached_path=cached_path,
                expires_at=expires_at.isoformat(),
                size_mb=round(os.path.getsize(cached_path) / 1024 / 1024, 2)
            )
            
            return cached_path
            
        except Exception as e:
            logger.error("audio_cache_store_failed", job_id=job_id, error=str(e))
            raise
    
    def get_audio(self, job_id: str) -> Optional[dict]:
        """
        Get cached audio file info
        
        Args:
            job_id: Job identifier
        
        Returns:
            dict: Audio info (path, metadata) or None if not found/expired
        """
        if job_id not in self._cache:
            return None
        
        entry = self._cache[job_id]
        
        # Check if expired
        if datetime.utcnow() > entry["expires_at"]:
            logger.info("audio_cache_expired", job_id=job_id)
            self.delete_audio(job_id)
            return None
        
        # Check if file still exists
        if not os.path.exists(entry["path"]):
            logger.warning("audio_cache_file_missing", job_id=job_id, path=entry["path"])
            del self._cache[job_id]
            return None
        
        return entry
    
    def delete_audio(self, job_id: str) -> bool:
        """
        Delete cached audio file
        
        Args:
            job_id: Job identifier
        
        Returns:
            bool: True if deleted, False if not found
        """
        if job_id not in self._cache:
            return False
        
        entry = self._cache[job_id]
        
        try:
            # Delete job directory
            job_cache_dir = os.path.dirname(entry["path"])
            if os.path.exists(job_cache_dir):
                shutil.rmtree(job_cache_dir)
            
            # Remove from cache
            del self._cache[job_id]
            
            logger.info("audio_cache_deleted", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("audio_cache_delete_failed", job_id=job_id, error=str(e))
            return False
    
    def cleanup_expired(self):
        """Cleanup all expired cache entries"""
        now = datetime.utcnow()
        expired_jobs = [
            job_id for job_id, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        
        for job_id in expired_jobs:
            self.delete_audio(job_id)
        
        if expired_jobs:
            logger.info("audio_cache_cleanup", expired_count=len(expired_jobs))
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        total_size = sum(
            entry["size_bytes"]
            for entry in self._cache.values()
        )
        
        return {
            "total_files": len(self._cache),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": self._cache_dir
        }


# Singleton instance
_audio_cache_manager: Optional[AudioCacheManager] = None


def get_audio_cache() -> AudioCacheManager:
    """Get the audio cache manager singleton"""
    global _audio_cache_manager
    if _audio_cache_manager is None:
        _audio_cache_manager = AudioCacheManager()
    return _audio_cache_manager


__all__ = ["AudioCacheManager", "get_audio_cache"]

