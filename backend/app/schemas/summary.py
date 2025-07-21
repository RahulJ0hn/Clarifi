from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class SummarizeRequest(BaseModel):
    url: str
    question: Optional[str] = None
    include_content: bool = True
    ai_provider: Optional[str] = None
    
class SummarizeResponse(BaseModel):
    id: str
    url: str
    title: Optional[str]
    summary_text: str
    question: Optional[str]
    response: Optional[str]
    ai_provider: str
    processing_time: Optional[float]
    created_at: datetime
    
class SummaryHistory(BaseModel):
    id: str
    url: str
    title: Optional[str]
    summary_text: str
    question: Optional[str]
    response: Optional[str]
    created_at: datetime
    
class SummaryListResponse(BaseModel):
    summaries: list[SummaryHistory]
    total: int
    page: int
    per_page: int 