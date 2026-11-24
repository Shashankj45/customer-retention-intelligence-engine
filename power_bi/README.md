# Power BI Implementation Guide

## Customer Intelligence, Churn, LTV & Retention Optimization Engine

> **⚠️ Governance & Data Origin Notice**:
> - **Synthetic Telemetry**: The underlying relational dataset (5,000 customers, 51,653 transactions, 572,806 website sessions, 3,691 support tickets — totaling 633,150 records) is synthetically generated for portfolio benchmarking.
> - **Simulation Modeling**: Retention ROI measures (e.g., `[Simulated Net Retention Benefit $]`) reflect what-if scenario simulations calculated using prescriptive decision logic and empirical response elasticities, not historical audited accounting.

This guide walks you through importing the dimensional data model and DAX measures into **Microsoft Power BI Desktop**.

---

## 1. Quick Data Ingestion (1-Click)

The pipeline automatically exports pre-structured dimensional tables to:
`data/power_bi_exports/`

Available tables:
1. `Dim_Customer.csv`
2. `Dim_Date.csv`
3. `Dim_ChurnPredictions.csv`
4. `Dim_CLVPredictions.csv`
5. `Dim_RFMSegments.csv`
6. `Dim_RetentionRecommendations.csv`
7. `Fact_Transactions.csv`
8. `Fact_WebsiteSessions.csv`
9. `Fact_SupportTickets.csv`

To refresh or regenerate these export files at any time, run:
```bash
python -m power_bi.export_data
```

---

## 2. Setting Up Power BI Desktop

1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV** (or **Folder** to import all at once from `data/power_bi_exports`).
3. Select all 9 CSV files and click **Load**.
4. In the **Model View** (left navigation bar), set up the relationships as specified in `power_bi/data_model_star_schema.md`:
   - Connect `Dim_Customer[customer_id]` to:
     * `Fact_Transactions[customer_id]` (1 to Many)
     * `Fact_WebsiteSessions[customer_id]` (1 to Many)
     * `Fact_SupportTickets[customer_id]` (1 to Many)
     * `Dim_ChurnPredictions[customer_id]` (1 to 1)
     * `Dim_CLVPredictions[customer_id]` (1 to 1)
     * `Dim_RFMSegments[customer_id]` (1 to 1)
     * `Dim_RetentionRecommendations[customer_id]` (1 to 1)
   - Connect `Dim_Date[date_key]` to:
     * `Fact_Transactions[date_key]` (1 to Many)
     * `Fact_WebsiteSessions[date_key]` (1 to Many)
     * `Fact_SupportTickets[date_key]` (1 to Many)

---

## 3. Creating DAX Measures

1. Create a dedicated measure table: Home > **Enter Data** > Name it `_DAX Measures` > Load.
2. Open `power_bi/dax_measures.txt`.
3. Copy and paste each DAX formula into Power BI (**New Measure**).
4. Recommended core measures to add first:
   - `[Total Gross Revenue]`
   - `[Net Revenue]`
   - `[Customer Churn Rate %]`
   - `[Critical Risk Customers]`
   - `[Total Projected 12M CLV]`
   - `[Total Potential Saved Revenue]`
   - `[Net Retention Benefit $]`

---

## 4. Recommended Report Pages & Visuals

### Page 1: Executive Dashboard
- **KPI Cards**: `[Net Revenue]`, `[Customer Count]`, `[Customer Churn Rate %]`, `[ARPU]`
- **Line & Clustered Column Chart**: Monthly Net Revenue & MoM Growth % by `Dim_Date[year_month]`
- **Matrix / Heatmap**: Cohort Retention % by `Cohort Month` vs `Month Index`
- **Donut Chart**: Churn % by `Dim_Customer[subscription_tier]`

### Page 2: Churn & ML Risk Intelligence
- **Card**: `[Critical Risk Customers]`, `[Revenue at Immediate Risk]`
- **Donut Chart**: Customer share by `Dim_ChurnPredictions[risk_tier]`
- **Scatter Chart**: Churn Probability vs Historical Spend by Customer
- **Table Visual**: Watchlist of Critical/High-Risk customers with customer name, probability, top risk driver, and contract type.

### Page 3: Customer Lifetime Value (CLV) & Pareto
- **Card**: `[Total Projected 12M CLV]`, `[Average Predicted CLV]`
- **Line Chart**: Cumulative % of CLV vs Cumulative % of Customers (Pareto curve)
- **Bar Chart**: Total 12M CLV by `Dim_CLVPredictions[clv_tier]`
- **Treemap**: Revenue concentration by `Dim_Customer[country]` and `subscription_tier`

### Page 4: Retention Strategy & ROI Simulator
- **Card**: `[Total Potential Saved Revenue]`, `[Net Retention Benefit $]`, `[Retention ROI Multiplier %]`
- **Waterfall Chart**: Gross Saved Revenue -> Campaign Operations -> Discount Cost -> Net Profit Benefit
- **Bar Chart**: Recommended Strategy count by `Dim_RetentionRecommendations[recommended_strategy]`
- **Table Visual**: Prioritized outreach list sorted by `priority_rank` ascending.
