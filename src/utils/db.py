"""
Database utility module for Superstore Data Pipeline.
Manages SQLAlchemy engine, connection checks, and SQL script execution.
"""

from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from config.config import config
from src.utils.logger import get_logger

logger = get_logger("db_utils")


def get_db_engine(uri: Optional[str] = None) -> Engine:
    """Returns a configured SQLAlchemy engine."""
    db_uri = uri or config.postgres.connection_uri
    return create_engine(db_uri, pool_pre_ping=True)


def check_db_connection(engine: Optional[Engine] = None) -> bool:
    """Tests whether the database connection is live and reachable."""
    eng = engine or get_db_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1;"))
            return True
    except OperationalError as e:
        logger.warning(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking database connection: {e}")
        return False


def execute_sql_file(file_path: Path, engine: Optional[Engine] = None) -> None:
    """Reads a SQL file and executes its statements within a transaction."""
    eng = engine or get_db_engine()
    if not file_path.is_file():
        raise FileNotFoundError(f"SQL file not found at: {file_path}")

    sql_content = file_path.read_text(encoding="utf-8")
    with eng.begin() as conn:
        conn.execute(text(sql_content))
    logger.debug(f"Executed SQL script: {file_path.name}")
