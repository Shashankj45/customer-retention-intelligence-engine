-- ============================================================================
-- Customer Intelligence, Churn, LTV & Retention Optimization Engine
-- Relational Schema DDL (PostgreSQL & SQLite Compatible ANSI SQL)
-- ============================================================================

-- 1. CUSTOMERS TABLE
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL,
    age INTEGER CHECK (age >= 18 AND age <= 120),
    gender VARCHAR(20),
    signup_date DATE NOT NULL,
    subscription_tier VARCHAR(30) NOT NULL,
    contract_type VARCHAR(30) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    paperless_billing INTEGER DEFAULT 1,
    acquisition_channel VARCHAR(50) NOT NULL,
    preferred_device VARCHAR(30),
    churn_status INTEGER DEFAULT 0 CHECK (churn_status IN (0, 1)),
    churn_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_tier ON customers(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_customers_contract ON customers(contract_type);
CREATE INDEX IF NOT EXISTS idx_customers_churn ON customers(churn_status);
CREATE INDEX IF NOT EXISTS idx_customers_signup ON customers(signup_date);

-- 2. TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    category VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- 3. WEBSITE SESSIONS TABLE
CREATE TABLE IF NOT EXISTS website_sessions (
    session_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    session_date TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds >= 0),
    pages_viewed INTEGER NOT NULL CHECK (pages_viewed >= 1),
    device VARCHAR(30),
    is_bounced INTEGER DEFAULT 0 CHECK (is_bounced IN (0, 1)),
    primary_action VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_customer ON website_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON website_sessions(session_date);

-- 4. SUPPORT TICKETS TABLE
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    created_date TIMESTAMP NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    resolution_time_hours DECIMAL(6, 1) CHECK (resolution_time_hours >= 0),
    csat_score INTEGER CHECK (csat_score BETWEEN 1 AND 5),
    status VARCHAR(30) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tickets_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_date ON support_tickets(created_date);
CREATE INDEX IF NOT EXISTS idx_tickets_csat ON support_tickets(csat_score);

-- 5. PIPELINE EXECUTION LOGS
CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    execution_id VARCHAR(50) PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds DECIMAL(8, 2),
    error_message TEXT
);

-- 6. DATA QUALITY AUDIT TABLE
CREATE TABLE IF NOT EXISTS data_quality_audit (
    audit_id VARCHAR(50) PRIMARY KEY,
    execution_id VARCHAR(50),
    table_name VARCHAR(100) NOT NULL,
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    failed_records_count INTEGER DEFAULT 0,
    check_details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. CHURN PREDICTIONS TABLE
CREATE TABLE IF NOT EXISTS churn_predictions (
    customer_id VARCHAR(20) PRIMARY KEY,
    churn_probability DECIMAL(5, 4) NOT NULL,
    predicted_churn INTEGER NOT NULL CHECK (predicted_churn IN (0, 1)),
    risk_tier VARCHAR(30) NOT NULL,
    top_feature_1 VARCHAR(50),
    top_feature_2 VARCHAR(50),
    top_feature_3 VARCHAR(50),
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 8. CLV PREDICTIONS TABLE
CREATE TABLE IF NOT EXISTS clv_predictions (
    customer_id VARCHAR(20) PRIMARY KEY,
    predicted_clv_12m DECIMAL(10, 2) NOT NULL,
    historical_revenue DECIMAL(10, 2) NOT NULL,
    clv_tier VARCHAR(30) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 9. RETENTION RECOMMENDATIONS TABLE
CREATE TABLE IF NOT EXISTS retention_recommendations (
    recommendation_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    risk_tier VARCHAR(30) NOT NULL,
    recommended_strategy VARCHAR(100) NOT NULL,
    intervention_channel VARCHAR(50) NOT NULL,
    estimated_retention_cost DECIMAL(10, 2) NOT NULL,
    expected_saved_revenue DECIMAL(10, 2) NOT NULL,
    estimated_net_roi DECIMAL(8, 2) NOT NULL,
    priority_rank INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
