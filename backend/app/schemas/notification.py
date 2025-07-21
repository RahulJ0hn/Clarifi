from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    source: Optional[str]
    source_type: Optional[str]
    is_read: bool
    is_sent: bool
    priority: str
    created_at: datetime
    read_at: Optional[datetime]
    sent_at: Optional[datetime]
    data: Optional[Dict[str, Any]]

class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int

class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[str]

class NotificationCreateRequest(BaseModel):
    title: str
    message: str
    notification_type: str = "info"
    source: Optional[str] = None
    source_type: Optional[str] = None
    priority: str = "normal"
    data: Optional[Dict[str, Any]] = None

class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_notifications: int
    recent_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int] 