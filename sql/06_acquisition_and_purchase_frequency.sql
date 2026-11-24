-- ============================================================================
-- 06_acquisition_and_purchase_frequency.sql
-- Acquisition Performance & Purchase Velocity Analytics
-- ============================================================================

DROP VIEW IF EXISTS view_acquisition_metrics;
DROP VIEW IF EXISTS view_purchase_frequency;

CREATE VIEW view_acquisition_metrics AS
WITH channel_stats AS (
    SELECT 
        c.acquisition_channel,
        COUNT(c.customer_id) AS acquired_customers,
        SUM(c.churn_status) AS churned_customers,
        ROUND(AVG(CASE WHEN c.churn_status = 1 THEN 1.0 ELSE 0.0 END) * 100.0, 2) AS channel_churn_rate_pct,
        ROUND(SUM(CASE WHEN t.status = 'Completed' THEN t.amount ELSE 0 END), 2) AS total_revenue_generated,
        ROUND(AVG(c.age), 1) AS avg_customer_age
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.acquisition_channel
)
SELECT 
    acquisition_channel,
    acquired_customers,
    churned_customers,
    (acquired_customers - churned_customers) AS active_retained_customers,
    channel_churn_rate_pct,
    total_revenue_generated,
    ROUND(total_revenue_generated / CAST(acquired_customers AS FLOAT), 2) AS revenue_per_acquired_customer,
    -- Benchmark CAC per channel
    CASE 
        WHEN acquisition_channel = 'Organic Search' THEN 18.00
        WHEN acquisition_channel = 'Paid Ads' THEN 95.00
        WHEN acquisition_channel = 'Email Marketing' THEN 22.00
        WHEN acquisition_channel = 'Referral' THEN 28.00
        WHEN acquisition_channel = 'Social Media' THEN 48.00
        ELSE 12.00
    END AS estimated_cac,
    -- LTV / CAC Ratio
    ROUND((total_revenue_generated / CAST(acquired_customers AS FLOAT)) / 
          (CASE 
              WHEN acquisition_channel = 'Organic Search' THEN 18.00
              WHEN acquisition_channel = 'Paid Ads' THEN 95.00
              WHEN acquisition_channel = 'Email Marketing' THEN 22.00
              WHEN acquisition_channel = 'Referral' THEN 28.00
              WHEN acquisition_channel = 'Social Media' THEN 48.00
              ELSE 12.00
          END), 2) AS ltv_to_cac_ratio
FROM channel_stats;

CREATE VIEW view_purchase_frequency AS
WITH customer_orders AS (
    SELECT 
        customer_id,
        COUNT(transaction_id) AS total_orders,
        SUM(CASE WHEN status = 'Completed' THEN amount ELSE 0 END) AS total_completed_spend,
        SUM(CASE WHEN status = 'Refunded' THEN 1 ELSE 0 END) AS refund_count,
        ROUND(AVG(CASE WHEN status = 'Completed' THEN amount END), 2) AS avg_order_value,
        MIN(transaction_date) AS first_order_date,
        MAX(transaction_date) AS last_order_date
    FROM transactions
    GROUP BY customer_id
)
SELECT 
    c.subscription_tier,
    COUNT(co.customer_id) AS customers_count,
    ROUND(AVG(co.total_orders), 1) AS avg_orders_per_customer,
    ROUND(AVG(co.avg_order_value), 2) AS average_order_value,
    ROUND(AVG(co.total_completed_spend), 2) AS avg_spend_per_customer,
    ROUND(AVG(CAST(co.refund_count AS FLOAT) / CASE WHEN co.total_orders > 0 THEN co.total_orders ELSE 1 END) * 100.0, 2) AS avg_refund_rate_pct
FROM customers c
JOIN customer_orders co ON c.customer_id = co.customer_id
GROUP BY c.subscription_tier;
