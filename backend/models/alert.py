"""
Liopleurodon — Job Alert Models
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobAlertBase(BaseModel):
    name: str
    filters: dict  # stored as JSONB — mirrors JobSearchParams
    is_active: bool = True
    frequency: str = "daily"  # realtime, daily, weekly


class JobAlertCreate(JobAlertBase):
    user_id: str


class JobAlertResponse(JobAlertBase):
    id: str
    user_id: str
    last_triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
