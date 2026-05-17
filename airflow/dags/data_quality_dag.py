"""Airflow DAG for data quality checks."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "ipl-data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}


def run_null_checks(**context):
    """Run null value checks across all layers."""
    from data_quality.checks.validators import DataValidator

    validator = DataValidator()
    results = validator.check_nulls("data")
    context["ti"].xcom_push(key="null_check_results", value=results)
    return results


def run_duplicate_checks(**context):
    """Run duplicate checks."""
    from data_quality.checks.validators import DataValidator

    validator = DataValidator()
    results = validator.check_duplicates("data")
    context["ti"].xcom_push(key="duplicate_check_results", value=results)
    return results


def run_schema_checks(**context):
    """Run schema validation checks."""
    from data_quality.checks.validators import DataValidator

    validator = DataValidator()
    results = validator.check_schema("data")
    context["ti"].xcom_push(key="schema_check_results", value=results)
    return results


def run_freshness_checks(**context):
    """Run data freshness checks."""
    from data_quality.checks.validators import DataValidator

    validator = DataValidator()
    results = validator.check_freshness("data")
    context["ti"].xcom_push(key="freshness_check_results", value=results)
    return results


def evaluate_results(**context):
    """Evaluate all data quality results."""
    ti = context["ti"]
    null_results = ti.xcom_pull(task_ids="quality_checks.run_null_checks",
                                 key="null_check_results") or {}
    dup_results = ti.xcom_pull(task_ids="quality_checks.run_duplicate_checks",
                                key="duplicate_check_results") or {}
    schema_results = ti.xcom_pull(task_ids="quality_checks.run_schema_checks",
                                   key="schema_check_results") or {}
    freshness_results = ti.xcom_pull(task_ids="quality_checks.run_freshness_checks",
                                      key="freshness_check_results") or {}

    all_passed = all(
        r.get("passed", True) for r in
        [null_results, dup_results, schema_results, freshness_results]
    )

    if not all_passed:
        return "alert_failure"
    return "mark_success"


with DAG(
    dag_id="ipl_data_quality",
    default_args=default_args,
    description="Data quality checks across all lakehouse layers",
    schedule_interval="0 7 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ipl", "data-quality", "validation"],
    doc_md="""
    ## IPL Data Quality Pipeline

    Runs comprehensive data quality checks:
    1. Null value checks
    2. Duplicate detection
    3. Schema validation
    4. Data freshness checks
    """,
) as dag:

    start = BashOperator(
        task_id="start_dq_checks",
        bash_command='echo "Starting Data Quality Checks - $(date)"',
    )

    with TaskGroup("quality_checks") as quality_group:
        null_check = PythonOperator(
            task_id="run_null_checks",
            python_callable=run_null_checks,
        )
        duplicate_check = PythonOperator(
            task_id="run_duplicate_checks",
            python_callable=run_duplicate_checks,
        )
        schema_check = PythonOperator(
            task_id="run_schema_checks",
            python_callable=run_schema_checks,
        )
        freshness_check = PythonOperator(
            task_id="run_freshness_checks",
            python_callable=run_freshness_checks,
        )

    evaluate = BranchPythonOperator(
        task_id="evaluate_results",
        python_callable=evaluate_results,
    )

    alert_failure = BashOperator(
        task_id="alert_failure",
        bash_command='echo "DATA QUALITY ALERT: Checks failed! Review results." && exit 1',
    )

    mark_success = BashOperator(
        task_id="mark_success",
        bash_command='echo "All data quality checks passed - $(date)"',
    )

    start >> quality_group >> evaluate >> [alert_failure, mark_success]
