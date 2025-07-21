from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Optional
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import engine, Base
from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.routers import summarize, monitor, notifications, auth
from app.services.scheduler import scheduler
from app.services.websocket_manager import websocket_manager
from app.core.rate_limiter import rate_limit_middleware
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import Optional

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="Clarifi",
    description="An AI-powered browser-like web app with summarization and monitoring capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware_wrapper(request, call_next):
    return await rate_limit_middleware(request, call_next)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(summarize.router, prefix="/api", tags=["summarize"])
app.include_router(monitor.router, prefix="/api", tags=["monitor"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])

@app.get("/")
async def root():
    return {"message": "Clarifi API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "scheduler_running": scheduler.running}

@app.get("/api/stats")
async def get_main_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get main application statistics
    """
    try:
        # If no user, return empty stats
        if not current_user:
            return {
                "total_summaries": 0,
                "recent_summaries": 0,
                "top_domains": [],
                "total_monitors": 0,
                "active_monitors": 0,
                "total_notifications": 0,
                "unread_notifications": 0,
                "available_ai_providers": ["aws_bedrock"]
            }
        
        # Import models
        from app.models.summary import Summary
        from app.models.monitor import Monitor
        from app.models.notification import Notification
        from datetime import datetime, timedelta
        
        # Get summary stats
        total_summaries = db.query(Summary).filter(Summary.user_id == current_user.id).count()
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_summaries = db.query(Summary).filter(
            Summary.user_id == current_user.id,
            Summary.created_at >= seven_days_ago
        ).count()
        
        # Get monitor stats
        total_monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).count()
        active_monitors = db.query(Monitor).filter(
            Monitor.user_id == current_user.id,
            Monitor.is_active == True
        ).count()
        
        # Get notification stats
        total_notifications = db.query(Notification).filter(Notification.user_id == current_user.id).count()
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        # Get top domains for current user
        summaries = db.query(Summary).filter(Summary.user_id == current_user.id).all()
        domains = {}
        for summary in summaries:
            try:
                from urllib.parse import urlparse
                domain = urlparse(summary.url).netloc
                domains[domain] = domains.get(domain, 0) + 1
            except:
                continue
        
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_summaries": total_summaries,
            "recent_summaries": recent_summaries,
            "top_domains": [{"domain": domain, "count": count} for domain, count in top_domains],
            "total_monitors": total_monitors,
            "active_monitors": active_monitors,
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "available_ai_providers": ["aws_bedrock"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting main stats: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication")
):
    """
    WebSocket endpoint with JWT token authentication
    Connect with: ws://localhost:8000/ws?token=<jwt_token>
    """
    try:
        # Connect with authentication
        success = await websocket_manager.connect(websocket, token)
        
        if not success:
            return  # Connection was closed due to authentication failure
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Parse incoming message
                try:
                    message = json.loads(data)
                    message_type = message.get("type", "unknown")
                    
                    # Handle different message types
                    if message_type == "ping":
                        await websocket_manager.send_personal_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                    elif message_type == "echo":
                        await websocket_manager.send_personal_json({
                            "type": "echo_response",
                            "data": message.get("data", ""),
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                    else:
                        # Echo back for unknown message types
                        await websocket_manager.send_personal_json({
                            "type": "message_received",
                            "original_type": message_type,
                            "data": message,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                        
                except json.JSONDecodeError:
                    # Handle plain text messages
                    await websocket_manager.send_personal_message(f"Message received: {data}", websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_manager.send_personal_json({
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        pass  # Normal disconnection
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 