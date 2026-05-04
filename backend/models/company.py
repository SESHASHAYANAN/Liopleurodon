"""
Liopleurodon — Company Models
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    company_type: Optional[str] = None
    size: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    website_url: Optional[str] = None
    careers_url: Optional[str] = None
    vc_backers: Optional[list[str]] = None
    funding_stage: Optional[str] = None
    total_funding: Optional[str] = None
    glassdoor_rating: Optional[float] = None
    is_stealth: bool = False


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
