"""Airflow DAG for batch ETL pipeline (Silver + Gold layers)."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "ipl-data-platform",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}


def run_silver_transforms(**context):
    """Run Silver layer transformations."""
    from spark_jobs.silver.transform_matches import SilverMatchTransformer

    transformer = SilverMatchTransformer(
        bronze_path="data/bronze",
        silver_path="data/silver",
    )
    results = transformer.run_all_transforms()
    context["ti"].xcom_push(key="silver_results", value=results)
    return results


def run_gold_analytics(**context):
    """Run Gold layer analytics."""
    from spark_jobs.gold.match_analytics import GoldMatchAnalytics

    analytics = GoldMatchAnalytics(
        silver_path="data/silver",
        gold_path="data/gold",
    )
    results = analytics.run_all_analytics()
    context["ti"].xcom_push(key="gold_results", value=results)
    return results


def run_dbt_models(**context):
    """Run dbt transformations."""
    import subprocess

    result = subprocess.run(
        ["dbt", "run", "--project-dir", "dbt", "--profiles-dir", "dbt"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed: {result.stderr}")
    return result.stdout


def run_dbt_tests(**context):
    """Run dbt tests."""
    import subprocess

    result = subprocess.run(
        ["dbt", "test", "--project-dir", "dbt", "--profiles-dir", "dbt"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt test failed: {result.stderr}")
    return result.stdout


with DAG(
    dag_id="ipl_batch_etl",
    default_args=default_args,
    description="Batch ETL pipeline for Silver and Gold layers",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ipl", "etl", "batch", "spark", "dbt"],
    doc_md="""
    ## IPL Batch ETL Pipeline

    Transforms data through Silver and Gold layers.

    ### Steps:
    1. Silver layer: Clean and transform Bronze data
    2. Gold layer: Generate analytics aggregations
    3. dbt: Run warehouse transformations
    4. dbt: Run data tests
    """,
) as dag:
    start = BashOperator(
        task_id="start_etl",
        bash_command='echo "Starting Batch ETL - $(date)"',
    )

    with TaskGroup("silver_layer") as silver_group:
        silver_transform = PythonOperator(
            task_id="run_silver_transforms",
            python_callable=run_silver_transforms,
        )

    with TaskGroup("gold_layer") as gold_group:
        gold_analytics = PythonOperator(
            task_id="run_gold_analytics",
            python_callable=run_gold_analytics,
        )

    with TaskGroup("dbt_transformations") as dbt_group:
        dbt_run = PythonOperator(
            task_id="run_dbt_models",
            python_callable=run_dbt_models,
        )

        dbt_test = PythonOperator(
            task_id="run_dbt_tests",
            python_callable=run_dbt_tests,
        )

        dbt_run >> dbt_test

    end = BashOperator(
        task_id="end_etl",
        bash_command='echo "Batch ETL Completed - $(date)"',
    )

    start >> silver_group >> gold_group >> dbt_group >> end
