from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for backward compatibility
    url = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=False)
    question = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    ai_provider = Column(String, default="anthropic")
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "summary_text": self.summary_text,
            "question": self.question,
            "response": self.response,
            "ai_provider": self.ai_provider,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 