import os
import logging
import threading
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from src.job_alert.pipeline.runner import PipelineRunner
from src.job_alert.db.engine import Base, engine, SessionLocal
from src.job_alert.db.models import Job, Run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("job_alert.server")

pipeline_lock = threading.Lock()
pipeline_state = {
    "is_running": False,
    "last_run_started": None,
    "last_run_finished": None,
    "last_run_status": None,
    "total_runs": 0,
}

scheduler = BackgroundScheduler()

def execute_pipeline():
    """Thread-safe execution wrapper for pipeline runner."""
    if not pipeline_lock.acquire(blocking=False):
        logger.warning("Pipeline run skipped: previous run is still in progress.")
        return False

    try:
        pipeline_state["is_running"] = True
        pipeline_state["last_run_started"] = datetime.now(timezone.utc).isoformat()
        pipeline_state["total_runs"] += 1
        logger.info("Starting scheduled/triggered job alert pipeline run...")

        # Ensure database tables exist before execution
        Base.metadata.create_all(bind=engine)

        max_queries = int(os.getenv("MAX_QUERIES", "15"))
        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

        runner = PipelineRunner(dry_run=dry_run, max_queries=max_queries)
        runner.run()

        pipeline_state["last_run_status"] = "success"
        logger.info("Pipeline execution completed successfully.")
        return True
    except Exception as e:
        pipeline_state["last_run_status"] = f"failed: {str(e)}"
        logger.exception("Pipeline execution failed with exception.")
        return False
    finally:
        pipeline_state["is_running"] = False
        pipeline_state["last_run_finished"] = datetime.now(timezone.utc).isoformat()
        pipeline_lock.release()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema validated at startup.")
    except Exception as e:
        logger.error(f"Error initializing DB schema on startup: {e}")

    # Setup background scheduler interval (default: 6 hours)
    interval_hours = int(os.getenv("RUN_INTERVAL_HOURS", "6"))
    scheduler.add_job(execute_pipeline, 'interval', hours=interval_hours, id="job_alert_pipeline")
    scheduler.start()
    logger.info(f"Background scheduler started. Pipeline scheduled every {interval_hours} hours.")

    # Trigger initial run in background on startup if configured (default: true)
    if os.getenv("RUN_ON_STARTUP", "true").lower() == "true":
        thread = threading.Thread(target=execute_pipeline, daemon=True)
        thread.start()

    yield

    # Shutdown logic
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")

app = FastAPI(
    title="Engineering Job Alert Agent API",
    description="24/7 background worker and HTTP health monitor for automated job intelligence.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {
        "service": "Engineering Job Alert Agent",
        "status": "running",
        "health_check": "/health",
        "trigger_run": "/run",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    db_healthy = False
    job_count = 0
    try:
        db = SessionLocal()
        job_count = db.query(Job).count()
        db_healthy = True
        db.close()
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    next_run = None
    job = scheduler.get_job("job_alert_pipeline")
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()

    return {
        "status": "ok" if db_healthy else "degraded",
        "database_connected": db_healthy,
        "total_jobs_in_db": job_count,
        "pipeline_state": pipeline_state,
        "next_scheduled_run": next_run
    }

@app.api_route("/run", methods=["GET", "POST"])
def trigger_run(background_tasks: BackgroundTasks):
    if pipeline_state["is_running"]:
        return {"status": "in_progress", "message": "Pipeline is already running."}
    
    background_tasks.add_task(execute_pipeline)
    return {"status": "triggered", "message": "Pipeline run triggered successfully in background."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("src.job_alert.server:app", host="0.0.0.0", port=port, reload=False)
