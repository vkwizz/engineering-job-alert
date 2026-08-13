import logging
from typing import List
from src.job_alert.ingestion.base import JobSource
from src.job_alert.normalization.schemas import NormalizedJob
from src.job_alert.normalization.normalizer import generate_canonical_key
try:
    from jobspy import scrape_jobs
except ImportError:
    scrape_jobs = None

logger = logging.getLogger(__name__)

import concurrent.futures

class JobspySource(JobSource):
    def fetch_jobs(self, query: str, location: str) -> List[NormalizedJob]:
        if scrape_jobs is None:
            logger.error("jobspy is not installed")
            return []
            
        logger.info(f"Fetching jobs from JobSpy for query '{query}' in '{location}'")
        
        def _do_scrape():
            # Exclude glassdoor because datacenter IPs (Render) get instant 403 blocks
            return scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=query,
                location=location,
                results_wanted=15,
                country_ece="india"
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_scrape)
                jobs = future.result(timeout=15)
        except concurrent.futures.TimeoutError:
            logger.warning(f"JobSpy timed out after 15s for query '{query}' in '{location}'")
            return []
        except Exception as e:
            logger.error(f"JobSpy failed: {e}")
            return []
            
            normalized_jobs = []
            if jobs is not None and not jobs.empty:
                for idx, row in jobs.iterrows():
                    company_name = str(row.get('company', ''))
                    title = str(row.get('title', ''))
                    job_location = str(row.get('location', ''))
                    job_id = str(row.get('id', idx))
                    
                    job = NormalizedJob(
                        canonical_key=generate_canonical_key(company_name, title, job_location),
                        title=title,
                        company_name=company_name,
                        location=job_location,
                        raw_description=str(row.get('description', '')),
                        apply_url=str(row.get('job_url', '')),
                        source="jobspy",
                        source_job_id=job_id,
                        source_url=str(row.get('job_url', '')),
                        confidence=85
                    )
                    normalized_jobs.append(job)
            return normalized_jobs
        except Exception as e:
            logger.error(f"JobSpy failed: {e}")
            return []
