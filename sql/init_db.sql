-- ==============================================================================
-- Superstore Data Pipeline - Database Initialization
-- ==============================================================================

-- Create separate layers according to Data Architecture:
-- raw     -> Raw source-aligned tables
-- staging -> Cleaned, standardized snake_case & typed data
-- silver  -> Normalized dimensional star schema (dim_*, fact_*)
-- gold    -> Business-ready analytics & KPI aggregation tables

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
