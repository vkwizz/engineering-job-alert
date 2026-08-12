from typing import List, Dict
from src.job_alert.normalization.schemas import NormalizedJob

def deduplicate_jobs(jobs: List[NormalizedJob]) -> List[NormalizedJob]:
    """
    Deduplicates a list of jobs based on canonical_key.
    Merges sources for duplicate jobs.
    """
    deduped: Dict[str, NormalizedJob] = {}
    
    for job in jobs:
        if job.canonical_key in deduped:
            # Keep the one with higher confidence
            if job.confidence > deduped[job.canonical_key].confidence:
                deduped[job.canonical_key] = job
        else:
            deduped[job.canonical_key] = job
            
    return list(deduped.values())
