"""Pydantic schemas for Makeable Jobs API."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ------------------------------------------------------------
# Auth
# ------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=4096)


# ------------------------------------------------------------
# Users
# ------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    avatar: str | None = None
    headline: str | None = None
    bio: str | None = None
    skills: list[Any] = []
    experience: int = 0
    location: str | None = None
    resume_url: str | None = None
    preferences: dict[str, Any] = {}
    role: str = "user"
    created_at: datetime


class UserUpdate(BaseModel):
    name: str | None = None
    avatar: str | None = None
    headline: str | None = None
    bio: str | None = None
    skills: list[str] | None = None
    experience: int | None = None
    location: str | None = None
    preferences: dict[str, Any] | None = None


class PreferencesUpdate(BaseModel):
    remote_only: bool = False
    job_types: list[str] = []
    locations: list[str] = []
    keywords: list[str] = []


# ------------------------------------------------------------
# Companies
# ------------------------------------------------------------
class CompanyBase(BaseModel):
    name: str
    slug: str
    logo: str | None = None
    website: str | None = None
    industry: str | None = None
    description: str | None = None
    location: str | None = None
    size: str | None = None
    rating: float = 0
    verified: bool = False


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    review_count: int = 0
    created_at: datetime
    open_positions: int = 0


class CompaniesOut(BaseModel):
    companies: list[CompanyOut]


class CompanyUpdate(BaseModel):
    name: str | None = None
    logo: str | None = None
    website: str | None = None
    industry: str | None = None
    description: str | None = None
    location: str | None = None
    size: str | None = None
    rating: float | None = None
    verified: bool | None = None


# ------------------------------------------------------------
# Jobs
# ------------------------------------------------------------
JobSource = Literal["linkedin", "indeed", "naukri", "internshala", "wellfound", "company", "manual", "serpapi", "usajobs", "jsearch", "greenhouse", "ashby", "remoteok"]
JobType = Literal["full_time", "part_time", "contract", "internship", "freelance"]
Level = Literal["entry", "mid", "senior", "lead", "executive"]


class JobCreate(BaseModel):
    external_id: str | None = None
    source: JobSource
    title: str
    description: str | None = None
    company_name: str
    company_logo: str | None = None
    location: str | None = None
    remote: bool = False
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "INR"
    salary_text: str | None = None
    job_type: JobType = "full_time"
    level: Level = "entry"
    skills: list[str] = []
    apply_url: str
    apply_on: str = "Original Website"
    experience_min: int = 0
    experience_max: int = 0
    posted_at: datetime | None = None
    expires_at: datetime | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    title: str
    description: str | None = None
    company_id: str | None = None
    company_name: str
    company_logo: str | None = None
    location: str | None = None
    remote: bool
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str
    salary_text: str | None = None
    job_type: str
    level: str
    skills: list[Any] = []
    apply_url: str
    apply_on: str
    experience_min: int
    experience_max: int
    posted_at: datetime | None = None
    sponsored: bool = False
    views: int = 0


class JobList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[JobOut]


class SavedJobsOut(BaseModel):
    jobs: list[JobOut]


class JobSearchParams(BaseModel):
    q: str | None = None
    location: str | None = None
    remote: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: JobType | None = None
    level: Level | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    source: str | None = None
    company: str | None = None
    sort: Literal["recent", "salary_desc", "salary_asc", "relevance"] = "recent"
    page: int = 1
    page_size: int = 20


# ------------------------------------------------------------
# Saved jobs / Applications
# ------------------------------------------------------------
class SavedJobCreate(BaseModel):
    job_id: str


class ApplicationStatusUpdate(BaseModel):
    status: Literal["applied", "interviewing", "offered", "rejected", "withdrawn"]
    notes: str | None = None


class ApplicationCreate(BaseModel):
    job_id: str | None = None
    company_name: str | None = None
    role: str | None = None
    applied_url: str | None = None
    status: Literal["applied", "interviewing", "offered", "rejected", "withdrawn"] = "applied"


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str | None = None
    company_name: str | None = None
    role: str | None = None
    status: str
    applied_url: str | None = None
    notes: str | None = None
    applied_at: datetime


class ApplicationsOut(BaseModel):
    applications: list[ApplicationOut]


# ------------------------------------------------------------
# Searches / Notifications / Alerts
# ------------------------------------------------------------
class SearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    filters: dict[str, Any] = {}
    result_count: int = 0
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str | None = None
    data: dict[str, Any] = {}
    read: bool = False
    created_at: datetime


class NotificationsOut(BaseModel):
    notifications: list[NotificationOut]


class AlertCreate(BaseModel):
    query: str
    filters: dict[str, Any] = {}
    frequency: Literal["instant", "daily", "weekly"] = "daily"


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    filters: dict[str, Any] = {}
    frequency: str = "daily"
    active: bool = True
    created_at: datetime


class AlertsOut(BaseModel):
    alerts: list[AlertOut]


class DeviceTokenCreate(BaseModel):
    token: str
    platform: Literal["android", "ios", "web"] = "android"


# ------------------------------------------------------------
# Resume / AI
# ------------------------------------------------------------
class AIOptions(BaseModel):
    """Optional user-supplied LLM credentials for AI-powered features.

    When provided, requests are forwarded to the user's own OpenAI or Gemini
    account; when omitted, a deterministic heuristic engine is used.
    """

    api_key: str | None = Field(default=None, max_length=300)
    provider: Literal["openai", "gemini"] = "openai"


class ResumeAnalyzeRequest(AIOptions):
    resume_text: str = Field(min_length=50, max_length=100_000)
    target_role: str | None = None
    job_description: str | None = None


class ResumeAnalysisOut(BaseModel):
    ats_score: int
    missing_keywords: list[str] = []
    suggestions: list[str] = []
    summary: str = ""


class CoverLetterRequest(AIOptions):
    resume_text: str
    job_title: str
    company_name: str
    job_description: str | None = None


class CoverLetterOut(BaseModel):
    cover_letter: str


class SkillGapRequest(AIOptions):
    resume_text: str
    target_role: str


class SkillGapOut(BaseModel):
    current_skills: list[str] = []
    missing_skills: list[str] = []
    recommended_learning: list[str] = []


class InterviewPrepRequest(AIOptions):
    job_title: str
    job_description: str | None = None
    resume_text: str | None = None


class InterviewPrepOut(BaseModel):
    questions: list[str] = []


# ------------------------------------------------------------
# Developer API Dashboard / SerpApi usage
# ------------------------------------------------------------
class RecentSearchOut(BaseModel):
    endpoint: str
    query: str | None = None
    location: str | None = None
    page: int = 1
    response_time_ms: int = 0
    cached: bool = False
    status_code: int = 200
    timestamp: str


class CacheStatsOut(BaseModel):
    backend: str
    hits: int
    misses: int
    entries: int
    hit_rate: float


class ProviderHealthOut(BaseModel):
    name: str
    configured: bool


class UsageOut(BaseModel):
    searches_used: int
    monthly_limit: int
    remaining: int
    cache_hit_rate: float
    total_requests: int
    cache: CacheStatsOut
    provider: ProviderHealthOut
    recent_searches: list[RecentSearchOut] = []


# ------------------------------------------------------------
# Admin / Analytics
# ------------------------------------------------------------
class AnalyticsOut(BaseModel):
    active_users: int
    total_jobs: int
    total_searches: int
    total_saved_jobs: int
    total_applications: int
    popular_companies: list[dict[str, Any]] = []
    jobs_by_source: list[dict[str, Any]] = []