from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MonitorCreateRequest(BaseModel):
    name: str
    url: str
    monitor_type: str = "content"  # content, price, selector, item_search
    css_selector: Optional[str] = None
    xpath_selector: Optional[str] = None
    item_name: Optional[str] = None  # e.g., "Bitcoin", "AAPL", "iPhone 15"
    item_type: Optional[str] = None  # crypto, stock, product, news, auto
    check_interval: int = 300
    notification_enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None

class MonitorUpdateRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    check_interval: Optional[int] = None
    notification_enabled: Optional[bool] = None
    css_selector: Optional[str] = None
    xpath_selector: Optional[str] = None
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MonitorResponse(BaseModel):
    id: str
    name: str
    url: str
    monitor_type: str
    css_selector: Optional[str]
    xpath_selector: Optional[str]
    item_name: Optional[str]
    item_type: Optional[str]
    current_value: Optional[str]
    previous_value: Optional[str]
    check_interval: int
    is_active: bool
    notification_enabled: bool
    last_checked: Optional[datetime]
    last_changed: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

class MonitorListResponse(BaseModel):
    monitors: list[MonitorResponse]
    total: int
    page: int
    per_page: int

class MonitorStatusResponse(BaseModel):
    id: str
    name: str
    url: str
    current_value: Optional[str]
    previous_value: Optional[str]
    last_checked: Optional[datetime]
    last_changed: Optional[datetime]
    is_active: bool
    has_changed: bool 