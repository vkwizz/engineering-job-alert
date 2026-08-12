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

def passes_hard_filters(job: NormalizedJob) -> Tuple[bool, str]:
    title_lower = job.title.lower()
    desc_lower = (job.raw_description or "").lower()

    # 1. Reject roles requiring ANY prior professional experience (> 0 years)
    exp_patterns = [
        r'\b(?:[1-9]\d*)\+?\s*(?:years?|yrs?)\b', # 1+ years, 2+ yrs, 5 years
        r'\b[1-9]\d*\s*-\s*[1-9]\d*\s*(?:years?|yrs?)\b', # 1-2 years, 2-4 yrs
        r'\bmin(?:imum)?\s+[1-9]\d*\s*(?:years?|yrs?)\b',
        r'\bexperienced\b',
        r'\b(?:senior|lead|principal|staff|manager|head|director)\b',
        r'\b(?:software developer|software engineer|engineer)\s+(?:2|3|4|ii|iii|iv|v|level 2|level 3)\b'
    ]
    for pattern in exp_patterns:
        if re.search(pattern, title_lower) or re.search(pattern, desc_lower):
            # Allow "0-1 years" or "0 years" explicitly
            if re.search(r'\b0\s*(?:-\s*1)?\s*(?:years?|yrs?)\b', title_lower) or re.search(r'\b0\s*(?:-\s*1)?\s*(?:years?|yrs?)\b', desc_lower):
                pass
            else:
                return False, f"Requires professional experience (>0 yrs): '{pattern}'"

    # 2. Reject non-engineering roles explicitly excluded
    exclude_domains = config.prefs.technical_domains.exclude
    exclude_patterns = [domain.replace('_', ' ') for domain in exclude_domains]
    for pattern in exclude_patterns:
        if pattern in title_lower:
            return False, f"Excluded domain matched: {pattern}"

    # 3. Must be a student / placement / fresher / intern role eligible for B.Tech college students
    student_fresher_keywords = [
        "intern", "internship", "fresher", "trainee", "graduate", "campus", "entry level", 
        "junior", "placement", "b.tech", "btech", "b.e", "be", "2026", "2027", "associate"
    ]
    
    has_student_keyword = any(kw in title_lower for kw in student_fresher_keywords) or any(kw in desc_lower for kw in student_fresher_keywords)
    if not has_student_keyword and not ("engineer" in title_lower or "developer" in title_lower):
        return False, "Not eligible for B.Tech final year college students / freshers"

    # 4. Location & Company Tier Filter:
    # - Kerala: Allow ALL valid engineering fresher/intern jobs from ANY company (lower & higher rated companies allowed)
    # - Outside Kerala (Tamil Nadu, Karnataka, etc.): Allow ONLY Tier-1 Top MNC/Product companies (Google, Qualcomm, Amazon, Microsoft, etc.)
    in_kerala = is_kerala_location(job.location)
    matched_comp = matcher.match(job.company_name)

    if not in_kerala:
        if not matched_comp or matched_comp.tier != 1:
            return False, f"Outside Kerala ({job.location}): Only Tier-1 top companies (Google, Qualcomm, Amazon, etc.) are allowed"

    return True, "Passed hard filters"
