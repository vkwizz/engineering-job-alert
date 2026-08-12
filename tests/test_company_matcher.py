import pytest
from src.job_alert.company.matcher import CompanyMatcher, normalize_company_name

def test_company_normalization():
    assert normalize_company_name("Google, Inc.") == "googleinc"
    assert normalize_company_name("Amazon Web Services") == "amazonwebservices"

def test_company_matching():
    matcher = CompanyMatcher()
    
    # Test canonical match
    google = matcher.match("Google")
    assert google is not None
    assert google.canonical_name == "Google"
    assert google.tier == 1

    # Test alias match
    aws = matcher.match("Amazon Web Services")
    assert aws is not None
    assert aws.canonical_name == "Amazon"

    # Test non-whitelisted company
    unknown = matcher.match("Unknown Local Startup LLC")
    assert unknown is None
