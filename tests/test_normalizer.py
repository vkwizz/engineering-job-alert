import pytest
from src.job_alert.normalization.normalizer import generate_canonical_key, normalize_job
from src.job_alert.normalization.schemas import RawJobRecord

def test_canonical_key_generation():
    key1 = generate_canonical_key("Google", "Software Engineer Intern", "Bangalore")
    key2 = generate_canonical_key("Google LLC", "Software Engineer Intern", "Bangalore, India")
    assert key1 == key2

def test_normalize_raw_job():
    raw = RawJobRecord(
        source="jobspy",
        source_job_id="123",
        title="Backend Engineer Intern",
        company_name="Microsoft",
        location="Bengaluru",
        raw_description="Python Flask SQL",
        apply_url="https://careers.microsoft.com/job/123",
        source_url="https://linkedin.com/jobs/123"
    )

    norm = normalize_job(raw)
    assert norm is not None
    assert norm.company_name == "Microsoft"
    assert norm.title == "Backend Engineer Intern"
    assert norm.source == "jobspy"
