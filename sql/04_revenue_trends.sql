-- ============================================================================
-- 04_revenue_trends.sql
-- Monthly Revenue Trends, ARPU, and Churn Velocity
-- ============================================================================

DROP VIEW IF EXISTS view_revenue_trends;

CREATE VIEW view_revenue_trends AS
WITH monthly_metrics AS (
    SELECT 
        SUBSTR(t.transaction_date, 1, 7) AS revenue_month,
        COUNT(DISTINCT t.customer_id) AS active_paying_customers,
        COUNT(t.transaction_id) AS total_transactions,
        ROUND(SUM(CASE WHEN t.status = 'Completed' THEN t.amount ELSE 0 END), 2) AS gross_revenue,
        ROUND(SUM(CASE WHEN t.status = 'Refunded' THEN t.amount ELSE 0 END), 2) AS refunded_revenue,
        ROUND(SUM(CASE WHEN t.status = 'Completed' THEN t.amount ELSE -t.amount END), 2) AS net_revenue
    FROM transactions t
    GROUP BY SUBSTR(t.transaction_date, 1, 7)
),
lagged_metrics AS (
    SELECT 
        revenue_month,
        active_paying_customers,
        total_transactions,
        gross_revenue,
        refunded_revenue,
        net_revenue,
        ROUND(net_revenue / CAST(active_paying_customers AS FLOAT), 2) AS arpu,
        LAG(net_revenue, 1) OVER (ORDER BY revenue_month) AS prev_month_net_revenue
    FROM monthly_metrics
)
SELECT 
    revenue_month,
    active_paying_customers,
    total_transactions,
    gross_revenue,
    refunded_revenue,
    net_revenue,
    arpu,
    prev_month_net_revenue,
    CASE 
        WHEN prev_month_net_revenue IS NOT NULL AND prev_month_net_revenue > 0 
        THEN ROUND(((net_revenue - prev_month_net_revenue) / prev_month_net_revenue) * 100.0, 2)
        ELSE 0.0 
    END AS mom_growth_pct
FROM lagged_metrics
ORDER BY revenue_month ASC;
