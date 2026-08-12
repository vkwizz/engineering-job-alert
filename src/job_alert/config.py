import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class CandidateConfig(BaseModel):
    degree_types: List[str]
    graduation_year: int

class LocationsConfig(BaseModel):
    preferred: List[str]

class TechnicalDomainsConfig(BaseModel):
    include: List[str]
    exclude: List[str]

class ScoringConfig(BaseModel):
    company: int
    technical: int
    student: int
    location: int
    freshness: int
    source: int

class AlertsConfig(BaseModel):
    immediate_threshold: int
    digest_threshold: int
    telegram_enabled: bool
    gmail_enabled: bool

class UserPreferences(BaseModel):
    candidate: CandidateConfig
    locations: LocationsConfig
    technical_domains: TechnicalDomainsConfig
    scoring: ScoringConfig
    alerts: AlertsConfig

class CompanyEntry(BaseModel):
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    tier: Optional[int] = None
    company_score: int = 0
    preferred: bool = False
    industry: Optional[str] = None
    notes: Optional[str] = None
    direct_career_url: Optional[str] = None

class CompaniesConfig(BaseModel):
    companies: List[CompanyEntry]

def load_yaml(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_user_preferences() -> UserPreferences:
    data = load_yaml(PROJECT_ROOT / "config" / "user_preferences.yaml")
    return UserPreferences(**data)

def get_companies_config() -> CompaniesConfig:
    data = load_yaml(PROJECT_ROOT / "config" / "companies.yaml")
    return CompaniesConfig(**data)

class AppConfig:
    def __init__(self):
        self.prefs = get_user_preferences()
        self.companies = get_companies_config()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        db_url = os.getenv("DATABASE_URL", "sqlite:///jobs.db")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        self.database_url = db_url
        self.gmail_sender = os.getenv("GMAIL_SENDER_ADDRESS")
        self.gmail_recipient = os.getenv("GMAIL_RECIPIENT_ADDRESS") or os.getenv("GMAIL_SENDER_ADDRESS")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.google_space_webhook_url = os.getenv("GOOGLE_SPACE_WEBHOOK_URL")

config = AppConfig()
