"""
Data Ingestion Module for Superstore Sales Pipeline.

Responsible for:
1. Programmatically downloading the Superstore dataset from Kaggle (or verified source).
2. Extracting and locating the raw CSV.
3. Preserving the exact original raw data into data/raw/superstore.csv.
4. Recording rich ingestion metadata (timestamp, source, size, row count, sha256 checksum).
"""

import os
import json
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import pandas as pd

from config.config import config
from src.utils.logger import get_logger

logger = get_logger("ingestion")


def compute_sha256(file_path: Path) -> str:
    """Calculates the SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def count_csv_rows(file_path: Path) -> int:
    """Counts data rows in a CSV file excluding the header."""
    count = 0
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for _ in f:
            count += 1
    return max(0, count - 1)


def has_kaggle_credentials() -> bool:
    """Checks if Kaggle API credentials are configured."""
    has_env = bool(config.kaggle.username and config.kaggle.key)
    has_file = (Path.home() / ".kaggle" / "kaggle.json").is_file()
    return has_env or has_file


def download_from_kaggle(dataset_slug: str, target_dir: Path) -> Optional[Path]:
    """Downloads dataset from Kaggle using official Kaggle API."""
    logger.info(f"Attempting download from Kaggle dataset: {dataset_slug}")

    # Set environment variables for Kaggle API if provided in config
    if config.kaggle.username and config.kaggle.key:
        os.environ["KAGGLE_USERNAME"] = config.kaggle.username
        os.environ["KAGGLE_KEY"] = config.kaggle.key

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        target_dir.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(dataset_slug, path=str(target_dir), unzip=True)
        logger.info(f"Kaggle download successful for dataset: {dataset_slug}")

        # Find the extracted CSV file
        csv_files = list(target_dir.glob("*.csv"))
        if csv_files:
            return csv_files[0]
        return None
    except Exception as e:
        logger.warning(f"Kaggle API download failed or credentials missing: {e}")
        return None


def download_from_url(url: str, target_path: Path) -> Path:
    """Downloads dataset directly from URL as fallback/reproducible source."""
    logger.info(f"Downloading dataset from verified mirror: {url}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return target_path


def ingest_superstore_data(force_download: bool = False) -> Dict[str, Any]:
    """
    Main ingestion function.
    Downloads, stores raw dataset and records ingestion metadata.
    """
    logger.info("Starting ingestion")
    raw_dir = config.paths.raw_data_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    target_csv = config.paths.raw_csv_path
    metadata_path = raw_dir / "ingestion_metadata.json"

    source_used = "local_cache"

    # If raw CSV already exists and force_download is False, use existing file
    if target_csv.is_file() and not force_download:
        logger.info(f"Raw data file already exists at {target_csv}. Preserving raw file.")
    else:
        downloaded_file = None
        if has_kaggle_credentials():
            downloaded_file = download_from_kaggle(config.kaggle.dataset, raw_dir)
            if downloaded_file:
                source_used = f"kaggle:{config.kaggle.dataset}"

        if not downloaded_file:
            logger.info("Kaggle credentials not provided or download unavailable. Using verified public mirror.")
            temp_path = raw_dir / "downloaded_superstore.csv"
            download_from_url(config.kaggle.fallback_url, temp_path)
            downloaded_file = temp_path
            source_used = f"mirror:{config.kaggle.fallback_url}"

        # Ensure target is saved as superstore.csv without altering contents
        if downloaded_file != target_csv:
            shutil.copy2(downloaded_file, target_csv)
            if downloaded_file.name != target_csv.name and downloaded_file.exists():
                try:
                    downloaded_file.unlink()
                except OSError:
                    pass

        logger.info("Download completed")

    # Record and calculate ingestion metadata
    file_size_bytes = target_csv.stat().st_size
    checksum = compute_sha256(target_csv)
    row_count = count_csv_rows(target_csv)

    logger.info(f"Rows detected: {row_count}")

    metadata = {
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source_used,
        "kaggle_dataset_configured": config.kaggle.dataset,
        "raw_file_name": target_csv.name,
        "raw_file_path": str(target_csv),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 3),
        "row_count": row_count,
        "sha256_checksum": checksum,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Ingestion metadata written to {metadata_path}")
    return metadata


if __name__ == "__main__":
    meta = ingest_superstore_data()
    print("Ingestion Metadata Summary:\n", json.dumps(meta, indent=2))
