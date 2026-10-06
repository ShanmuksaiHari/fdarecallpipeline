-- Sanity checks for the silver and gold tables.
-- Run in Databricks (SQL Editor) after a pipeline run.


-- 1) Row count and freshness of the silver table
SELECT COUNT(*) AS total_rows,
       MAX(report_date) AS latest_report
FROM silver_recalls;


-- 2) One row per recall: this must return zero rows (the MERGE relies on it)
SELECT recall_number, COUNT(*) AS copies
FROM silver_recalls
GROUP BY recall_number
HAVING COUNT(*) > 1;


-- 3) Recalls with no usable recall_number (the source uses the text 'N/A')
SELECT COUNT(*) AS na_recall_numbers
FROM silver_recalls
WHERE recall_number = 'N/A';


-- 4) Every recall should have a hazard category
SELECT hazard_category, COUNT(*) AS recalls
FROM silver_recalls
GROUP BY hazard_category
ORDER BY recalls DESC;


-- 5) Null dates (a spike here means the date cast in the notebook broke)
SELECT
    SUM(CASE WHEN report_date IS NULL THEN 1 ELSE 0 END) AS null_report_date,
    SUM(CASE WHEN recall_initiation_date IS NULL THEN 1 ELSE 0 END) AS null_initiation_date
FROM silver_recalls;


-- 6) Disclosure lag should be plausible: how long a recall took to be reported
SELECT MIN(lag_days) AS min_lag,
       AVG(lag_days) AS avg_lag,
       MAX(lag_days) AS max_lag,
       COUNT(*) AS rows_in_table
FROM disclosure_lag;


-- 7) Longest lags first: look here for bad source dates
SELECT recall_number, recalling_firm, recall_initiation_date, report_date, lag_days
FROM disclosure_lag
ORDER BY lag_days DESC
LIMIT 5;
