import argparse
import logging
import sys
from src.job_alert.pipeline.runner import PipelineRunner
from src.job_alert.db.engine import Base, engine

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    parser = argparse.ArgumentParser(description="Personal Engineering Opportunity Intelligence Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run ingestion & scoring without writing to DB or sending alerts")
    parser.add_argument("--init-db", action="store_true", help="Initialize database schema tables")
    parser.add_argument("--max-queries", type=int, default=15, help="Maximum search query pairs to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    
    args = parser.parse_args()
    setup_logging(args.verbose)

    logging.info("Initializing Engineering Opportunity Intelligence Agent...")

    if args.init_db:
        logging.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialization complete.")
        if not args.dry_run:
            return

    # Always ensure tables exist before running
    Base.metadata.create_all(bind=engine)

    runner = PipelineRunner(dry_run=args.dry_run, max_queries=args.max_queries)
    runner.run()

    logging.info("Execution complete.")

if __name__ == "__main__":
    main()
