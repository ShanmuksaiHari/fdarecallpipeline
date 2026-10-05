-- Gold layer: aggregate tables built from the silver_recalls Delta table.
-- These run inside Databricks (the notebook wraps each one in spark.sql(...)).
-- Grafana reads these six tables for the dashboard panels.


-- 1) Recalls per year and FDA classification (line chart)
CREATE OR REPLACE TABLE recalls_by_year_class AS
SELECT
    YEAR(report_date) AS year,
    classification,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE report_date IS NOT NULL
GROUP BY YEAR(report_date), classification
ORDER BY year, classification;


-- 2) Recalls per state (map)
CREATE OR REPLACE TABLE recalls_by_state AS
SELECT
    state,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE state IS NOT NULL
GROUP BY state
ORDER BY recall_count DESC;


-- 3) Top 20 recalling firms (bar list)
CREATE OR REPLACE TABLE recalls_by_firm AS
SELECT
    recalling_firm,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE recalling_firm IS NOT NULL
GROUP BY recalling_firm
ORDER BY recall_count DESC
LIMIT 20;


-- 4) Recalls per year and hazard category (donut chart)
CREATE OR REPLACE TABLE recalls_by_hazard AS
SELECT
    YEAR(report_date) AS year,
    hazard_category,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE report_date IS NOT NULL
GROUP BY YEAR(report_date), hazard_category
ORDER BY year, hazard_category;


-- 5) Days between a recall starting and the FDA publishing it (stat panel)
-- The date filter drops rows with malformed initiation dates found in the
-- source data (dates far outside the valid range).
CREATE OR REPLACE TABLE disclosure_lag AS
SELECT
    recall_number,
    recalling_firm,
    classification,
    recall_initiation_date,
    report_date,
    DATEDIFF(report_date, recall_initiation_date) AS lag_days
FROM silver_recalls
WHERE recall_initiation_date IS NOT NULL
  AND report_date IS NOT NULL
  AND recall_initiation_date >= '2004-01-01'
  AND recall_initiation_date <= CURRENT_DATE();


-- 6) 25 most recent Class I (most severe) recalls (table panel)
CREATE OR REPLACE TABLE latest_class_one AS
SELECT
    recall_number,
    recalling_firm,
    state,
    product_description,
    reason_for_recall,
    hazard_category,
    report_date,
    status
FROM silver_recalls
WHERE classification = 'Class I'
ORDER BY report_date DESC
LIMIT 25;
