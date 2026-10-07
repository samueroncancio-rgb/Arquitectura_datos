-- ==============================================================================
-- Schema: silver
-- Purpose: Cleaned, deduplicated, and normalized dimensional star schema model.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Dimension: dim_date
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS silver.fact_sales CASCADE;
DROP TABLE IF EXISTS silver.dim_date CASCADE;
DROP TABLE IF EXISTS silver.dim_customers CASCADE;
DROP TABLE IF EXISTS silver.dim_products CASCADE;
DROP TABLE IF EXISTS silver.dim_geography CASCADE;

CREATE TABLE silver.dim_date (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

INSERT INTO silver.dim_date (
    date_id,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week,
    day_name,
    is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT AS date_id,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(DAY FROM d)::INT AS day,
    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(
    '2014-01-01'::DATE,
    '2018-01-05'::DATE,
    '1 day'::INTERVAL
) AS d;

-- ------------------------------------------------------------------------------
-- 2. Dimension: dim_customers
-- ------------------------------------------------------------------------------
CREATE TABLE silver.dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    segment VARCHAR(50) NOT NULL
);

INSERT INTO silver.dim_customers (customer_id, customer_name, segment)
SELECT DISTINCT
    customer_id,
    customer_name,
    segment
FROM staging.superstore;

-- ------------------------------------------------------------------------------
-- 3. Dimension: dim_products
-- Resolves minor naming variations by selecting the most recent record per Product ID
-- ------------------------------------------------------------------------------
CREATE TABLE silver.dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(50) NOT NULL
);

INSERT INTO silver.dim_products (product_id, product_name, category, sub_category)
SELECT DISTINCT ON (product_id)
    product_id,
    product_name,
    category,
    sub_category
FROM staging.superstore
ORDER BY product_id, order_date DESC, row_id DESC;

-- ------------------------------------------------------------------------------
-- 4. Dimension: dim_geography
-- ------------------------------------------------------------------------------
CREATE TABLE silver.dim_geography (
    geo_id SERIAL PRIMARY KEY,
    country VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    CONSTRAINT uq_geo_location UNIQUE (country, region, state, city, postal_code)
);

INSERT INTO silver.dim_geography (country, region, state, city, postal_code)
SELECT DISTINCT
    country,
    region,
    state,
    city,
    postal_code
FROM staging.superstore
ORDER BY country, region, state, city, postal_code;

-- ------------------------------------------------------------------------------
-- 5. Fact Table: fact_sales
-- Granularity: 1 row per order line item (Row ID is the unique transaction PK)
-- ------------------------------------------------------------------------------
CREATE TABLE silver.fact_sales (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL REFERENCES silver.dim_date(full_date),
    ship_date DATE NOT NULL REFERENCES silver.dim_date(full_date),
    days_to_ship INT NOT NULL CHECK (days_to_ship >= 0),
    ship_mode VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL REFERENCES silver.dim_customers(customer_id),
    product_id VARCHAR(50) NOT NULL REFERENCES silver.dim_products(product_id),
    country VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    sales NUMERIC(12, 4) NOT NULL CHECK (sales > 0),
    quantity INT NOT NULL CHECK (quantity > 0),
    discount NUMERIC(5, 4) NOT NULL CHECK (discount >= 0.0 AND discount <= 1.0),
    profit NUMERIC(12, 4) NOT NULL,
    unit_price NUMERIC(12, 4) NOT NULL,
    unit_cost NUMERIC(12, 4) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL
);

INSERT INTO silver.fact_sales (
    row_id,
    order_id,
    order_date,
    ship_date,
    days_to_ship,
    ship_mode,
    customer_id,
    product_id,
    country,
    region,
    state,
    city,
    postal_code,
    sales,
    quantity,
    discount,
    profit,
    unit_price,
    unit_cost,
    profit_margin
)
SELECT
    s.row_id,
    s.order_id,
    s.order_date,
    s.ship_date,
    s.days_to_ship,
    s.ship_mode,
    s.customer_id,
    s.product_id,
    s.country,
    s.region,
    s.state,
    s.city,
    s.postal_code,
    s.sales,
    s.quantity,
    s.discount,
    s.profit,
    ROUND(s.sales / s.quantity, 4) AS unit_price,
    ROUND((s.sales - s.profit) / s.quantity, 4) AS unit_cost,
    ROUND(s.profit / NULLIF(s.sales, 0), 4) AS profit_margin
FROM staging.superstore s;

-- Indexes on foreign keys for high query performance
CREATE INDEX idx_fact_sales_order_date ON silver.fact_sales(order_date);
CREATE INDEX idx_fact_sales_customer_id ON silver.fact_sales(customer_id);
CREATE INDEX idx_fact_sales_product_id ON silver.fact_sales(product_id);
CREATE INDEX idx_fact_sales_order_id ON silver.fact_sales(order_id);
