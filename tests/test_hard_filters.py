import pytest
from src.job_alert.filtering.hard_filters import passes_hard_filters
from src.job_alert.normalization.schemas import NormalizedJob

def make_job(title: str, description: str = "", company: str = "Google", location: str = "Kerala"):
    return NormalizedJob(
        canonical_key=f"test_{title}",
        company_name=company,
        title=title,
        location=location,
        raw_description=description,
        source="test",
        source_url="https://example.com"
    )

def test_senior_roles_rejected():
    job1 = make_job("Senior Software Engineer")
    passed1, reason1 = passes_hard_filters(job1)
    assert not passed1

    job2 = make_job("Software Development Manager")
    passed2, _ = passes_hard_filters(job2)
    assert not passed2

    job3 = make_job("Software Engineer", description="Requires 5+ years of experience in Java")
    passed3, _ = passes_hard_filters(job3)
    assert not passed3

def test_excluded_domains_rejected():
    job1 = make_job("Data Analyst Intern")
    passed1, reason1 = passes_hard_filters(job1)
    assert not passed1
    assert "Excluded domain matched" in reason1

    job2 = make_job("HR Specialist Trainee")
    passed2, _ = passes_hard_filters(job2)
    assert not passed2

def test_valid_engineering_intern_passes_kerala():
    # In Kerala, non-Tier-1 local company passes
    job1 = make_job("Software Engineer Intern", description="Looking for B.Tech CS 2026 students", company="Local Startup Kochi", location="Kochi, Kerala")
    passed1, _ = passes_hard_filters(job1)
    assert passed1

def test_outside_kerala_requires_tier1():
    # Outside Kerala (Chennai), Tier 1 company Google passes
    google_tn = make_job("Software Engineer Intern", description="B.Tech 2026", company="Google", location="Chennai, Tamil Nadu")
    passed1, _ = passes_hard_filters(google_tn)
    assert passed1

    # Outside Kerala (Chennai), non-Tier-1 company is REJECTED
    unknown_tn = make_job("Software Engineer Intern", description="B.Tech 2026", company="Unknown Ordinary Corp", location="Chennai, Tamil Nadu")
    passed2, reason2 = passes_hard_filters(unknown_tn)
    assert not passed2
    assert "Only Tier-1 top companies" in reason2
