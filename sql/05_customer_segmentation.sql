-- ============================================================================
-- 05_customer_segmentation.sql
-- Multi-Dimensional Behavioral & Value Customer Segmentation
-- ============================================================================

DROP VIEW IF EXISTS view_customer_segmentation;

CREATE VIEW view_customer_segmentation AS
WITH customer_behavior AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.country,
        c.subscription_tier,
        c.contract_type,
        c.payment_method,
        c.acquisition_channel,
        c.churn_status,
        -- Total spend
        COALESCE(SUM(CASE WHEN t.status = 'Completed' THEN t.amount ELSE 0 END), 0.0) AS total_spend,
        -- Average session length & pageviews
        COALESCE(AVG(s.duration_seconds), 0) AS avg_session_duration,
        COALESCE(AVG(s.pages_viewed), 0) AS avg_pages_viewed,
        COALESCE(SUM(s.is_bounced), 0) AS total_bounced_sessions,
        -- Total tickets and avg csat
        COALESCE(COUNT(DISTINCT tk.ticket_id), 0) AS support_tickets_count,
        COALESCE(AVG(tk.csat_score), 4.0) AS avg_csat_score
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    LEFT JOIN website_sessions s ON c.customer_id = s.customer_id
    LEFT JOIN support_tickets tk ON c.customer_id = tk.customer_id
    GROUP BY c.customer_id, c.customer_name, c.country, c.subscription_tier, c.contract_type, c.payment_method, c.acquisition_channel, c.churn_status
)
SELECT 
    customer_id,
    customer_name,
    country,
    subscription_tier,
    contract_type,
    payment_method,
    acquisition_channel,
    churn_status,
    ROUND(total_spend, 2) AS total_spend,
    ROUND(avg_session_duration, 1) AS avg_session_duration,
    ROUND(avg_pages_viewed, 1) AS avg_pages_viewed,
    total_bounced_sessions,
    support_tickets_count,
    ROUND(avg_csat_score, 2) AS avg_csat_score,
    -- Behavioral Value Tier
    CASE 
        WHEN total_spend >= 2500 THEN 'Tier 1: Enterprise VIP'
        WHEN total_spend >= 1000 THEN 'Tier 2: High Value'
        WHEN total_spend >= 300 THEN 'Tier 3: Mid Value'
        ELSE 'Tier 4: Standard / Low Value'
    END AS value_segment,
    -- Health Segment
    CASE 
        WHEN churn_status = 1 THEN 'Churned'
        WHEN support_tickets_count >= 3 AND avg_csat_score < 3.0 THEN 'Distressed / High Friction'
        WHEN avg_session_duration < 60 THEN 'Disengaged'
        WHEN total_spend >= 1000 AND avg_csat_score >= 4.0 THEN 'Advocate / High Health'
        ELSE 'Healthy Standard'
    END AS customer_health_segment
FROM customer_behavior;
