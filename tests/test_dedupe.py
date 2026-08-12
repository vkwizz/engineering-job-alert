import pytest
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.deduplication.dedupe import deduplicate_jobs

def test_deduplicate_identical_jobs():
    job1 = NormalizedJob(
        canonical_key="key_google_software_engineer_intern_bangalore",
        company_name="Google",
        title="Software Engineer Intern",
        location="Bangalore",
        source="jobspy",
        source_url="https://linkedin.com/jobs/123"
    )
    
    job2 = NormalizedJob(
        canonical_key="key_google_software_engineer_intern_bangalore",
        company_name="Google",
        title="Software Engineer Intern",
        location="Bangalore",
        source="serpapi",
        source_url="https://google.com/jobs/123"
    )

    job3 = NormalizedJob(
        canonical_key="key_microsoft_backend_intern_hyderabad",
        company_name="Microsoft",
        title="Backend Engineer Intern",
        location="Hyderabad",
        source="jobspy",
        source_url="https://indeed.com/jobs/456"
    )

    deduped = deduplicate_jobs([job1, job2, job3])
    assert len(deduped) == 2
    keys = [j.canonical_key for j in deduped]
    assert "key_google_software_engineer_intern_bangalore" in keys
    assert "key_microsoft_backend_intern_hyderabad" in keys
