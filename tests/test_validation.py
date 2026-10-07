"""
Unit tests for data validation module.
Verifies column existence, type checks, missing values, date logic, and error routing.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.validation.validator import (
    validate_superstore_data,
    EXPECTED_COLUMNS,
    REQUIRED_NOT_NULL_COLUMNS,
    DataValidationError,
)
from config.config import config


def test_expected_columns_definition():
    """Verify all 21 columns of the Superstore dataset are specified."""
    assert len(EXPECTED_COLUMNS) == 21
    assert "Row ID" in EXPECTED_COLUMNS
    assert "Order ID" in EXPECTED_COLUMNS
    assert "Sales" in EXPECTED_COLUMNS
    assert "Profit" in EXPECTED_COLUMNS
    assert "Quantity" in EXPECTED_COLUMNS


def test_validation_passes_on_real_raw_dataset():
    """Validates that the source Superstore dataset passes all validation rules."""
    assert config.paths.raw_csv_path.is_file(), "Raw dataset file must exist for test"
    is_valid, summary, valid_df = validate_superstore_data(config.paths.raw_csv_path)

    assert is_valid is True
    assert summary["rows_checked"] == 9994
    assert summary["valid_rows"] == 9994
    assert summary["invalid_rows"] == 0
    assert summary["checks"]["Required columns"] is True
    assert summary["checks"]["Data types"] is True
    assert summary["checks"]["Null values"] is True
    assert summary["checks"]["Dates"] is True
    assert summary["checks"]["Numeric values"] is True
    assert summary["checks"]["Duplicate IDs"] is True
    assert len(valid_df) == 9994


def test_validation_detects_missing_columns(tmp_path):
    """Ensures validator raises DataValidationError when required columns are absent."""
    broken_csv = tmp_path / "broken_schema.csv"
    df = pd.DataFrame({"Order ID": ["CA-1"], "Sales": [10.0]})
    df.to_csv(broken_csv, index=False)

    with pytest.raises(DataValidationError, match="Schema mismatch"):
        validate_superstore_data(broken_csv)


def test_validation_detects_corrupt_rows(tmp_path):
    """Ensures corrupt rows (negative sales, invalid date, ship date before order date) are flagged."""
    test_csv = tmp_path / "test_corrupt.csv"
    valid_row = {col: "A" for col in EXPECTED_COLUMNS}
    valid_row["Row ID"] = 1
    valid_row["Order ID"] = "CA-2016-1"
    valid_row["Order Date"] = "11/8/2016"
    valid_row["Ship Date"] = "11/10/2016"
    valid_row["Sales"] = 100.0
    valid_row["Quantity"] = 2
    valid_row["Discount"] = 0.1
    valid_row["Profit"] = 20.0

    # Corrupt row: Negative sales & ship date before order date
    bad_row = dict(valid_row)
    bad_row["Row ID"] = 2
    bad_row["Sales"] = -50.0  # Invalid
    bad_row["Ship Date"] = "11/1/2016"  # Ship date before order date!

    df = pd.DataFrame([valid_row, bad_row])
    df.to_csv(test_csv, index=False)

    is_valid, summary, valid_df = validate_superstore_data(test_csv)
    assert is_valid is False
    assert summary["rows_checked"] == 2
    assert summary["valid_rows"] == 1
    assert summary["invalid_rows"] == 1
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["Row ID"] == 1
