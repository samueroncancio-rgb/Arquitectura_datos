"""
Integration tests for database layers (Raw, Staging, Silver, Gold).
Gracefully skips if PostgreSQL container is not running.
"""

from decimal import Decimal
import pytest
from sqlalchemy import text
from src.utils.db import get_db_engine, check_db_connection


@pytest.fixture(scope="module")
def db_engine():
    """Provides a database engine if connected, else skips tests."""
    try:
        engine = get_db_engine()
        if not check_db_connection(engine):
            pytest.skip("PostgreSQL database is not accessible. Run 'docker compose up -d' for DB integration tests.")
        return engine
    except Exception as e:
        pytest.skip(f"PostgreSQL database is not accessible: {e}")


def test_db_layer_row_counts_and_completeness(db_engine):
    """Verifies row counts across data layers when DB is running."""
    with db_engine.connect() as conn:
        raw_count = conn.execute(text("SELECT COUNT(*) FROM raw.superstore;")).scalar()
        staging_count = conn.execute(text("SELECT COUNT(*) FROM staging.superstore;")).scalar()
        silver_fact_count = conn.execute(text("SELECT COUNT(*) FROM silver.fact_sales;")).scalar()

        assert raw_count == 9994
        assert staging_count == 9994
        assert silver_fact_count == 9994


def test_gold_tables_not_empty(db_engine):
    """Verifies that business gold tables are populated."""
    gold_tables = [
        "daily_sales",
        "monthly_sales",
        "category_performance",
        "product_performance",
        "customer_performance",
        "regional_performance",
    ]
    with db_engine.connect() as conn:
        for t in gold_tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM gold.{t};")).scalar()
            assert count > 0, f"Gold table gold.{t} is empty!"


def test_sales_total_consistency_between_silver_and_gold(db_engine):
    """Verifies that sum of sales in Silver fact matches sum of sales in Gold monthly aggregations within rounding tolerance."""
    with db_engine.connect() as conn:
        silver_sales = conn.execute(text("SELECT ROUND(SUM(sales), 2) FROM silver.fact_sales;")).scalar()
        gold_sales = conn.execute(text("SELECT ROUND(SUM(total_sales), 2) FROM gold.monthly_sales;")).scalar()

        # Monthly aggregation applies ROUND(SUM(sales), 2) per month (48 months), causing normal cent rounding variance
        assert abs(silver_sales - gold_sales) <= Decimal("0.05"), f"Mismatch between Silver ({silver_sales}) and Gold ({gold_sales}) sales totals!"

