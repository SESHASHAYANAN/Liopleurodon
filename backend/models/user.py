"""
Liopleurodon — User Models
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    resume_url: Optional[str] = None
    preferences: dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SavedJob(BaseModel):
    id: Optional[str] = None
    user_id: str
    job_id: str
    created_at: Optional[datetime] = None


class UserApplication(BaseModel):
    id: Optional[str] = None
    user_id: str
    job_id: str
    status: str = "applied"
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
