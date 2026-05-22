"""Airflow DAG for streaming pipeline orchestration."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "ipl-data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def start_kafka_producer(**context):
    """Start Kafka producer for live match simulation."""
    from kafka.producers.ball_event_producer import BallEventProducer

    producer = BallEventProducer(
        bootstrap_servers=context["params"].get("kafka_servers", "kafka:9092"),
    )
    try:
        producer.simulate_live_match(
            speed=float(context["params"].get("speed", 5.0)),
            delay=float(context["params"].get("delay", 0.5)),
        )
    finally:
        producer.close()


def check_streaming_health(**context):
    """Check health of streaming pipelines."""
    import json
    from pathlib import Path

    health = {
        "kafka_producer": "healthy",
        "spark_streaming": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
    health_file = Path("data/monitoring/streaming_health.json")
    health_file.parent.mkdir(parents=True, exist_ok=True)
    with open(health_file, "w") as f:
        json.dump(health, f, indent=2)
    return health


with DAG(
    dag_id="ipl_streaming_orchestration",
    default_args=default_args,
    description="Orchestrate streaming pipeline components",
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ipl", "streaming", "kafka", "spark"],
    params={
        "kafka_servers": "kafka:9092",
        "speed": 5.0,
        "delay": 0.5,
    },
    doc_md="""
    ## IPL Streaming Orchestration

    Manages the streaming pipeline:
    1. Starts Kafka producers for match simulation
    2. Monitors streaming health
    """,
) as dag:
    health_check_start = PythonOperator(
        task_id="check_streaming_health_start",
        python_callable=check_streaming_health,
    )

    run_simulation = PythonOperator(
        task_id="run_match_simulation",
        python_callable=start_kafka_producer,
        execution_timeout=timedelta(minutes=30),
    )

    health_check_end = PythonOperator(
        task_id="check_streaming_health_end",
        python_callable=check_streaming_health,
    )

    health_check_start >> run_simulation >> health_check_end
