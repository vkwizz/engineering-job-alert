import pytest
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.scoring.score import calculate_score

def test_high_priority_kerala_job_scoring():
    job = NormalizedJob(
        canonical_key="key_google_software_intern_kochi",
        company_name="Google",
        title="Software Engineer Intern",
        location="Kochi, Kerala",
        source="jobspy",
        source_url="https://example.com",
        confidence=90
    )

    ai_dict = {
        "is_target_technical_role": True,
        "student_eligible": True,
        "excluded_role": False
    }

    score = calculate_score(job, ai_dict)
    assert score >= 80

def test_low_score_unmatched_company():
    job = NormalizedJob(
        canonical_key="key_unknown_generic_role",
        company_name="Random Unknown Entity",
        title="General Engineer",
        location="Other Location",
        source="jobspy",
        source_url="https://example.com",
        confidence=50
    )

    score = calculate_score(job, {})
    assert score < 60
