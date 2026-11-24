"""
Master Pipeline Orchestrator CLI.
Allows running the full end-to-end data science lifecycle or individual stages via command line.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger

logger = get_logger("orchestrator")

def run_generate():
    from src.data.generator import CustomerDataGenerator
    logger.info(">>> Stage: Synthetic Data Generation")
    generator = CustomerDataGenerator()
    generator.generate_all()

def run_etl():
    from src.data.etl_pipeline import ETLPipeline
    logger.info(">>> Stage: Automated ETL & Data Quality Validation")
    pipeline = ETLPipeline()
    pipeline.run()

def run_sql():
    from src.database.sql_runner import SQLAnalyticsRunner
    logger.info(">>> Stage: SQL Analytics Views Deployment (RFM, Cohorts, Revenue Trends)")
    runner = SQLAnalyticsRunner()
    runner.deploy_all_views()

def run_features():
    from src.features.feature_engineering import FeatureEngineeringPipeline
    logger.info(">>> Stage: Feature Engineering Matrix Construction")
    pipeline = FeatureEngineeringPipeline()
    pipeline.build_feature_dataset()

def run_churn():
    from src.models.churn_model import ChurnModelEngine
    from src.models.explainability import ChurnExplainabilityEngine
    from src.mlops.mlflow_tracker import MLflowTracker
    logger.info(">>> Stage: Churn ML Benchmarking, XGBoost Training & SHAP Explainability")
    engine = ChurnModelEngine()
    engine.train_and_benchmark()
    explainer = ChurnExplainabilityEngine()
    explainer.compute_global_importance(sample_size=300)
    tracker = MLflowTracker()
    tracker.log_churn_experiment()

def run_clv():
    from src.models.clv_model import CLVModelEngine
    from src.mlops.mlflow_tracker import MLflowTracker
    logger.info(">>> Stage: Customer Lifetime Value (CLV) Regression & Pareto Analysis")
    engine = CLVModelEngine()
    engine.train_and_evaluate()
    tracker = MLflowTracker()
    tracker.log_clv_experiment()

def run_retention():
    from src.retention.decision_engine import RetentionDecisionEngine
    logger.info(">>> Stage: Retention Optimization Strategy & ROI Assignment")
    engine = RetentionDecisionEngine()
    engine.generate_recommendations()

def run_powerbi():
    from power_bi.export_data import PowerBIExporter
    logger.info(">>> Stage: Power BI Star Schema Data Mart Export")
    exporter = PowerBIExporter()
    exporter.export_all()

def run_drift():
    from src.mlops.drift_monitor import DriftMonitor
    logger.info(">>> Stage: Statistical Data Drift Evaluation")
    monitor = DriftMonitor()
    monitor.evaluate_drift()

def run_all():
    logger.info("=================================================================")
    logger.info("EXECUTING FULL END-TO-END CUSTOMER INTELLIGENCE PLATFORM PIPELINE")
    logger.info("=================================================================")
    run_generate()
    run_etl()
    run_sql()
    run_features()
    run_churn()
    run_clv()
    run_retention()
    run_drift()
    run_powerbi()
    logger.info("=================================================================")
    logger.info("ALL PIPELINE STAGES COMPLETED SUCCESSFULLY!")
    logger.info("Launch dashboard with: streamlit run dashboard/app.py")
    logger.info("=================================================================")

def main():
    parser = argparse.ArgumentParser(description="Customer Intelligence & Retention Engine CLI")
    parser.add_argument(
        "--step",
        choices=["all", "generate", "etl", "sql", "features", "churn", "clv", "retention", "drift", "powerbi", "dashboard"],
        default="all",
        help="Pipeline stage to execute (default: all)"
    )
    args = parser.parse_args()

    dispatch = {
        "all": run_all,
        "generate": run_generate,
        "etl": run_etl,
        "sql": run_sql,
        "features": run_features,
        "churn": run_churn,
        "clv": run_clv,
        "retention": run_retention,
        "drift": run_drift,
        "powerbi": run_powerbi
    }

    if args.step == "dashboard":
        import subprocess
        subprocess.run(["streamlit", "run", "dashboard/app.py"])
    else:
        dispatch[args.step]()

if __name__ == "__main__":
    main()
