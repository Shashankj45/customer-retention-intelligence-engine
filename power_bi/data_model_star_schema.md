# Power BI Dimensional Data Model (Star Schema)

This document specifies the enterprise Star Schema data model designed for Microsoft Power BI reporting.

```
                               ┌──────────────────────────┐
                               │         Dim_Date         │
                               ├──────────────────────────┤
                               │ date_key (PK)            │
                               │ full_date                │
                               │ year                     │
                               │ quarter                  │
                               │ month_num                │
                               │ month_name               │
                               │ year_month               │
                               └────────────┬─────────────┘
                                            │ 1
                                            │
                                            │ *
                    ┌───────────────────────┼───────────────────────┐
                    │ *                     │ *                     │ *
        ┌───────────▼───────────┐ ┌─────────▼─────────┐ ┌───────────▼───────────┐
        │   Fact_Transactions   │ │Fact_WebsiteSession│ │  Fact_SupportTickets  │
        ├───────────────────────┤ ├───────────────────┤ ├───────────────────────┤
        │ transaction_id (PK)   │ │ session_id (PK)   │ │ ticket_id (PK)        │
        │ customer_id (FK)      │ │ customer_id (FK)  │ │ customer_id (FK)      │
        │ date_key (FK)         │ │ date_key (FK)     │ │ date_key (FK)         │
        │ amount                │ │ duration_seconds  │ │ priority              │
        │ category              │ │ pages_viewed      │ │ resolution_time_hours │
        │ status                │ │ is_bounced        │ │ csat_score            │
        │ payment_method        │ │ primary_action    │ │ status                │
        └───────────▲───────────┘ └─────────▲─────────┘ └───────────▲───────────┘
                    │ *                     │ *                     │ *
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                                            │ 1
                               ┌────────────┴─────────────┐
                               │       Dim_Customer       │
                               ├──────────────────────────┤
                               │ customer_id (PK)         │
                               │ customer_name            │
                               │ email                    │
                               │ country                  │
                               │ age, gender              │
                               │ subscription_tier        │
                               │ contract_type            │
                               │ churn_status             │
                               └────────────┬─────────────┘
                                            │ 1
                         ┌──────────────────┼──────────────────┐
                         │ 1:1              │ 1:1              │ 1:1
              ┌──────────▼──────────┐┌──────▼─────────┐┌───────▼──────────┐
              │ Dim_ChurnPrediction ││Dim_CLVPredictio││Dim_RetentionRec  │
              ├─────────────────────┤├────────────────┤├──────────────────┤
              │ customer_id (PK/FK) ││customer_id(PK) ││customer_id (PK)  │
              │ churn_probability   ││predicted_clv   ││recommended_action│
              │ risk_tier           ││clv_tier        ││expected_savings  │
              │ top_feature_1       ││historical_spend││net_roi           │
              └─────────────────────┘└────────────────┘└──────────────────┘
```

---

## Table Specifications & Cardinalities

### 1. Dimension Tables (Conformed)
- **Dim_Customer**: One row per customer (`customer_id` is Primary Key). Holds demographic and subscription attributes.
- **Dim_Date**: Calendar dimension with contiguous daily dates, fiscal quarters, month numbers, and weekday flags.
- **Dim_ChurnPredictions**: 1-to-1 extension containing model inference, churn probability, risk tier, and primary SHAP risk factors.
- **Dim_CLVPredictions**: 1-to-1 extension containing historical revenue, 12-month forward predicted CLV, and value tier.
- **Dim_RFMSegments**: 1-to-1 extension containing R, F, M percentile scores and segment names.
- **Dim_RetentionRecommendations**: 1-to-1 extension containing prescribed retention strategies, intervention channels, and estimated net ROI.

### 2. Fact Tables (Transactional & Behavioral)
- **Fact_Transactions**: Granular ledger of all payment transactions, amounts, status (Completed, Refunded, Failed), and payment methods.
  - Foreign Keys: `customer_id` -> `Dim_Customer[customer_id]`, `date_key` -> `Dim_Date[date_key]`.
- **Fact_WebsiteSessions**: Web telemetry events, session duration, pageviews, bounce flag, and primary actions.
  - Foreign Keys: `customer_id` -> `Dim_Customer[customer_id]`, `date_key` -> `Dim_Date[date_key]`.
- **Fact_SupportTickets**: Customer service inquiries, CSAT ratings, priority levels, and resolution times.
  - Foreign Keys: `customer_id` -> `Dim_Customer[customer_id]`, `date_key` -> `Dim_Date[date_key]`.

---

## Power BI Relationship Settings

| From Table | From Column | To Table | To Column | Cardinality | Cross-Filter Direction | Active |
|---|---|---|---|---|---|---|
| `Fact_Transactions` | `customer_id` | `Dim_Customer` | `customer_id` | Many to One (*:1) | Single | Yes |
| `Fact_Transactions` | `date_key` | `Dim_Date` | `date_key` | Many to One (*:1) | Single | Yes |
| `Fact_WebsiteSessions` | `customer_id` | `Dim_Customer` | `customer_id` | Many to One (*:1) | Single | Yes |
| `Fact_WebsiteSessions` | `date_key` | `Dim_Date` | `date_key` | Many to One (*:1) | Single | Yes |
| `Fact_SupportTickets` | `customer_id` | `Dim_Customer` | `customer_id` | Many to One (*:1) | Single | Yes |
| `Fact_SupportTickets` | `date_key` | `Dim_Date` | `date_key` | Many to One (*:1) | Single | Yes |
| `Dim_ChurnPredictions` | `customer_id` | `Dim_Customer` | `customer_id` | One to One (1:1) | Both | Yes |
| `Dim_CLVPredictions` | `customer_id` | `Dim_Customer` | `customer_id` | One to One (1:1) | Both | Yes |
| `Dim_RFMSegments` | `customer_id` | `Dim_Customer` | `customer_id` | One to One (1:1) | Both | Yes |
| `Dim_RetentionRecommendations` | `customer_id` | `Dim_Customer` | `customer_id` | One to One (1:1) | Both | Yes |
