import logging
import requests
from typing import List
from src.job_alert.ingestion.base import JobSource
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.normalization.normalizer import generate_canonical_key
from src.job_alert.config import config

logger = logging.getLogger(__name__)

class SerpApiSource(JobSource):
    def fetch_jobs(self, query: str, location: str) -> List[NormalizedJob]:
        if not config.serpapi_api_key:
            logger.error("SERPAPI_API_KEY is missing")
            return []
            
        logger.info(f"Fetching jobs from SerpApi for query '{query}' in '{location}'")
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "api_key": config.serpapi_api_key,
            "hl": "en"
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            normalized_jobs = []
            for job_data in data.get("jobs_results", []):
                company_name = job_data.get("company_name", "")
                title = job_data.get("title", "")
                job_location = job_data.get("location", "")
                job_id = job_data.get("job_id", "")
                
                job = NormalizedJob(
                    canonical_key=generate_canonical_key(company_name, title, job_location),
                    title=title,
                    company_name=company_name,
                    location=job_location,
                    raw_description=job_data.get("description", ""),
                    apply_url=job_data.get("share_link", ""),
                    source="serpapi",
                    source_job_id=job_id,
                    source_url=job_data.get("share_link", ""),
                    source_raw_json=job_data,
                    confidence=90
                )
                normalized_jobs.append(job)
            return normalized_jobs
        except Exception as e:
            logger.error(f"SerpApi failed: {e}")
            return []
