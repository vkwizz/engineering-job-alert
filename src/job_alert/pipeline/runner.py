import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.job_alert.ingestion.jobspy_source import JobspySource
from src.job_alert.ingestion.serpapi_source import SerpApiSource
from src.job_alert.ingestion.queries import generate_search_matrix
from src.job_alert.deduplication.dedupe import deduplicate_jobs
from src.job_alert.filtering.hard_filters import passes_hard_filters
from src.job_alert.ai.classifier import AIClassifier
from src.job_alert.scoring.score import calculate_score
from src.job_alert.notifications.telegram import send_telegram_alert
from src.job_alert.notifications.gmail import send_gmail_alert, send_digest_email
from src.job_alert.config import config
from src.job_alert.db.engine import SessionLocal
from src.job_alert.db.models import Job, JobSource, JobAnalysis, Alert, Run, Company

logger = logging.getLogger(__name__)

def utcnow():
    return datetime.now(timezone.utc)

class PipelineRunner:
    def __init__(self, dry_run: bool = False, max_queries: int = 15):
        self.jobspy = JobspySource()
        self.serpapi = SerpApiSource()
        self.classifier = AIClassifier()
        self.db = SessionLocal()
        self.dry_run = dry_run
        self.max_queries = max_queries

    def run(self):
        logger.info(f"Starting pipeline run (dry_run={self.dry_run})...")
        
        # 0. Record run start in DB
        run_record = None
        if not self.dry_run:
            run_record = Run(started_at=utcnow(), status="running")
            self.db.add(run_record)
            self.db.commit()
            self.db.refresh(run_record)

        stats = {
            "jobs_fetched": 0,
            "jobs_normalized": 0,
            "jobs_deduplicated": 0,
            "jobs_rejected": 0,
            "jobs_ai_classified": 0,
            "jobs_alerted": 0,
        }

        digest_candidates = []

        try:
            # 1. Ingestion via search matrix
            search_items = generate_search_matrix(max_queries=self.max_queries)
            raw_jobs = []

            total_items = len(search_items)
            for idx, item in enumerate(search_items, 1):
                query, loc = item["query"], item["location"]
                logger.info(f"[{idx}/{total_items}] Discovering jobs for: query='{query}', location='{loc}'")
                
                try:
                    js_jobs = self.jobspy.fetch_jobs(query, loc)
                    raw_jobs.extend(js_jobs)
                except Exception as e:
                    logger.error(f"JobSpy error for {query} in {loc}: {e}")

                try:
                    sa_jobs = self.serpapi.fetch_jobs(query, loc)
                    raw_jobs.extend(sa_jobs)
                except Exception as e:
                    logger.error(f"SerpApi error for {query} in {loc}: {e}")

            stats["jobs_fetched"] = len(raw_jobs)
            stats["jobs_normalized"] = len(raw_jobs)
            logger.info(f"Fetched total {len(raw_jobs)} raw job records")

            # 2. Normalization & Deduplication
            deduped = deduplicate_jobs(raw_jobs)
            stats["jobs_deduplicated"] = len(deduped)
            logger.info(f"Deduplicated down to {len(deduped)} unique canonical jobs")

            # 3. Filtering, AI Classification & Scoring
            for norm_job in deduped:
                # Deterministic Hard Filter
                passed, reason = passes_hard_filters(norm_job)
                if not passed:
                    logger.info(f"Job '{norm_job.title}' @ '{norm_job.company_name}' REJECTED: {reason}")
                    stats["jobs_rejected"] += 1
                    continue

                # AI Semantic Classification
                ai_dict = {}
                ai_class = self.classifier.classify_job(norm_job)
                if ai_class:
                    stats["jobs_ai_classified"] += 1
                    ai_dict = ai_class.model_dump()
                    if ai_class.excluded_role:
                        logger.info(f"Job '{norm_job.title}' REJECTED by AI classifier")
                        stats["jobs_rejected"] += 1
                        continue

                # Hybrid Scoring
                score = calculate_score(norm_job, ai_dict)
                summary = ai_dict.get("summary") or f"Role matching target preferences at {norm_job.company_name} in {norm_job.location}."
                
                logger.info(f"PASSED: '{norm_job.title}' @ '{norm_job.company_name}' -> Score: {score}/100")

                # Persistence & Alerting
                alerted = self._process_job(norm_job, score, summary, ai_dict)
                if alerted:
                    stats["jobs_alerted"] += 1
                    digest_candidates.append({"job": norm_job, "score": score, "summary": summary})

            # Send aggregated digest if configured
            if digest_candidates and not self.dry_run:
                send_digest_email(digest_candidates)

            # Mark run complete
            if run_record:
                run_record.status = "completed"
                run_record.finished_at = utcnow()
                for key, val in stats.items():
                    setattr(run_record, key, val)
                self.db.commit()

            logger.info(f"Pipeline run finished successfully. Stats: {stats}")

        except Exception as e:
            logger.exception(f"Pipeline run encountered unexpected error: {e}")
            if run_record:
                run_record.status = "failed"
                run_record.finished_at = utcnow()
                run_record.error_summary = str(e)
                self.db.commit()

    def _process_job(self, norm_job, score: int, summary: str, ai_dict: dict) -> bool:
        if self.dry_run:
            logger.info(f"[DRY RUN] Would save job and trigger alerts for '{norm_job.title}' (Score: {score})")
            return score >= config.prefs.alerts.immediate_threshold

        existing = self.db.query(Job).filter(Job.canonical_key == norm_job.canonical_key).first()
        if existing:
            existing.last_seen_at = utcnow()
            self.db.commit()
            return False

        # Create new Job record
        job = Job(
            canonical_key=norm_job.canonical_key,
            title=norm_job.title,
            normalized_title=norm_job.title.lower(),
            location=norm_job.location,
            raw_description=norm_job.raw_description,
            apply_url=norm_job.apply_url,
            status="new"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        source = JobSource(
            job_id=job.id,
            source=norm_job.source,
            source_job_id=norm_job.source_job_id,
            source_url=norm_job.source_url,
            source_confidence=norm_job.confidence
        )
        self.db.add(source)

        analysis = JobAnalysis(
            job_id=job.id,
            final_score=float(score),
            ai_reasoning_summary=summary,
            student_eligible=ai_dict.get("student_eligible"),
            is_internship=ai_dict.get("is_internship"),
            is_graduate_role=ai_dict.get("is_graduate_role"),
            is_target_technical_role=ai_dict.get("is_target_technical_role"),
            is_excluded_role=ai_dict.get("excluded_role", False)
        )
        self.db.add(analysis)
        self.db.commit()

        # Send Notifications if score passes threshold
        alert_sent = False
        if score >= config.prefs.alerts.immediate_threshold:
            # Send Telegram Alert
            send_telegram_alert(norm_job, score, summary)
            
            # Send Gmail Alert
            send_gmail_alert(norm_job, score, summary)

            # Send Google Space Alert (if webhook configured)
            from src.job_alert.notifications.google_space import send_google_space_alert
            send_google_space_alert(norm_job, score, summary)

            # Record Alert in DB
            alert_rec = Alert(
                job_id=job.id,
                channel="multi",
                alert_type="immediate",
                notification_key=f"alert_{job.id}_{int(utcnow().timestamp())}",
                status="sent"
            )
            self.db.add(alert_rec)
            self.db.commit()
            alert_sent = True

        return alert_sent
