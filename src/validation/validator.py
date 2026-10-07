"""
Data Validation Module for Superstore Sales Pipeline.

Validates:
1. File existence and schema integrity.
2. Required non-null columns.
3. Proper data types and parseability.
4. Valid date ranges and chronological logic (Ship Date >= Order Date).
5. Sensible numeric bounds (Sales > 0, Quantity >= 1, 0 <= Discount <= 1.0).
6. Unique primary identifier (Row ID).

Any invalid rows are saved to data/errors/ with detailed failure reasons.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from config.config import config
from src.utils.logger import get_logger

logger = get_logger("validation")

EXPECTED_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
]

REQUIRED_NOT_NULL_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Customer ID",
    "Product ID",
    "Sales",
    "Quantity",
    "Profit",
]


class DataValidationError(Exception):
    """Raised when data validation encounters fatal errors."""
    pass


def load_raw_csv(file_path: Path) -> pd.DataFrame:
    """Reads raw CSV handling UTF-8 or Windows-1252 encoding."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")

    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="windows-1252")

    return df


def validate_superstore_data(file_path: Path = None) -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    """
    Executes the comprehensive data validation suite on the raw dataset.
    Returns:
        (is_valid: bool, summary: dict, validated_df: pd.DataFrame)
    """
    csv_path = file_path or config.paths.raw_csv_path
    logger.info(f"Starting data validation on: {csv_path}")

    if not csv_path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {csv_path}")

    df = load_raw_csv(csv_path)
    total_rows = len(df)
    logger.info(f"Total rows read: {total_rows}")

    # Track check results
    checks_status = {
        "Required columns": False,
        "Data types": False,
        "Null values": False,
        "Dates": False,
        "Numeric values": False,
        "Duplicate IDs": False,
    }

    # 1. Schema / Expected columns check
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        logger.error(f"Schema mismatch: missing columns {missing_cols}")
        raise DataValidationError(f"Schema mismatch: missing columns {missing_cols}")
    checks_status["Required columns"] = True

    # Initialize error tracking mask for each row
    row_errors: Dict[int, List[str]] = {i: [] for i in df.index}

    # 2. Check Null values in required fields
    for col in REQUIRED_NOT_NULL_COLUMNS:
        null_mask = df[col].isnull()
        for idx in df[null_mask].index:
            row_errors[idx].append(f"Null value in required column: {col}")

    null_count = int(sum(df[c].isnull().sum() for c in REQUIRED_NOT_NULL_COLUMNS))
    checks_status["Null values"] = bool(null_count == 0)

    # 3. Check Dates
    order_dates = pd.to_datetime(df["Order Date"], format="mixed", errors="coerce")
    ship_dates = pd.to_datetime(df["Ship Date"], format="mixed", errors="coerce")

    # Flag unparseable dates
    unparseable_order = order_dates.isnull() & df["Order Date"].notnull()
    for idx in df[unparseable_order].index:
        row_errors[idx].append("Invalid/unparseable Order Date")

    unparseable_ship = ship_dates.isnull() & df["Ship Date"].notnull()
    for idx in df[unparseable_ship].index:
        row_errors[idx].append("Invalid/unparseable Ship Date")

    # Flag chronological inconsistency (ship date < order date)
    valid_dates_mask = order_dates.notnull() & ship_dates.notnull()
    impossible_dates = valid_dates_mask & (ship_dates < order_dates)
    for idx in df[impossible_dates].index:
        row_errors[idx].append("Impossible chronology: Ship Date is before Order Date")

    # Year range check (reasonable sales dates between 2000 and 2030)
    out_of_range_order = valid_dates_mask & ((order_dates.dt.year < 2000) | (order_dates.dt.year > 2030))
    for idx in df[out_of_range_order].index:
        row_errors[idx].append("Order Date out of realistic year range (2000-2030)")

    checks_status["Dates"] = not bool(unparseable_order.any() or unparseable_ship.any() or impossible_dates.any())

    # 4. Numeric Checks
    sales_numeric = pd.to_numeric(df["Sales"], errors="coerce")
    qty_numeric = pd.to_numeric(df["Quantity"], errors="coerce")
    disc_numeric = pd.to_numeric(df["Discount"], errors="coerce")
    prof_numeric = pd.to_numeric(df["Profit"], errors="coerce")

    for idx in df[sales_numeric.isnull() | (sales_numeric <= 0)].index:
        row_errors[idx].append("Sales must be a positive number (>0)")

    for idx in df[qty_numeric.isnull() | (qty_numeric <= 0) | (qty_numeric % 1 != 0)].index:
        row_errors[idx].append("Quantity must be a positive integer (>=1)")

    for idx in df[disc_numeric.isnull() | (disc_numeric < 0.0) | (disc_numeric > 1.0)].index:
        row_errors[idx].append("Discount must be between 0.0 and 1.0 (0% to 100%)")

    for idx in df[prof_numeric.isnull() | np.isinf(prof_numeric)].index:
        row_errors[idx].append("Profit must be a finite numeric value")

    numeric_valid = (
        sales_numeric.notnull().all()
        and (sales_numeric > 0).all()
        and qty_numeric.notnull().all()
        and (qty_numeric >= 1).all()
        and disc_numeric.notnull().all()
        and (disc_numeric >= 0.0).all()
        and (disc_numeric <= 1.0).all()
        and prof_numeric.notnull().all()
    )
    checks_status["Numeric values"] = bool(numeric_valid)
    checks_status["Data types"] = bool(numeric_valid and checks_status["Dates"])

    # 5. Duplicate Row ID check
    duplicate_row_ids = df.duplicated(subset=["Row ID"], keep=False)
    for idx in df[duplicate_row_ids].index:
        row_errors[idx].append("Duplicate Row ID detected")

    checks_status["Duplicate IDs"] = not bool(duplicate_row_ids.any())

    # Identify invalid vs valid rows
    invalid_indices = [idx for idx, errs in row_errors.items() if len(errs) > 0]
    valid_indices = [idx for idx, errs in row_errors.items() if len(errs) == 0]

    valid_rows_count = len(valid_indices)
    invalid_rows_count = len(invalid_indices)

    # Save invalid rows to data/errors/ if any exist
    if invalid_rows_count > 0:
        config.paths.errors_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        error_df = df.loc[invalid_indices].copy()
        error_df["validation_errors"] = ["; ".join(row_errors[idx]) for idx in invalid_indices]
        error_file = config.paths.errors_dir / f"invalid_rows_{timestamp}.csv"
        error_df.to_csv(error_file, index=False)
        logger.warning(f"Saved {invalid_rows_count} invalid rows to {error_file}")

    # Build and print the structured validation report
    lines = [
        "========================================",
        "VALIDATION RESULT",
        f"Rows checked: {total_rows}",
        f"Valid rows: {valid_rows_count}",
        f"Invalid rows: {invalid_rows_count}",
        "",
        "Checks:",
    ]
    for check_name, status in checks_status.items():
        symbol = "✓" if status else "✗"
        lines.append(f"{symbol} {check_name}")
    lines.append("========================================")

    report_str = "\n".join(lines)
    print(report_str)

    summary = {
        "rows_checked": total_rows,
        "valid_rows": valid_rows_count,
        "invalid_rows": invalid_rows_count,
        "checks": checks_status,
        "all_passed": invalid_rows_count == 0 and all(checks_status.values()),
    }

    if summary["all_passed"]:
        logger.info("Validation passed")
    else:
        logger.warning(f"Validation finished with {invalid_rows_count} rejected rows.")

    return summary["all_passed"], summary, df.loc[valid_indices].copy()


if __name__ == "__main__":
    is_valid, summary, valid_df = validate_superstore_data()
