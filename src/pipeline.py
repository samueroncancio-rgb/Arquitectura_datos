"""
Main Pipeline Runner for Superstore Sales ELT Pipeline.

Can be run directly via:
    python src/pipeline.py
or
    python -m src.pipeline
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.utils.logger import get_logger
from src.utils.db import get_db_engine, check_db_connection
from src.ingestion.download import ingest_superstore_data
from src.validation.validator import validate_superstore_data, DataValidationError
from src.loading.loader import load_raw_table
from src.transformation.transformer import (
    run_staging_transformation,
    run_silver_transformation,
    run_gold_transformation,
)

logger = get_logger("pipeline_runner")


def run_pipeline(force_download: bool = False, run_tests: bool = True) -> bool:
    """
    Executes the entire end-to-end pipeline in sequential order.
    Fully idempotent: safe to execute multiple times.
    """
    try:
        # Step 1: Ingestion
        ingest_metadata = ingest_superstore_data(force_download=force_download)

        # Step 2: Validation
        is_valid, validation_summary, valid_df = validate_superstore_data()
        if not is_valid:
            logger.error("Pipeline stopped due to critical validation errors.")
            return False

        # Generate Visual Analytics Dashboard
        from src.utils.generate_dashboard import generate_html_dashboard
        dashboard_path = generate_html_dashboard()
        logger.info(f"Visual Analytics Dashboard generated at: file://{dashboard_path.resolve()}")

        # Step 3: Database Connection Check
        engine = get_db_engine()
        if not check_db_connection(engine):
            logger.warning(
                "PostgreSQL is not reachable. Please start the database container using:\n"
                "    docker compose up -d\n"
                "Raw data validation completed successfully."
            )
            if run_tests:
                logger.info("Running offline data quality tests...")
                pytest.main(["-v", str(PROJECT_ROOT / "tests")])
            return False

        # Step 4: Load Raw Table
        load_raw_table(valid_df, engine=engine)

        # Step 5: Staging Transformation
        run_staging_transformation(engine=engine)

        # Step 6: Silver Dimensional Modeling
        run_silver_transformation(engine=engine)

        # Step 7: Gold Analytical Aggregations
        run_gold_transformation(engine=engine)

        # Step 8: Automated Data Quality Tests
        if run_tests:
            logger.info("Running automated data quality tests...")
            exit_code = pytest.main(["-v", str(PROJECT_ROOT / "tests")])
            if exit_code == 0:
                logger.info("Quality tests passed")
            else:
                logger.error(f"Quality tests failed with code {exit_code}")
                return False

        logger.info("Pipeline executed successfully!")
        return True

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Superstore Data Pipeline")
    parser.add_argument("--force-download", action="store_true", help="Force re-downloading source dataset")
    parser.add_argument("--no-tests", action="store_true", help="Skip automated pytest suite at the end")
    args = parser.parse_args()

    success = run_pipeline(
        force_download=args.force_download,
        run_tests=not args.no_tests,
    )
    sys.exit(0 if success else 1)
