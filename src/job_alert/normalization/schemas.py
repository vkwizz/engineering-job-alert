from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RawJobRecord(BaseModel):
    source: str
    source_job_id: Optional[str] = None
    title: str
    company_name: str
    location: Optional[str] = None
    raw_description: Optional[str] = None
    apply_url: Optional[str] = None
    source_url: Optional[str] = None
    confidence: int = 50

class NormalizedJob(BaseModel):
    canonical_key: str
    title: str
    company_name: str
    location: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    remote_type: Optional[str] = None
    employment_type: Optional[str] = None
    posted_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    raw_description: Optional[str] = None
    apply_url: Optional[str] = None
    company_career_url: Optional[str] = None
    source: str = "unknown"
    source_job_id: Optional[str] = "unknown"
    source_url: Optional[str] = None
    source_raw_json: Optional[Dict[str, Any]] = None
    confidence: int = 50
