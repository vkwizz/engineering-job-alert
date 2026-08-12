from src.job_alert.config import config
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.company.matcher import matcher

def calculate_score(job: NormalizedJob, ai_classification: dict = None) -> int:
    score = 0
    weights = config.prefs.scoring
    
    # Company score
    comp = matcher.match(job.company_name)
    if comp:
        score += comp.company_score
    else:
        score += int(weights.company * 0.3)
        
    # Technical fit
    if ai_classification and ai_classification.get('is_target_technical_role'):
        score += weights.technical
    elif any(inc.replace('_', ' ') in job.title.lower() for inc in config.prefs.technical_domains.include):
        score += int(weights.technical * 0.8)
        
    # Student fit
    if 'intern' in job.title.lower() or 'fresher' in job.title.lower() or 'grad' in job.title.lower():
        score += weights.student
    elif ai_classification and ai_classification.get('student_eligible'):
        score += weights.student
        
    # Location
    job_loc_lower = (job.location or "").lower()
    loc_score_added = False
    for loc in config.prefs.locations.preferred:
        if loc.lower() in job_loc_lower:
            score += weights.location
            loc_score_added = True
            break
            
    if not loc_score_added and 'india' in job_loc_lower:
        score += int(weights.location * 0.5)
        
    # Freshness
    score += weights.freshness
    
    # Source confidence
    score += int(weights.source * (job.confidence / 100))
    
    return min(100, score)
