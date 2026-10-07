-- ==============================================================================
-- Schema: gold
-- Purpose: Business-ready analytical aggregation tables and KPIs.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Table: gold.daily_sales
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.daily_sales CASCADE;

CREATE TABLE gold.daily_sales (
    order_date DATE PRIMARY KEY,
    total_orders INT NOT NULL,
    total_items_sold INT NOT NULL,
    total_customers INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL
);

INSERT INTO gold.daily_sales (
    order_date,
    total_orders,
    total_items_sold,
    total_customers,
    total_sales,
    total_profit,
    avg_order_value,
    profit_margin
)
SELECT
    f.order_date,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_items_sold,
    COUNT(DISTINCT f.customer_id) AS total_customers,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin
FROM silver.fact_sales f
GROUP BY f.order_date
ORDER BY f.order_date;

-- ------------------------------------------------------------------------------
-- 2. Table: gold.monthly_sales
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.monthly_sales CASCADE;

CREATE TABLE gold.monthly_sales (
    year INT NOT NULL,
    month INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    total_orders INT NOT NULL,
    total_items_sold INT NOT NULL,
    total_customers INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    avg_discount NUMERIC(5, 4) NOT NULL,
    PRIMARY KEY (year, month)
);

INSERT INTO gold.monthly_sales (
    year,
    month,
    year_month,
    total_orders,
    total_items_sold,
    total_customers,
    total_sales,
    total_profit,
    avg_order_value,
    profit_margin,
    avg_discount
)
SELECT
    d.year,
    d.month,
    TO_CHAR(d.full_date, 'YYYY-MM') AS year_month,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_items_sold,
    COUNT(DISTINCT f.customer_id) AS total_customers,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    ROUND(AVG(f.discount), 4) AS avg_discount
FROM silver.fact_sales f
JOIN silver.dim_date d ON f.order_date = d.full_date
GROUP BY d.year, d.month, TO_CHAR(d.full_date, 'YYYY-MM')
ORDER BY d.year, d.month;

-- ------------------------------------------------------------------------------
-- 3. Table: gold.category_performance
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.category_performance CASCADE;

CREATE TABLE gold.category_performance (
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    avg_discount NUMERIC(5, 4) NOT NULL,
    PRIMARY KEY (category, sub_category)
);

INSERT INTO gold.category_performance (
    category,
    sub_category,
    total_orders,
    total_quantity,
    total_sales,
    total_profit,
    profit_margin,
    avg_discount
)
SELECT
    p.category,
    p.sub_category,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    ROUND(AVG(f.discount), 4) AS avg_discount
FROM silver.fact_sales f
JOIN silver.dim_products p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY total_sales DESC;

-- ------------------------------------------------------------------------------
-- 4. Table: gold.product_performance
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.product_performance CASCADE;

CREATE TABLE gold.product_performance (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    order_frequency INT NOT NULL,
    total_units_sold INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    performance_flag VARCHAR(30) NOT NULL
);

INSERT INTO gold.product_performance (
    product_id,
    product_name,
    category,
    sub_category,
    order_frequency,
    total_units_sold,
    total_sales,
    total_profit,
    profit_margin,
    performance_flag
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    COUNT(DISTINCT f.order_id) AS order_frequency,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    CASE 
        WHEN SUM(f.profit) < 0 THEN 'Loss-Maker'
        WHEN SUM(f.sales) >= 5000 AND (SUM(f.profit) / NULLIF(SUM(f.sales), 0)) >= 0.20 THEN 'Star Product'
        WHEN SUM(f.sales) >= 3000 THEN 'High Volume'
        ELSE 'Standard'
    END AS performance_flag
FROM silver.fact_sales f
JOIN silver.dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category
ORDER BY total_sales DESC;

-- ------------------------------------------------------------------------------
-- 5. Table: gold.customer_performance
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.customer_performance CASCADE;

CREATE TABLE gold.customer_performance (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    total_orders INT NOT NULL,
    total_items_purchased INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    avg_order_value NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    first_order_date DATE NOT NULL,
    latest_order_date DATE NOT NULL
);

INSERT INTO gold.customer_performance (
    customer_id,
    customer_name,
    segment,
    total_orders,
    total_items_purchased,
    total_sales,
    total_profit,
    avg_order_value,
    profit_margin,
    first_order_date,
    latest_order_date
)
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_items_purchased,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    MIN(f.order_date) AS first_order_date,
    MAX(f.order_date) AS latest_order_date
FROM silver.fact_sales f
JOIN silver.dim_customers c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment
ORDER BY total_sales DESC;

-- ------------------------------------------------------------------------------
-- 6. Table: gold.regional_performance
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS gold.regional_performance CASCADE;

CREATE TABLE gold.regional_performance (
    region VARCHAR(50) NOT NULL,
    state VARCHAR(100) NOT NULL,
    total_orders INT NOT NULL,
    total_customers INT NOT NULL,
    total_sales NUMERIC(12, 2) NOT NULL,
    total_profit NUMERIC(12, 2) NOT NULL,
    profit_margin NUMERIC(8, 4) NOT NULL,
    avg_days_to_ship NUMERIC(5, 2) NOT NULL,
    PRIMARY KEY (region, state)
);

INSERT INTO gold.regional_performance (
    region,
    state,
    total_orders,
    total_customers,
    total_sales,
    total_profit,
    profit_margin,
    avg_days_to_ship
)
SELECT
    f.region,
    f.state,
    COUNT(DISTINCT f.order_id) AS total_orders,
    COUNT(DISTINCT f.customer_id) AS total_customers,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0), 4) AS profit_margin,
    ROUND(AVG(f.days_to_ship), 2) AS avg_days_to_ship
FROM silver.fact_sales f
GROUP BY f.region, f.state
ORDER BY total_sales DESC;
