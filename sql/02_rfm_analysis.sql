-- ============================================================================
-- 02_rfm_analysis.sql
-- Recency, Frequency, Monetary (RFM) Segmentation Engine
-- ============================================================================

DROP VIEW IF EXISTS view_rfm_analysis;

CREATE VIEW view_rfm_analysis AS
WITH customer_aggregates AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.subscription_tier,
        c.churn_status,
        -- Recency: Days since last completed transaction relative to reference date '2026-11-01'
        CAST((JULIANDAY('2026-11-01') - JULIANDAY(MAX(t.transaction_date))) AS INTEGER) AS recency_days,
        -- Frequency: Count of completed transactions
        COUNT(CASE WHEN t.status = 'Completed' THEN t.transaction_id END) AS frequency,
        -- Monetary: Sum of completed transaction amounts
        COALESCE(SUM(CASE WHEN t.status = 'Completed' THEN t.amount ELSE 0 END), 0.0) AS monetary
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.customer_name, c.subscription_tier, c.churn_status
),
rfm_scores AS (
    SELECT 
        customer_id,
        customer_name,
        subscription_tier,
        churn_status,
        COALESCE(recency_days, 999) AS recency_days,
        frequency,
        monetary,
        -- Recency Score: lower days = higher score (5 is best)
        NTILE(5) OVER (ORDER BY COALESCE(recency_days, 999) DESC) AS r_score,
        -- Frequency Score: higher frequency = higher score (5 is best)
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        -- Monetary Score: higher spend = higher score (5 is best)
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM customer_aggregates
)
SELECT 
    customer_id,
    customer_name,
    subscription_tier,
    churn_status,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score * 100 + f_score * 10 + m_score) AS rfm_combined_score,
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Potential Loyalists'
        WHEN r_score = 5 AND f_score = 1 THEN 'Recent Customers'
        WHEN r_score >= 3 AND f_score <= 2 THEN 'Promising'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
        WHEN r_score = 1 AND f_score >= 4 AND m_score >= 4 THEN 'Can''t Lose Them'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 2 THEN 'Hibernating'
        ELSE 'Lost Customers'
    END AS rfm_segment
FROM rfm_scores;
