from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for backward compatibility
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="info")  # info, warning, error, success
    source = Column(String, nullable=True)  # monitor_id, summary_id, etc.
    source_type = Column(String, nullable=True)  # monitor, summary, system
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    priority = Column(String, default="normal")  # low, normal, high, urgent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Store additional data as JSON
    data = Column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "source": self.source,
            "source_type": self.source_type,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "data": self.data
        } 