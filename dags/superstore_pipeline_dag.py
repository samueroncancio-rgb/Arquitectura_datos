"""
Apache Airflow DAG for Superstore End-to-End Data Pipeline.

Workflow:
download_dataset
   ↓
validate_raw_data
   ↓
load_raw
   ↓
transform_staging
   ↓
build_silver
   ↓
build_gold
   ↓
run_quality_tests
   ↓
pipeline_success
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to python path for DAG execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from airflow import DAG
from airflow.operators.python import PythonOperator
try:
    from airflow.operators.empty import EmptyOperator
except ImportError:
    from airflow.operators.dummy import DummyOperator as EmptyOperator  # Airflow <2.3 compatibility

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=10),
}


def task_download_dataset():
    """Downloads raw dataset and records metadata."""
    from src.ingestion.download import ingest_superstore_data
    meta = ingest_superstore_data()
    return meta


def task_validate_raw_data():
    """Validates raw dataset schema, nulls, types, and logic."""
    from src.validation.validator import validate_superstore_data, DataValidationError
    is_valid, summary, _ = validate_superstore_data()
    if not is_valid:
        raise DataValidationError(f"Raw data validation failed: {summary}")
    return summary


def task_load_raw():
    """Loads validated dataset into raw.superstore table."""
    from src.validation.validator import validate_superstore_data
    from src.loading.loader import load_raw_table
    _, _, valid_df = validate_superstore_data()
    count = load_raw_table(valid_df)
    return count


def task_transform_staging():
    """Standardizes types, formats, and columns in staging.superstore."""
    from src.transformation.transformer import run_staging_transformation
    return run_staging_transformation()


def task_build_silver():
    """Builds clean dimensional star schema (dim_*, fact_sales)."""
    from src.transformation.transformer import run_silver_transformation
    return run_silver_transformation()


def task_build_gold():
    """Builds analytical and KPI reporting tables."""
    from src.transformation.transformer import run_gold_transformation
    return run_gold_transformation()


def task_run_quality_tests():
    """Runs automated Pytest suite to verify pipeline data quality."""
    import pytest
    ret_code = pytest.main(["-v", str(PROJECT_ROOT / "tests")])
    if ret_code != 0:
        raise RuntimeError(f"Automated data quality tests failed with pytest exit code {ret_code}")


with DAG(
    dag_id="superstore_sales_pipeline",
    default_args=default_args,
    description="End-to-end ELT pipeline for Superstore Sales dataset",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["superstore", "sales", "analytics", "production"],
    doc_md=__doc__,
) as dag:

    download_dataset = PythonOperator(
        task_id="download_dataset",
        python_callable=task_download_dataset,
    )

    validate_raw_data = PythonOperator(
        task_id="validate_raw_data",
        python_callable=task_validate_raw_data,
    )

    load_raw = PythonOperator(
        task_id="load_raw",
        python_callable=task_load_raw,
    )

    transform_staging = PythonOperator(
        task_id="transform_staging",
        python_callable=task_transform_staging,
    )

    build_silver = PythonOperator(
        task_id="build_silver",
        python_callable=task_build_silver,
    )

    build_gold = PythonOperator(
        task_id="build_gold",
        python_callable=task_build_gold,
    )

    run_quality_tests = PythonOperator(
        task_id="run_quality_tests",
        python_callable=task_run_quality_tests,
    )

    pipeline_success = EmptyOperator(
        task_id="pipeline_success",
    )

    # Define clean pipeline dependencies
    (
        download_dataset
        >> validate_raw_data
        >> load_raw
        >> transform_staging
        >> build_silver
        >> build_gold
        >> run_quality_tests
        >> pipeline_success
    )
