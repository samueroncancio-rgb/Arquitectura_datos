"""
Configuration module for the Superstore Data Pipeline.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from base directory
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class KaggleConfig:
    username: str = os.getenv("KAGGLE_USERNAME", "")
    key: str = os.getenv("KAGGLE_KEY", "")
    dataset: str = os.getenv("KAGGLE_DATASET", "bravehart101/sample-superstore-dataset")
    # Verified public mirror URL for the exact 9,994-row dataset if Kaggle credentials are not provided
    fallback_url: str = os.getenv(
        "SUPERSTORE_FALLBACK_URL",
        "https://raw.githubusercontent.com/Muskan40/SampleStore_EDA/master/Sample%20-%20Superstore.csv",
    )


@dataclass(frozen=True)
class PostgresConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    db: str = os.getenv("POSTGRES_DB", "superstore_db")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")

    schema_raw: str = os.getenv("POSTGRES_SCHEMA_RAW", "raw")
    schema_staging: str = os.getenv("POSTGRES_SCHEMA_STAGING", "staging")
    schema_silver: str = os.getenv("POSTGRES_SCHEMA_SILVER", "silver")
    schema_gold: str = os.getenv("POSTGRES_SCHEMA_GOLD", "gold")

    @property
    def connection_uri(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


@dataclass(frozen=True)
class PathConfig:
    base_dir: Path = BASE_DIR
    raw_data_dir: Path = BASE_DIR / "data" / "raw"
    raw_csv_path: Path = BASE_DIR / os.getenv("RAW_DATA_PATH", "data/raw/superstore.csv")
    errors_dir: Path = BASE_DIR / os.getenv("ERRORS_DATA_PATH", "data/errors")
    processed_dir: Path = BASE_DIR / os.getenv("PROCESSED_DATA_PATH", "data/processed")
    sql_dir: Path = BASE_DIR / "sql"
    logs_dir: Path = BASE_DIR / "logs"


@dataclass(frozen=True)
class AppConfig:
    kaggle: KaggleConfig = KaggleConfig()
    postgres: PostgresConfig = PostgresConfig()
    paths: PathConfig = PathConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


# Global config instance
config = AppConfig()
