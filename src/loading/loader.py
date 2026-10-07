"""
Raw Data Loading Module.

Responsible for:
1. Ensuring database schemas and raw.superstore table exist.
2. Truncating raw.superstore for idempotent reload.
3. Loading validated source data directly into raw.superstore without business transformations.
4. Logging progress and verifying row counts.
"""

from typing import Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.config import config
from src.utils.logger import get_logger
from src.utils.db import get_db_engine, check_db_connection, execute_sql_file

logger = get_logger("loader")


def load_raw_table(df: pd.DataFrame, engine: Optional[Engine] = None) -> int:
    """
    Loads raw validated DataFrame into PostgreSQL raw.superstore.
    Ensures idempotency by truncating existing data before insert.
    """
    eng = engine or get_db_engine()

    if not check_db_connection(eng):
        raise ConnectionError(
            f"Cannot connect to PostgreSQL at {config.postgres.host}:{config.postgres.port}. "
            f"Ensure PostgreSQL is running (e.g. via 'docker compose up -d')."
        )

    # 1. Initialize schemas
    init_sql = config.paths.sql_dir / "init_db.sql"
    if init_sql.is_file():
        execute_sql_file(init_sql, eng)

    # 2. Ensure raw table DDL
    raw_ddl_sql = config.paths.sql_dir / "raw" / "create_raw_superstore.sql"
    if raw_ddl_sql.is_file():
        execute_sql_file(raw_ddl_sql, eng)

    # 3. Truncate raw.superstore for idempotency
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw.superstore;"))

    # Convert all columns to string representations to match raw source representation
    df_raw = df.astype(str)

    # 4. Insert into raw.superstore
    df_raw.to_sql(
        name="superstore",
        schema=config.postgres.schema_raw,
        con=eng,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    # 5. Verify row count
    with eng.connect() as conn:
        loaded_count = conn.execute(text("SELECT COUNT(*) FROM raw.superstore;")).scalar()

    logger.info("Raw table loaded")
    logger.info(f"Loaded {loaded_count} rows into {config.postgres.schema_raw}.superstore")

    return loaded_count


if __name__ == "__main__":
    from src.validation.validator import validate_superstore_data
    _, _, valid_df = validate_superstore_data()
    load_raw_table(valid_df)
