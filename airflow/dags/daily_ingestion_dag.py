"""Airflow DAG for daily IPL data ingestion pipeline."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "ipl-data-platform",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}


def generate_sample_data(**context):
    """Generate sample datasets for ingestion."""
    from ingestion.sources.sample_data import save_sample_data

    files = save_sample_data("data/samples")
    context["ti"].xcom_push(key="generated_files", value=files)
    return files


def run_bronze_ingestion(**context):
    """Run Bronze layer ingestion."""
    from spark_jobs.bronze.ingest_raw_data import BronzeIngestion

    ingestion = BronzeIngestion(
        raw_path="data/samples",
        bronze_path="data/bronze",
    )
    results = ingestion.run_full_ingestion()
    context["ti"].xcom_push(key="bronze_results", value=results)
    return results


def validate_bronze_data(**context):
    """Validate Bronze layer data quality."""
    from data_quality.checks.validators import DataValidator

    validator = DataValidator()
    results = validator.validate_bronze_layer("data/bronze")
    if not results["passed"]:
        raise ValueError(f"Bronze validation failed: {results['failures']}")
    return results


with DAG(
    dag_id="ipl_daily_ingestion",
    default_args=default_args,
    description="Daily IPL data ingestion pipeline",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ipl", "ingestion", "daily"],
    doc_md="""
    ## IPL Daily Ingestion Pipeline

    Ingests raw IPL data into the Bronze layer of the lakehouse.

    ### Steps:
    1. Generate/fetch sample data
    2. Ingest into Bronze layer
    3. Validate data quality
    """,
) as dag:
    start = BashOperator(
        task_id="start_pipeline",
        bash_command='echo "Starting IPL Daily Ingestion - $(date)"',
    )

    with TaskGroup("data_generation") as data_gen_group:
        generate_data = PythonOperator(
            task_id="generate_sample_data",
            python_callable=generate_sample_data,
        )

    with TaskGroup("bronze_ingestion") as bronze_group:
        ingest_bronze = PythonOperator(
            task_id="run_bronze_ingestion",
            python_callable=run_bronze_ingestion,
        )

    with TaskGroup("quality_checks") as quality_group:
        validate_bronze = PythonOperator(
            task_id="validate_bronze_data",
            python_callable=validate_bronze_data,
        )

    end = BashOperator(
        task_id="end_pipeline",
        bash_command='echo "IPL Daily Ingestion Completed - $(date)"',
    )

    start >> data_gen_group >> bronze_group >> quality_group >> end
