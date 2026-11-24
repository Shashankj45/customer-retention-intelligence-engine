"""
Apache Airflow DAG: Customer Intelligence, Churn, LTV & Retention Pipeline.
Schedules daily batch ingestion, quality validation, SQL analytics views,
model training/inference, SHAP explainability, and Power BI analytical exports.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to sys.path so Airflow can resolve src.* imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.empty import EmptyOperator
    AIRFLOW_INSTALLED = True
except ImportError:
    # Allow safe execution and inspection even outside live Airflow worker
    AIRFLOW_INSTALLED = False

# Task Callables
def task_run_etl():
    """Extracts, cleanses, validates, and loads customer datasets."""
    from src.data.etl_pipeline import ETLPipeline
    pipeline = ETLPipeline()
    success = pipeline.run()
    if not success:
        raise RuntimeError("ETL Pipeline failed.")

def task_run_sql_views():
    """Deploys analytical SQL views (RFM, Cohorts, Revenue Trends)."""
    from src.database.sql_runner import SQLAnalyticsRunner
    runner = SQLAnalyticsRunner()
    runner.deploy_all_views()

def task_monitor_drift():
    """Checks feature distributions for statistical drift."""
    from src.mlops.drift_monitor import DriftMonitor
    monitor = DriftMonitor()
    report = monitor.evaluate_drift()
    print(f"Drift Status: {report['overall_status']} (Max PSI: {report['max_psi']})")

def task_train_churn():
    """Trains and benchmarks churn classification models and logs to MLflow."""
    from src.models.churn_model import ChurnModelEngine
    from src.mlops.mlflow_tracker import MLflowTracker
    engine = ChurnModelEngine()
    engine.train_and_benchmark()
    tracker = MLflowTracker()
    tracker.log_churn_experiment()

def task_compute_shap():
    """Computes global feature importance and customer SHAP explanations."""
    from src.models.explainability import ChurnExplainabilityEngine
    explainer = ChurnExplainabilityEngine()
    explainer.compute_global_importance(sample_size=300)

def task_train_clv():
    """Trains Customer Lifetime Value regression model and logs to MLflow."""
    from src.models.clv_model import CLVModelEngine
    from src.mlops.mlflow_tracker import MLflowTracker
    engine = CLVModelEngine()
    engine.train_and_evaluate()
    tracker = MLflowTracker()
    tracker.log_clv_experiment()

def task_retention_recommendations():
    """Generates personalized retention strategies and ROI estimations."""
    from src.retention.decision_engine import RetentionDecisionEngine
    engine = RetentionDecisionEngine()
    engine.generate_recommendations()

def task_export_power_bi():
    """Materializes clean analytical tables for Power BI reporting."""
    from power_bi.export_data import PowerBIExporter
    exporter = PowerBIExporter()
    exporter.export_all()

# DAG Definition
default_args = {
    "owner": "data_science_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

if AIRFLOW_INSTALLED:
    dag = DAG(
        dag_id="customer_intelligence_retention_pipeline",
        default_args=default_args,
        description="End-to-end Customer Intelligence, Churn ML, CLV and Retention ROI Pipeline",
        schedule_interval="0 2 * * *",  # Daily at 02:00 AM UTC
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["data-science", "churn", "clv", "mlops", "power-bi"]
    )

    with dag:
        start = EmptyOperator(task_id="pipeline_start")

        t1_etl = PythonOperator(
            task_id="etl_ingestion_and_quality_check",
            python_callable=task_run_etl
        )

        t2_sql = PythonOperator(
            task_id="deploy_sql_analytical_views",
            python_callable=task_run_sql_views
        )

        t3_drift = PythonOperator(
            task_id="evaluate_data_drift",
            python_callable=task_monitor_drift
        )

        t4_churn = PythonOperator(
            task_id="train_churn_model_and_mlflow_log",
            python_callable=task_train_churn
        )

        t5_shap = PythonOperator(
            task_id="compute_shap_explainability",
            python_callable=task_compute_shap
        )

        t6_clv = PythonOperator(
            task_id="train_clv_model_and_mlflow_log",
            python_callable=task_train_clv
        )

        t7_retention = PythonOperator(
            task_id="generate_retention_recommendations",
            python_callable=task_retention_recommendations
        )

        t8_pbi = PythonOperator(
            task_id="export_power_bi_data_mart",
            python_callable=task_export_power_bi
        )

        end = EmptyOperator(task_id="pipeline_complete")

        # Dependency Graph
        start >> t1_etl >> [t2_sql, t3_drift]
        t2_sql >> t4_churn >> t5_shap
        t2_sql >> t6_clv
        [t5_shap, t6_clv] >> t7_retention >> t8_pbi >> end
