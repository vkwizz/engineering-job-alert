import pytest
from src.job_alert.filtering.hard_filters import passes_hard_filters
from src.job_alert.normalization.schemas import NormalizedJob

def make_job(title: str, description: str = "", company: str = "TestCorp"):
    return NormalizedJob(
        canonical_key=f"test_{title}",
        company_name=company,
        title=title,
        location="Kerala",
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

def test_valid_engineering_intern_passes():
    job1 = make_job("Software Engineer Intern", description="Looking for B.Tech CS 2026 students")
    passed1, _ = passes_hard_filters(job1)
    assert passed1

    job2 = make_job("Backend Developer Fresher", description="Knowledge of Python, SQL, REST APIs")
    passed2, _ = passes_hard_filters(job2)
    assert passed2
