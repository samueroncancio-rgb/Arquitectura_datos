"""
Transformation Runner Module.

Executes SQL scripts for:
1. Staging layer (standardization, types, snake_case)
2. Silver layer (dimensional star schema: dim_*, fact_sales)
3. Gold layer (business aggregations and KPIs)
"""

from typing import Optional, Dict
from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.config import config
from src.utils.logger import get_logger
from src.utils.db import get_db_engine, execute_sql_file, check_db_connection

logger = get_logger("transformation")


def run_staging_transformation(engine: Optional[Engine] = None) -> int:
    """Executes staging transformation script and returns row count."""
    eng = engine or get_db_engine()
    sql_file = config.paths.sql_dir / "staging" / "transform_staging.sql"

    logger.info("Starting Staging transformation")
    execute_sql_file(sql_file, eng)

    with eng.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM staging.superstore;")).scalar()

    logger.info("Staging transformation completed")
    logger.info(f"staging.superstore contains {count} rows")
    return count


def run_silver_transformation(engine: Optional[Engine] = None) -> Dict[str, int]:
    """Executes silver dimensional modeling scripts and returns table counts."""
    eng = engine or get_db_engine()
    sql_file = config.paths.sql_dir / "silver" / "build_silver.sql"

    logger.info("Starting Silver transformation")
    execute_sql_file(sql_file, eng)

    counts = {}
    with eng.connect() as conn:
        counts["dim_date"] = conn.execute(text("SELECT COUNT(*) FROM silver.dim_date;")).scalar()
        counts["dim_customers"] = conn.execute(text("SELECT COUNT(*) FROM silver.dim_customers;")).scalar()
        counts["dim_products"] = conn.execute(text("SELECT COUNT(*) FROM silver.dim_products;")).scalar()
        counts["dim_geography"] = conn.execute(text("SELECT COUNT(*) FROM silver.dim_geography;")).scalar()
        counts["fact_sales"] = conn.execute(text("SELECT COUNT(*) FROM silver.fact_sales;")).scalar()

    logger.info("Silver transformation completed")
    logger.info(f"Silver counts: {counts}")
    return counts


def run_gold_transformation(engine: Optional[Engine] = None) -> Dict[str, int]:
    """Executes gold business layer aggregation scripts and returns table counts."""
    eng = engine or get_db_engine()
    sql_file = config.paths.sql_dir / "gold" / "build_gold.sql"

    logger.info("Starting Gold transformation")
    execute_sql_file(sql_file, eng)

    gold_counts = {}
    tables = [
        "daily_sales",
        "monthly_sales",
        "category_performance",
        "product_performance",
        "customer_performance",
        "regional_performance",
    ]
    with eng.connect() as conn:
        for t in tables:
            gold_counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM gold.{t};")).scalar()

    logger.info("Gold tables created")
    logger.info(f"Gold table counts: {gold_counts}")
    return gold_counts


def run_all_transformations(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """Runs staging, silver, and gold transformation stages sequentially."""
    eng = engine or get_db_engine()
    if not check_db_connection(eng):
        raise ConnectionError(
            f"Cannot connect to PostgreSQL at {config.postgres.host}:{config.postgres.port}. "
            "Ensure PostgreSQL is running."
        )

    staging_count = run_staging_transformation(eng)
    silver_counts = run_silver_transformation(eng)
    gold_counts = run_gold_transformation(eng)

    return {
        "staging": staging_count,
        "silver": silver_counts,
        "gold": gold_counts,
    }


if __name__ == "__main__":
    run_all_transformations()
