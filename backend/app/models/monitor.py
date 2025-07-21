from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Monitor(Base):
    __tablename__ = "monitors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for backward compatibility
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, index=True)
    monitor_type = Column(String, default="content")  # content, price, selector, item_search
    css_selector = Column(String, nullable=True)
    xpath_selector = Column(String, nullable=True)
    
    # New fields for Perplexity-style item search
    item_name = Column(String, nullable=True)  # e.g., "Bitcoin", "AAPL", "iPhone 15"
    item_type = Column(String, nullable=True)  # crypto, stock, product, news, auto
    
    current_value = Column(Text, nullable=True)
    previous_value = Column(Text, nullable=True)
    check_interval = Column(Integer, default=300)  # seconds
    is_active = Column(Boolean, default=True)
    notification_enabled = Column(Boolean, default=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    last_changed = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Store additional metadata as JSON
    monitor_metadata = Column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "url": self.url,
            "monitor_type": self.monitor_type,
            "css_selector": self.css_selector,
            "xpath_selector": self.xpath_selector,
            "item_name": self.item_name,
            "item_type": self.item_type,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "check_interval": self.check_interval,
            "is_active": self.is_active,
            "notification_enabled": self.notification_enabled,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_changed": self.last_changed.isoformat() if self.last_changed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.monitor_metadata
        } 