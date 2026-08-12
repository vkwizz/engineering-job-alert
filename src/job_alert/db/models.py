from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.job_alert.db.engine import Base

def utcnow():
    return datetime.now(timezone.utc)

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True, nullable=False)
    normalized_name = Column(String, index=True, nullable=False)
    tier = Column(Integer, nullable=True)
    company_score = Column(Integer, default=0)
    preferred = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
    industry = Column(String, nullable=True)
    career_url = Column(String, nullable=True)
    aliases_json = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    jobs = relationship("Job", back_populates="company")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    canonical_key = Column(String, unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    title = Column(String, nullable=False)
    normalized_title = Column(String, index=True, nullable=False)
    location = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    remote_type = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    role_family = Column(String, nullable=True)
    technical_domain = Column(String, nullable=True)
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    graduation_years_json = Column(JSON, default=list)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    raw_description = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    apply_url = Column(String, nullable=True)
    company_career_url = Column(String, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), default=utcnow)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow)
    status = Column(String, default="new", index=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="jobs")
    sources = relationship("JobSource", back_populates="job", cascade="all, delete-orphan")
    analysis = relationship("JobAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="job", cascade="all, delete-orphan")

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    source = Column(String, nullable=False)
    source_job_id = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_company_name = Column(String, nullable=True)
    source_raw_json = Column(JSON, nullable=True)
    source_first_seen_at = Column(DateTime(timezone=True), default=utcnow)
    source_last_seen_at = Column(DateTime(timezone=True), default=utcnow)
    source_confidence = Column(Integer, default=50)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    job = relationship("Job", back_populates="sources")

class JobAnalysis(Base):
    __tablename__ = "job_analysis"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    student_eligible = Column(Boolean, nullable=True)
    is_internship = Column(Boolean, nullable=True)
    is_graduate_role = Column(Boolean, nullable=True)
    is_target_technical_role = Column(Boolean, nullable=True)
    is_excluded_role = Column(Boolean, nullable=True)
    technical_domain = Column(String, nullable=True)
    role_family = Column(String, nullable=True)
    company_fit_score = Column(Float, default=0.0)
    technical_fit_score = Column(Float, default=0.0)
    student_fit_score = Column(Float, default=0.0)
    location_fit_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    source_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0, index=True)
    ai_reasoning_summary = Column(String, nullable=True)
    ai_model = Column(String, nullable=True)
    ai_classified_at = Column(DateTime(timezone=True), nullable=True)
    classifier_version = Column(String, nullable=True)

    job = relationship("Job", back_populates="analysis")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    channel = Column(String, nullable=False) # e.g., 'gmail', 'telegram'
    alert_type = Column(String, nullable=False) # e.g., 'immediate', 'digest'
    sent_at = Column(DateTime(timezone=True), default=utcnow)
    notification_key = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="sent")
    error_message = Column(String, nullable=True)

    job = relationship("Job", back_populates="alerts")

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="running")
    jobs_fetched = Column(Integer, default=0)
    jobs_normalized = Column(Integer, default=0)
    jobs_deduplicated = Column(Integer, default=0)
    jobs_rejected = Column(Integer, default=0)
    jobs_ai_classified = Column(Integer, default=0)
    jobs_alerted = Column(Integer, default=0)
    error_summary = Column(String, nullable=True)
    run_metadata_json = Column(JSON, default=dict)
