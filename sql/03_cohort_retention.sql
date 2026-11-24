-- ============================================================================
-- 03_cohort_retention.sql
-- Monthly Cohort Acquisition & Retention Rate Engine
-- ============================================================================

DROP VIEW IF EXISTS view_cohort_retention;

CREATE VIEW view_cohort_retention AS
WITH customer_cohorts AS (
    SELECT 
        customer_id,
        SUBSTR(signup_date, 1, 7) AS cohort_month,
        CAST(SUBSTR(signup_date, 1, 4) AS INTEGER) * 12 + CAST(SUBSTR(signup_date, 6, 2) AS INTEGER) AS cohort_month_val
    FROM customers
),
transaction_activities AS (
    SELECT DISTINCT
        t.customer_id,
        SUBSTR(t.transaction_date, 1, 7) AS activity_month,
        CAST(SUBSTR(t.transaction_date, 1, 4) AS INTEGER) * 12 + CAST(SUBSTR(t.transaction_date, 6, 2) AS INTEGER) AS activity_month_val
    FROM transactions t
    WHERE t.status = 'Completed'
),
cohort_activity AS (
    SELECT 
        c.cohort_month,
        (a.activity_month_val - c.cohort_month_val) AS month_index,
        COUNT(DISTINCT c.customer_id) AS active_customers
    FROM customer_cohorts c
    JOIN transaction_activities a ON c.customer_id = a.customer_id
    WHERE (a.activity_month_val - c.cohort_month_val) >= 0 
      AND (a.activity_month_val - c.cohort_month_val) <= 12
    GROUP BY c.cohort_month, (a.activity_month_val - c.cohort_month_val)
),
cohort_sizes AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT 
    ca.cohort_month,
    cs.cohort_size,
    ca.month_index,
    ca.active_customers,
    ROUND(CAST(ca.active_customers AS FLOAT) / CAST(cs.cohort_size AS FLOAT) * 100.0, 2) AS retention_rate_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
ORDER BY ca.cohort_month, ca.month_index;
