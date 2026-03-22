"""
WebSocket endpoint for real-time transcription debug
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import structlog
import json

logger = structlog.get_logger()


class DebugConnectionManager:
    """Manage WebSocket connections for debug streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a WebSocket client"""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)
        logger.info("websocket_connected", job_id=job_id, total_connections=len(self.active_connections[job_id]))
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Disconnect a WebSocket client"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info("websocket_disconnected", job_id=job_id)
    
    async def send_debug_message(self, job_id: str, message: dict):
        """Send debug message to all connected clients for a job"""
        if job_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("websocket_send_error", job_id=job_id, error=str(e))
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[job_id].discard(conn)


# Global manager instance
debug_manager = DebugConnectionManager()


def get_debug_manager() -> DebugConnectionManager:
    """Get the global debug manager"""
    return debug_manager

