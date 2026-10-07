-- ==============================================================================
-- Schema: raw
-- Table: raw.superstore
-- Purpose: Preserves the original file structure as ingested from source
-- ==============================================================================

CREATE TABLE IF NOT EXISTS raw.superstore (
    "Row ID" VARCHAR(50),
    "Order ID" VARCHAR(100),
    "Order Date" VARCHAR(50),
    "Ship Date" VARCHAR(50),
    "Ship Mode" VARCHAR(100),
    "Customer ID" VARCHAR(50),
    "Customer Name" VARCHAR(200),
    "Segment" VARCHAR(100),
    "Country" VARCHAR(100),
    "City" VARCHAR(100),
    "State" VARCHAR(100),
    "Postal Code" VARCHAR(50),
    "Region" VARCHAR(50),
    "Product ID" VARCHAR(100),
    "Category" VARCHAR(100),
    "Sub-Category" VARCHAR(100),
    "Product Name" TEXT,
    "Sales" VARCHAR(50),
    "Quantity" VARCHAR(50),
    "Discount" VARCHAR(50),
    "Profit" VARCHAR(50)
);
