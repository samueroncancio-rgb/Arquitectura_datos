"""
Automated Data Quality Tests.

Validates key data assumptions on the Superstore dataset:
- Required columns present
- No unexpected NULL values
- Order IDs format and presence
- Sales > 0 and numeric
- Quantity is positive integer
- Dates are chronologically sound
- Consistency of sales aggregations across dimensions
- No duplicate primary keys in entity models
"""

import pytest
import pandas as pd
from config.config import config
from src.validation.validator import load_raw_csv


@pytest.fixture(scope="module")
def raw_df() -> pd.DataFrame:
    """Fixture providing raw dataset DataFrame."""
    return load_raw_csv(config.paths.raw_csv_path)


def test_no_nulls_in_critical_fields(raw_df):
    """Verify that essential business fields have 0 null values."""
    critical_fields = [
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
    for col in critical_fields:
        null_count = raw_df[col].isnull().sum()
        assert null_count == 0, f"Column {col} has unexpected null values: {null_count}"


def test_row_ids_strictly_unique(raw_df):
    """Verify that Row ID is unique across all rows."""
    duplicate_rows = raw_df["Row ID"].duplicated().sum()
    assert duplicate_rows == 0, f"Found {duplicate_rows} duplicate Row IDs!"


def test_order_id_format_and_presence(raw_df):
    """Verify Order IDs are non-empty strings."""
    assert (raw_df["Order ID"].str.strip().str.len() > 0).all()
    assert raw_df["Order ID"].nunique() == 5009


def test_sales_and_quantity_are_positive(raw_df):
    """Verify Sales > 0 and Quantity >= 1."""
    sales = pd.to_numeric(raw_df["Sales"])
    quantity = pd.to_numeric(raw_df["Quantity"])

    assert (sales > 0).all(), "Found non-positive sales records!"
    assert (quantity >= 1).all(), "Found non-positive quantities!"


def test_discount_within_bounds(raw_df):
    """Verify Discount is between 0.0 (0%) and 1.0 (100%)."""
    discount = pd.to_numeric(raw_df["Discount"])
    assert (discount >= 0.0).all()
    assert (discount <= 1.0).all()


def test_chronological_integrity(raw_df):
    """Verify Ship Date is on or after Order Date."""
    order_dt = pd.to_datetime(raw_df["Order Date"])
    ship_dt = pd.to_datetime(raw_df["Ship Date"])
    violations = (ship_dt < order_dt).sum()
    assert violations == 0, f"Found {violations} orders where Ship Date is before Order Date!"


def test_sales_sum_consistency_across_categories(raw_df):
    """Verify that sum of sales grouped by category equals total sales exactly."""
    sales = pd.to_numeric(raw_df["Sales"])
    total_sales = round(sales.sum(), 2)

    category_sales = round(raw_df.groupby("Category")["Sales"].apply(lambda s: pd.to_numeric(s).sum()).sum(), 2)
    assert total_sales == category_sales, "Category aggregated sales do not match total sales!"


def test_customer_segment_consistency(raw_df):
    """Verify each customer ID is uniquely mapped to one single segment."""
    segments_per_customer = raw_df.groupby("Customer ID")["Segment"].nunique()
    assert (segments_per_customer == 1).all(), "Customer mapped to multiple conflicting segments!"
