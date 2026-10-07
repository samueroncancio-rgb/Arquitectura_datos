-- ==============================================================================
-- Schema: staging
-- Table: staging.superstore
-- Purpose: Standardize columns to snake_case, parse data types, trim strings,
--          and enforce basic format integrity without changing business granularity.
-- ==============================================================================

DROP TABLE IF EXISTS staging.superstore CASCADE;

CREATE TABLE staging.superstore (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE NOT NULL,
    ship_mode VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(150) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    region VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    sales NUMERIC(12, 4) NOT NULL CHECK (sales > 0),
    quantity INT NOT NULL CHECK (quantity > 0),
    discount NUMERIC(5, 4) NOT NULL CHECK (discount >= 0.0 AND discount <= 1.0),
    profit NUMERIC(12, 4) NOT NULL,
    days_to_ship INT NOT NULL CHECK (days_to_ship >= 0)
);

INSERT INTO staging.superstore (
    row_id,
    order_id,
    order_date,
    ship_date,
    ship_mode,
    customer_id,
    customer_name,
    segment,
    country,
    city,
    state,
    postal_code,
    region,
    product_id,
    category,
    sub_category,
    product_name,
    sales,
    quantity,
    discount,
    profit,
    days_to_ship
)
SELECT
    CAST("Row ID" AS INT) AS row_id,
    TRIM("Order ID") AS order_id,
    CASE 
        WHEN "Order Date" LIKE '%/%' THEN TO_DATE(TRIM("Order Date"), 'MM/DD/YYYY')
        ELSE CAST(TRIM("Order Date") AS DATE)
    END AS order_date,
    CASE 
        WHEN "Ship Date" LIKE '%/%' THEN TO_DATE(TRIM("Ship Date"), 'MM/DD/YYYY')
        ELSE CAST(TRIM("Ship Date") AS DATE)
    END AS ship_date,
    TRIM("Ship Mode") AS ship_mode,
    TRIM("Customer ID") AS customer_id,
    TRIM("Customer Name") AS customer_name,
    TRIM("Segment") AS segment,
    TRIM("Country") AS country,
    TRIM("City") AS city,
    TRIM("State") AS state,
    LPAD(TRIM(SPLIT_PART("Postal Code", '.', 1)), 5, '0') AS postal_code,
    TRIM("Region") AS region,
    TRIM("Product ID") AS product_id,
    TRIM("Category") AS category,
    TRIM("Sub-Category") AS sub_category,
    TRIM("Product Name") AS product_name,
    CAST("Sales" AS NUMERIC(12, 4)) AS sales,
    CAST("Quantity" AS INT) AS quantity,
    CAST("Discount" AS NUMERIC(5, 4)) AS discount,
    CAST("Profit" AS NUMERIC(12, 4)) AS profit,
    (
        CASE 
            WHEN "Ship Date" LIKE '%/%' THEN TO_DATE(TRIM("Ship Date"), 'MM/DD/YYYY')
            ELSE CAST(TRIM("Ship Date") AS DATE)
        END
        -
        CASE 
            WHEN "Order Date" LIKE '%/%' THEN TO_DATE(TRIM("Order Date"), 'MM/DD/YYYY')
            ELSE CAST(TRIM("Order Date") AS DATE)
        END
    ) AS days_to_ship
FROM raw.superstore;
