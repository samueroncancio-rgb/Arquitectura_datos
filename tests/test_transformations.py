"""
Unit tests for data transformations and metric calculation formulas.
Verifies business KPI math, discount bounds, and date diff calculations.
"""

import pytest
import pandas as pd
import numpy as np


def test_profit_margin_calculation():
    """Verify profit margin formula: profit / sales."""
    sales = 1000.0
    profit = 250.0
    margin = profit / sales
    assert margin == 0.25

    # Zero sales should handle zero division safely
    zero_sales = 0.0
    safe_margin = (profit / zero_sales) if zero_sales != 0 else 0.0
    assert safe_margin == 0.0


def test_average_order_value_calculation():
    """Verify AOV formula: total_sales / distinct_orders."""
    orders = pd.DataFrame({
        "order_id": ["O-1", "O-1", "O-2", "O-3"],
        "sales": [50.0, 50.0, 200.0, 100.0]
    })
    total_sales = orders["sales"].sum()
    distinct_orders = orders["order_id"].nunique()
    aov = total_sales / distinct_orders

    assert total_sales == 400.0
    assert distinct_orders == 3
    assert round(aov, 2) == 133.33


def test_days_to_ship_calculation():
    """Verify delivery lead time logic (days_to_ship = ship_date - order_date >= 0)."""
    order_dt = pd.to_datetime("2016-11-08")
    ship_dt = pd.to_datetime("2016-11-11")
    days = (ship_dt - order_dt).days

    assert days == 3
    assert days >= 0


def test_unit_price_and_unit_cost():
    """Verify unit economics formulas."""
    sales = 200.0
    profit = 50.0
    quantity = 4

    unit_price = sales / quantity
    unit_cost = (sales - profit) / quantity

    assert unit_price == 50.0
    assert unit_cost == 37.5
    assert (unit_price - unit_cost) * quantity == profit


def test_customer_dimension_deduplication():
    """Verify distinct customers entity derivation."""
    staging_sample = pd.DataFrame({
        "customer_id": ["C1", "C1", "C2"],
        "customer_name": ["Alice", "Alice", "Bob"],
        "segment": ["Consumer", "Consumer", "Corporate"]
    })
    dim_customers = staging_sample.drop_duplicates(subset=["customer_id"])
    assert len(dim_customers) == 2
    assert set(dim_customers["customer_id"]) == {"C1", "C2"}


def test_product_dimension_deduplication_latest():
    """Verify product deduplication resolves to latest record."""
    staging_sample = pd.DataFrame({
        "product_id": ["P1", "P1"],
        "product_name": ["Old Name", "New Name"],
        "category": ["Office", "Office"],
        "sub_category": ["Paper", "Paper"],
        "order_date": pd.to_datetime(["2015-01-01", "2017-01-01"]),
        "row_id": [10, 50]
    })
    sorted_df = staging_sample.sort_values(by=["order_date", "row_id"], ascending=[False, False])
    dim_products = sorted_df.drop_duplicates(subset=["product_id"], keep="first")
    assert len(dim_products) == 1
    assert dim_products.iloc[0]["product_name"] == "New Name"

