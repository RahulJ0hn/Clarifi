from fastapi import WebSocket, HTTPException, status
from typing import List, Dict, Any, Optional
import json
import logging
from app.core.clerk_auth import verify_clerk_token, get_user_from_token

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Map user_id to list of their active WebSocket connections
        self.user_connections: Dict[str, List[WebSocket]] = {}
        # Map WebSocket to user_id for quick lookup
        self.connection_users: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None):
        """Accept a new WebSocket connection with authentication"""
        try:
            await websocket.accept()
            
            # Verify token if provided
            if token:
                logger.info(f"🔐 Verifying WebSocket token: {token[:20]}...")
                
                if not verify_clerk_token(token):
                    logger.warning("❌ WebSocket token verification failed")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return False
                
                user_data = get_user_from_token(token)
                if not user_data:
                    logger.warning("❌ Failed to extract user data from WebSocket token")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return False
                
                user_id = user_data["user_id"]
                logger.info(f"✅ WebSocket authenticated for user: {user_id}")
                
                # Add to user's connections
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = []
                self.user_connections[user_id].append(websocket)
                self.connection_users[websocket] = user_id
                
                # Send welcome message
                await self.send_personal_json({
                    "type": "connection_established",
                    "user_id": user_id,
                    "message": "WebSocket connection authenticated successfully"
                }, websocket)
                
                logger.info(f"✅ WebSocket connected for user {user_id}. Total connections: {len(self.user_connections)}")
                return True
            else:
                logger.warning("⚠️ WebSocket connection without token (unauthenticated)")
                # Allow unauthenticated connections for backward compatibility
                # In production, you might want to reject these
                return True
                
        except Exception as e:
            logger.error(f"❌ Error accepting WebSocket connection: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return False
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        try:
            user_id = self.connection_users.get(websocket)
            
            if user_id and user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)
                    logger.info(f"🔌 WebSocket disconnected for user {user_id}")
                
                # Remove empty user connections
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    logger.info(f"🧹 Cleaned up empty connections for user {user_id}")
            
            # Remove from connection mapping
            if websocket in self.connection_users:
                del self.connection_users[websocket]
            
            logger.info(f"📊 Total users with connections: {len(self.user_connections)}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def send_personal_json(self, data: Dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific WebSocket connection"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending personal JSON: {str(e)}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any]):
        """Send data to all connections of a specific user"""
        if user_id not in self.user_connections:
            logger.warning(f"⚠️ No active connections for user {user_id}")
            return
        
        disconnected = []
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_message(self, message: str):
        """Broadcast a message to all connected clients (deprecated - use user-specific)"""
        logger.warning("⚠️ Using deprecated broadcast_message - use user-specific methods")
        
        disconnected = []
        for user_id, connections in self.user_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {str(e)}")
                    disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast JSON data to all connected clients (deprecated - use user-specific)"""
        logger.warning("⚠️ Using deprecated broadcast_json - use user-specific methods")
        
        disconnected = []
        for user_id, connections in self.user_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Error broadcasting JSON: {str(e)}")
                    disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_notification(self, notification_data: Dict[str, Any]):
        """Send a notification to the specific user who owns it"""
        user_id = notification_data.get("user_id")
        if not user_id:
            logger.warning("⚠️ Notification without user_id, cannot send to specific user")
            return
        
        message = {
            "type": "notification",
            "data": notification_data
        }
        await self.send_to_user(user_id, message)
        logger.info(f"📨 Sent notification to user {user_id}")
    
    async def send_monitor_update(self, monitor_data: Dict[str, Any]):
        """Send a monitor update to the specific user who owns it"""
        user_id = monitor_data.get("user_id")
        if not user_id:
            logger.warning("⚠️ Monitor update without user_id, cannot send to specific user")
            return
        
        message = {
            "type": "monitor_update",
            "data": monitor_data
        }
        await self.send_to_user(user_id, message)
        logger.info(f"👁️ Sent monitor update to user {user_id}")
    
    async def send_system_status(self, status_data: Dict[str, Any], user_id: Optional[str] = None):
        """Send system status update to specific user or all users"""
        message = {
            "type": "system_status",
            "data": status_data
        }
        
        if user_id:
            await self.send_to_user(user_id, message)
            logger.info(f"📊 Sent system status to user {user_id}")
        else:
            # Send to all users (for global system updates)
            for uid in self.user_connections.keys():
                await self.send_to_user(uid, message)
            logger.info(f"📊 Sent system status to all users")
    
    def get_connection_count(self) -> int:
        """Get the total number of active connections"""
        total = 0
        for connections in self.user_connections.values():
            total += len(connections)
        return total
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get the number of active connections for a specific user"""
        return len(self.user_connections.get(user_id, []))
    
    def is_connected(self) -> bool:
        """Check if there are any active connections"""
        return len(self.user_connections) > 0
    
    def get_connected_users(self) -> List[str]:
        """Get list of user IDs with active connections"""
        return list(self.user_connections.keys())

# Create global instance
websocket_manager = WebSocketManager() 