"""
Synthetic Data Generator for Customer Intelligence Platform.
Generates realistic, interconnected relational datasets:
- Customers (Demographics, Subscriptions, Contracts, Churn Ground Truth)
- Transactions (Financial history, amounts, categories, refunds)
- Website Sessions (Behavioral telemetry, duration, pageviews, bounce)
- Support Tickets (Customer service inquiries, resolution times, CSAT)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
from src.config import RANDOM_SEED, DEFAULT_NUM_CUSTOMERS, RAW_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("data_generator")

class CustomerDataGenerator:
    """Generates interconnected synthetic business datasets with authentic behavioral patterns."""

    def __init__(self, num_customers: int = DEFAULT_NUM_CUSTOMERS, seed: int = RANDOM_SEED):
        self.num_customers = num_customers
        self.seed = seed
        np.random.seed(seed)
        self.reference_date = datetime(2026, 11, 1)

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """Generates all 4 interconnected datasets and saves them to raw directory."""
        logger.info(f"Generating datasets for {self.num_customers} customers...")
        
        customers_df = self._generate_customers()
        transactions_df = self._generate_transactions(customers_df)
        sessions_df = self._generate_sessions(customers_df)
        tickets_df = self._generate_tickets(customers_df)

        datasets = {
            "customers": customers_df,
            "transactions": transactions_df,
            "website_sessions": sessions_df,
            "support_tickets": tickets_df
        }

        # Save to raw data folder
        for name, df in datasets.items():
            csv_path = RAW_DATA_DIR / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {name} dataset ({len(df):,} rows) -> {csv_path}")

        return datasets

    def _generate_customers(self) -> pd.DataFrame:
        """Generates demographic, subscription, and churn ground truth."""
        n = self.num_customers

        # IDs
        customer_ids = [f"CUST-{i+1:05d}" for i in range(n)]

        # Signup dates: uniformly distributed over past 24 months
        max_tenure_days = 730
        signup_deltas = np.random.randint(30, max_tenure_days, size=n)
        signup_dates = [self.reference_date - timedelta(days=int(d)) for d in signup_deltas]

        # First & Last Names pools
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Avery",
                       "Daniel", "Sophia", "Ethan", "Olivia", "Liam", "Emma", "Noah", "Ava", "Lucas", "Mia"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                      "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore"]
        
        names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(n)]
        emails = [f"{names[i].lower().replace(' ', '.')}.{i+1:05d}@example.com" for i in range(n)]

        # Demographics
        countries = np.random.choice(
            ["United States", "United Kingdom", "Germany", "Canada", "Australia", "India", "France"],
            size=n,
            p=[0.40, 0.15, 0.12, 0.10, 0.08, 0.08, 0.07]
        )
        ages = np.random.normal(38, 11, size=n).astype(int)
        ages = np.clip(ages, 18, 75)
        genders = np.random.choice(["Male", "Female", "Non-Binary"], size=n, p=[0.48, 0.48, 0.04])

        # Subscription & Contracts
        tiers = np.random.choice(
            ["Free", "Bronze", "Silver", "Gold", "Enterprise"],
            size=n,
            p=[0.25, 0.30, 0.25, 0.15, 0.05]
        )
        contracts = np.random.choice(
            ["Month-to-Month", "One-Year", "Two-Year"],
            size=n,
            p=[0.55, 0.30, 0.15]
        )
        payment_methods = np.random.choice(
            ["Credit Card", "Bank Transfer", "PayPal", "Electronic Check"],
            size=n,
            p=[0.45, 0.25, 0.20, 0.10]
        )
        paperless = np.random.choice([1, 0], size=n, p=[0.75, 0.25])
        channels = np.random.choice(
            ["Organic Search", "Paid Ads", "Email Marketing", "Referral", "Social Media", "Direct"],
            size=n,
            p=[0.28, 0.22, 0.18, 0.14, 0.10, 0.08]
        )
        devices = np.random.choice(["Desktop", "Mobile", "Tablet"], size=n, p=[0.55, 0.35, 0.10])

        # Calculate realistic latent churn propensity with unobserved real-world variance
        # In reality, churn is driven by both observable friction AND unobserved external events
        # (competitor offers, company budget cuts, champion user departure, etc.)
        churn_logits = (
            -0.8
            + (contracts == "Month-to-Month") * 0.65
            - (contracts == "Two-Year") * 0.75
            + (payment_methods == "Electronic Check") * 0.30
            - (tiers == "Enterprise") * 0.55
            - (tiers == "Gold") * 0.35
            + (tiers == "Free") * 0.35
            + (channels == "Paid Ads") * 0.20
            - (channels == "Referral") * 0.30
            + np.random.normal(0, 1.15, size=n)  # Substantial stochastic/unobserved variance
        )
        churn_probs = 1.0 / (1.0 + np.exp(-churn_logits))
        churn_labels = (np.random.uniform(0, 1, size=n) < churn_probs).astype(int)

        # Churn date: if churned, occurs between signup + 30 days and reference date
        churn_dates = []
        for i in range(n):
            if churn_labels[i] == 1:
                signup = signup_dates[i]
                remaining_days = max(15, (self.reference_date - signup).days)
                churn_delta = np.random.randint(15, remaining_days + 1)
                churn_dates.append((signup + timedelta(days=int(churn_delta))).strftime("%Y-%m-%d"))
            else:
                churn_dates.append(None)

        df = pd.DataFrame({
            "customer_id": customer_ids,
            "customer_name": names,
            "email": emails,
            "country": countries,
            "age": ages,
            "gender": genders,
            "signup_date": [d.strftime("%Y-%m-%d") for d in signup_dates],
            "subscription_tier": tiers,
            "contract_type": contracts,
            "payment_method": payment_methods,
            "paperless_billing": paperless,
            "acquisition_channel": channels,
            "preferred_device": devices,
            "churn_status": churn_labels,
            "churn_date": churn_dates
        })
        return df

    def _generate_transactions(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generates realistic transaction history consistent with subscription tiers and churn dates."""
        tx_records = []
        tx_counter = 1

        tier_price_map = {
            "Free": (5.0, 20.0),
            "Bronze": (29.0, 49.0),
            "Silver": (79.0, 149.0),
            "Gold": (199.0, 399.0),
            "Enterprise": (799.0, 1999.0)
        }

        for _, cust in customers_df.iterrows():
            cid = cust["customer_id"]
            tier = cust["subscription_tier"]
            is_churn = cust["churn_status"]
            signup = datetime.strptime(cust["signup_date"], "%Y-%m-%d")
            end_date = datetime.strptime(cust["churn_date"], "%Y-%m-%d") if is_churn else self.reference_date
            tenure_months = max(1, int((end_date - signup).days / 30))

            # Number of transactions depends on tenure and personal baseline activity with broad variance
            base_lam = np.random.uniform(0.6, 1.4)
            churn_activity_adj = np.random.uniform(0.75, 1.10) if is_churn else np.random.uniform(0.90, 1.25)
            num_txs = max(1, np.random.poisson(lam=max(1, tenure_months * base_lam * churn_activity_adj)))

            # Distribute transaction dates between signup and end_date
            total_days = max(1, (end_date - signup).days)
            deltas = np.sort(np.random.randint(0, total_days, size=num_txs))

            min_p, max_p = tier_price_map[tier]

            for d in deltas:
                tx_date = signup + timedelta(days=int(d))
                amount = round(float(np.random.uniform(min_p, max_p)), 2)
                
                # Categories
                cat_choices = ["Subscription", "Add-on", "Upgrade", "Usage Overage", "Professional Service"]
                cat_p = [0.65, 0.15, 0.10, 0.07, 0.03]
                category = np.random.choice(cat_choices, p=cat_p)

                # Status: small chance of refund or failure with natural overlap
                refund_p = 0.05 if is_churn else 0.02
                failed_p = 0.04 if is_churn else 0.01
                status_roll = np.random.uniform(0, 1)
                if status_roll < refund_p:
                    status = "Refunded"
                elif status_roll < refund_p + failed_p:
                    status = "Failed"
                else:
                    status = "Completed"

                tx_records.append({
                    "transaction_id": f"TXN-{tx_counter:07d}",
                    "customer_id": cid,
                    "transaction_date": tx_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": amount,
                    "category": category,
                    "status": status,
                    "payment_method": cust["payment_method"]
                })
                tx_counter += 1

        return pd.DataFrame(tx_records)

    def _generate_sessions(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generates web session telemetry (inactivity patterns predict churn)."""
        session_records = []
        sess_counter = 1

        for _, cust in customers_df.iterrows():
            cid = cust["customer_id"]
            is_churn = cust["churn_status"]
            signup = datetime.strptime(cust["signup_date"], "%Y-%m-%d")
            end_date = datetime.strptime(cust["churn_date"], "%Y-%m-%d") if is_churn else self.reference_date
            total_days = max(1, (end_date - signup).days)

            # Frequency: broad continuous customer-level variance with natural overlap
            base_rate = np.random.uniform(5, 18)
            churn_effect = np.random.normal(-1.5, 3.0) if is_churn else np.random.normal(0.0, 3.0)
            sessions_per_month = max(2.5, base_rate + churn_effect)
            num_sessions = max(2, int((total_days / 30.0) * sessions_per_month))

            # Inactivity distribution with natural overlap:
            # Many active customers have long gaps (casual users), and many churners visit right before cancellation
            if is_churn and total_days > 25 and np.random.uniform(0, 1) < 0.40:
                inactivity_gap = np.random.randint(4, 18)
                active_window = max(5, total_days - inactivity_gap)
                day_deltas = np.sort(np.random.randint(0, active_window, size=num_sessions))
            else:
                day_deltas = np.sort(np.random.randint(0, total_days, size=num_sessions))

            cust_mean_dur = max(60, np.random.normal(180, 50) - (is_churn * np.random.normal(15, 20)))

            for d in day_deltas:
                s_date = signup + timedelta(days=int(d), hours=int(np.random.randint(8, 22)), minutes=int(np.random.randint(0, 59)))
                duration = max(15, int(np.random.normal(cust_mean_dur, 45)))
                pages = max(1, int(duration / np.random.uniform(30, 90)))
                is_bounced = 1 if (pages == 1 and duration < 50) else 0

                actions = ["Dashboard Browse", "Feature Usage", "Billing Management", "Support Portal", "Settings", "Data Export"]
                if is_churn:
                    action_p = [0.25, 0.25, 0.22, 0.15, 0.08, 0.05]
                else:
                    action_p = [0.32, 0.38, 0.08, 0.08, 0.06, 0.08]
                action = np.random.choice(actions, p=action_p)

                session_records.append({
                    "session_id": f"SESS-{sess_counter:07d}",
                    "customer_id": cid,
                    "session_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": duration,
                    "pages_viewed": pages,
                    "device": cust["preferred_device"],
                    "is_bounced": is_bounced,
                    "primary_action": action
                })
                sess_counter += 1

        return pd.DataFrame(session_records)

    def _generate_tickets(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generates customer support tickets (dissatisfaction, unresolved tickets strongly correlated with churn)."""
        ticket_records = []
        tck_counter = 1

        for _, cust in customers_df.iterrows():
            cid = cust["customer_id"]
            is_churn = cust["churn_status"]
            signup = datetime.strptime(cust["signup_date"], "%Y-%m-%d")
            end_date = datetime.strptime(cust["churn_date"], "%Y-%m-%d") if is_churn else self.reference_date
            total_days = max(1, (end_date - signup).days)

            # Natural ticket frequency with realistic silent churners and active user inquiries
            if is_churn:
                num_tickets = np.random.choice([0, 1, 2, 3], p=[0.42, 0.33, 0.18, 0.07])
            else:
                num_tickets = np.random.choice([0, 1, 2, 3], p=[0.55, 0.30, 0.12, 0.03])

            if num_tickets == 0:
                continue

            day_deltas = np.sort(np.random.randint(0, total_days, size=num_tickets))

            for d in day_deltas:
                t_date = signup + timedelta(days=int(d), hours=int(np.random.randint(9, 18)))
                
                if is_churn:
                    categories = ["Cancellation Request", "Billing Dispute", "Technical Outage", "Bug Report", "Poor Performance"]
                    cat_p = [0.22, 0.25, 0.23, 0.18, 0.12]
                    priorities = ["Low", "Medium", "High", "Urgent"]
                    prio_p = [0.15, 0.40, 0.30, 0.15]
                    # Realistic CSAT distribution with overlap
                    csat = np.random.choice([1, 2, 3, 4, 5], p=[0.25, 0.25, 0.25, 0.15, 0.10])
                    res_hours = round(float(np.random.exponential(scale=24.0) + 6.0), 1)
                    status_choices = ["Resolved", "Closed", "Escalated", "Open"]
                    st_p = [0.55, 0.25, 0.12, 0.08]
                else:
                    categories = ["Feature Inquiry", "How-To Question", "Onboarding Help", "Billing Question", "Minor Bug", "Cancellation Request"]
                    cat_p = [0.28, 0.25, 0.20, 0.14, 0.08, 0.05]
                    priorities = ["Low", "Medium", "High"]
                    prio_p = [0.50, 0.35, 0.15]
                    # Active customers also occasionally have low CSAT
                    csat = np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.15, 0.25, 0.30, 0.20])
                    res_hours = round(float(np.random.exponential(scale=16.0) + 4.0), 1)
                    status_choices = ["Resolved", "Closed"]
                    st_p = [0.75, 0.25]

                category = np.random.choice(categories, p=cat_p)
                priority = np.random.choice(priorities, p=prio_p)
                status = np.random.choice(status_choices, p=st_p)

                ticket_records.append({
                    "ticket_id": f"TCK-{tck_counter:07d}",
                    "customer_id": cid,
                    "created_date": t_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "category": category,
                    "priority": priority,
                    "resolution_time_hours": res_hours,
                    "csat_score": int(csat),
                    "status": status
                })
                tck_counter += 1

        return pd.DataFrame(ticket_records)

if __name__ == "__main__":
    generator = CustomerDataGenerator()
    generator.generate_all()
