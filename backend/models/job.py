"""
Liopleurodon — Job Models
Unified schema for all job data across 10+ sources.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CompanyType(str, Enum):
    STARTUP = "startup"
    BIG_TECH = "big_tech"
    STEALTH = "stealth"
    VC_BACKED = "vc_backed"
    REMOTE_FIRST = "remote_first"
    OTHER = "other"


class RemoteType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    STAFF = "staff"
    PRINCIPAL = "principal"


class JobType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class JobBase(BaseModel):
    """Base job model — the unified schema for all sources."""
    title: str
    company_name: str
    company_logo_url: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    company_type: Optional[str] = None
    vc_backer: Optional[str] = None
    funding_stage: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    location_coords: Optional[dict] = None  # {"lat": float, "lng": float}
    remote_type: Optional[str] = None
    visa_sponsorship: bool = False
    relocation_support: bool = False
    work_authorization: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_period: str = "yearly"
    experience_level: Optional[str] = None
    years_experience_min: Optional[int] = None
    years_experience_max: Optional[int] = None
    job_type: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[list[str]] = None
    requirements: Optional[list[str]] = None
    benefits: Optional[list[str]] = None
    skills_required: Optional[list[str]] = None
    skills_preferred: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None
    apply_url: Optional[str] = None
    easy_apply: bool = False
    source_platforms: list[str] = Field(default_factory=list)
    posted_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_stealth: bool = False
    is_active: bool = True


class JobCreate(JobBase):
    """Job creation model — includes dedup hash."""
    dedup_hash: str


class JobResponse(JobBase):
    """Job response model — returned by the API."""
    id: str
    dedup_hash: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobSearchParams(BaseModel):
    """Search/filter parameters for job queries."""
    q: Optional[str] = None  # keyword search
    location: Optional[str] = None
    remote_type: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    visa_sponsorship: Optional[bool] = None
    relocation_support: Optional[bool] = None
    company_type: Optional[str] = None
    vc_backer: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    source: Optional[str] = None
    posted_within: Optional[str] = None  # "24h", "week", "month"
    page: int = 1
    per_page: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"


class JobStats(BaseModel):
    """Job statistics for sidebar."""
    total_jobs: int = 0
    remote_jobs: int = 0
    vc_backed_jobs: int = 0
    stealth_jobs: int = 0
    big_tech_jobs: int = 0
    jobs_by_source: dict[str, int] = Field(default_factory=dict)
    jobs_by_experience: dict[str, int] = Field(default_factory=dict)
