import re
from typing import Optional, Dict, Any
from src.job_alert.normalization.schemas import NormalizedJob

def normalize_title(title: str) -> str:
    """Normalize job title for deduplication."""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^\w\s]', ' ', title)
    return " ".join(title.split())

def generate_canonical_key(company: str, title: str, location: str) -> str:
    """Generate a unique key for deduplication."""
    from src.job_alert.company.matcher import matcher
    matched_comp = matcher.match(company)
    if matched_comp:
        company_norm = matched_comp.canonical_name.lower()
    else:
        company_clean = re.sub(r'\b(?:inc|llc|pvt|ltd|limited|corporation|corp)\b', '', str(company or 'unknown'), flags=re.IGNORECASE)
        company_norm = re.sub(r'[^\w\s]', '', company_clean.lower()).strip()
        
    title_norm = normalize_title(str(title or 'untitled'))
    # Extract primary city from location (e.g., 'Bangalore, India' -> 'bangalore')
    loc_primary = str(location or 'any').split(',')[0].strip()
    location_norm = re.sub(r'[^\w\s]', '', loc_primary.lower())
    return f"{company_norm}_{title_norm.replace(' ', '_')}_{location_norm}"

def normalize_job(raw_job: Any) -> Optional[NormalizedJob]:
    """
    Normalizes raw job dictionary or object into a NormalizedJob model.
    """
    if isinstance(raw_job, NormalizedJob):
        return raw_job

    if isinstance(raw_job, dict):
        company = raw_job.get("company_name") or raw_job.get("company") or "Unknown"
        title = raw_job.get("title") or "Untitled"
        location = raw_job.get("location") or "India"
        source = raw_job.get("source") or "unknown"
        source_job_id = str(raw_job.get("source_job_id") or raw_job.get("id") or hash(f"{company}_{title}"))
        apply_url = raw_job.get("apply_url") or raw_job.get("source_url")
        source_url = raw_job.get("source_url") or apply_url
        raw_description = raw_job.get("raw_description") or raw_job.get("description")
    else:
        company = getattr(raw_job, "company_name", None) or getattr(raw_job, "company", "Unknown")
        title = getattr(raw_job, "title", "Untitled")
        location = getattr(raw_job, "location", "India")
        source = getattr(raw_job, "source", "unknown")
        source_job_id = str(getattr(raw_job, "source_job_id", hash(f"{company}_{title}")))
        apply_url = getattr(raw_job, "apply_url", None) or getattr(raw_job, "source_url", None)
        source_url = getattr(raw_job, "source_url", None) or apply_url
        raw_description = getattr(raw_job, "raw_description", None) or getattr(raw_job, "description", None)

    canonical_key = generate_canonical_key(company, title, location)

    return NormalizedJob(
        canonical_key=canonical_key,
        title=title,
        company_name=company,
        location=location,
        raw_description=raw_description,
        apply_url=apply_url,
        source=source,
        source_job_id=source_job_id,
        source_url=source_url,
        confidence=getattr(raw_job, "confidence", 50) if not isinstance(raw_job, dict) else raw_job.get("confidence", 50)
    )
