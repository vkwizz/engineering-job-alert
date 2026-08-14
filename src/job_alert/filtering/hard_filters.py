import re
from typing import Tuple
from src.job_alert.config import config
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.company.matcher import matcher

def is_kerala_location(location_str: str) -> bool:
    if not location_str:
        return False
    loc = location_str.lower()
    kerala_cities = [
        "kerala", "kochi", "cochin", "thiruvananthapuram", "trivandrum", 
        "kozhikode", "calicut", "thrissur", "trichur", "kollam", "quilon", 
        "kottayam", "kannur", "cannanore", "alappuzha", "alleppey", "palakkad", 
        "perintalmanna", "kalamassery", "ernakulam", "chengannur", "pattambi"
    ]
    return any(city in loc for city in kerala_cities)

def detect_experience_requirement(text: str) -> Tuple[bool, str]:
    """
    Checks if text specifies any prior professional experience (>0 years) or senior roles.
    Returns (has_experience_requirement, reason).
    """
    if not text:
        return False, ""
    
    text_lower = text.lower()

    # 1. Seniority and Experienced Titles / Keywords
    senior_patterns = [
        r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b',
        r'\bmanager\b', r'\bdirector\b', r'\bhead\b', r'\barchitect\b', r'\bexperienced\b',
        r'\bmid-senior\b', r'\bsde[- ]?2\b', r'\bsde[- ]?ii\b', r'\bsde[- ]?3\b', r'\bsde[- ]?iii\b',
        r'\bdeveloper[- ]?2\b', r'\bengineer[- ]?2\b', r'\blevel[- ]?2\b', r'\blevel[- ]?3\b',
        r'\bl2\b', r'\bl3\b', r'\bl4\b', r'\bl5\b'
    ]
    for pattern in senior_patterns:
        if re.search(pattern, text_lower):
            return True, f"Senior/experienced keyword matched: '{pattern}'"

    # 2. Check for experience ranges starting at 1+ or higher (e.g., "1-3 years", "2-5 yrs", "1 to 3 years")
    range_matches = re.findall(r'\b([0-9]{1,2})\s*(?:-|to|\b\s*-\s*)\s*([0-9]{1,2})\s*(?:years?|yrs?|yr)\b', text_lower)
    for min_exp, max_exp in range_matches:
        if int(min_exp) >= 1:
            return True, f"Requires {min_exp}-{max_exp} years experience"

    # 3. Check for plus years (e.g., "1+ years", "2+ yrs", "3+ year", "1 + year")
    plus_matches = re.findall(r'\b([1-9][0-9]?)\s*\+\s*(?:years?|yrs?|yr)\b', text_lower)
    for exp_str in plus_matches:
        if int(exp_str) >= 1:
            return True, f"Requires {exp_str}+ years experience"

    # 4. Check for minimum experience phrases (e.g., "minimum 1 year", "min 2 yrs", "at least 1 year")
    min_phrase_matches = re.findall(r'\b(?:minimum|min|at least)\s+([1-9][0-9]?)\s*(?:years?|yrs?|yr)\b', text_lower)
    for exp_str in min_phrase_matches:
        if int(exp_str) >= 1:
            return True, f"Requires minimum {exp_str} year(s) experience"

    # 5. Check for "X year(s) of experience" or "X year(s) experience" (where X >= 1)
    phrase_matches = re.findall(r'\b([1-9][0-9]?)\s*(?:years?|yrs?|yr)\s+(?:of\s+)?(?:relevant\s+)?experience\b', text_lower)
    for exp_str in phrase_matches:
        if int(exp_str) >= 1:
            return True, f"Requires {exp_str} year(s) experience"

    return False, ""

def passes_hard_filters(job: NormalizedJob) -> Tuple[bool, str]:
    title_lower = job.title.lower()
    desc_lower = (job.raw_description or "").lower()

    # 1. Title Experience & Seniority Check
    has_title_exp, title_reason = detect_experience_requirement(title_lower)
    if has_title_exp:
        return False, f"Title rejected: {title_reason}"

    # 2. Description Experience & Seniority Check
    has_desc_exp, desc_reason = detect_experience_requirement(desc_lower)
    if has_desc_exp:
        return False, f"Description rejected: {desc_reason}"

    # 3. Reject non-engineering roles explicitly excluded
    exclude_domains = config.prefs.technical_domains.exclude
    exclude_patterns = [domain.replace('_', ' ') for domain in exclude_domains]
    for pattern in exclude_patterns:
        if pattern in title_lower:
            return False, f"Excluded domain matched: {pattern}"

    # 4. Must be eligible for B.Tech students / freshers (0 years exp)
    student_fresher_keywords = [
        "intern", "internship", "fresher", "trainee", "graduate", "campus", "entry level", 
        "junior", "placement", "b.tech", "btech", "b.e", "be", "2026", "2027", "associate",
        "0-1", "0-2", "0 year", "0 yrs"
    ]
    
    has_student_keyword = any(kw in title_lower for kw in student_fresher_keywords) or any(kw in desc_lower for kw in student_fresher_keywords)
    if not has_student_keyword:
        return False, "Not eligible for B.Tech final year college students / freshers (missing student/fresher keyword)"

    # 5. Location & Company Tier Filter:
    # - Kerala: Allow ALL valid engineering fresher/intern jobs from ANY company (lower & higher rated companies allowed)
    # - Outside Kerala (Tamil Nadu, Karnataka, etc.): Allow ONLY Tier-1 Top MNC/Product companies (Google, Qualcomm, Amazon, Microsoft, etc.)
    in_kerala = is_kerala_location(job.location)
    matched_comp = matcher.match(job.company_name)

    if not in_kerala:
        if not matched_comp or matched_comp.tier != 1:
            return False, f"Outside Kerala ({job.location}): Only Tier-1 top companies (Google, Qualcomm, Amazon, etc.) are allowed"

    return True, "Passed hard filters"
