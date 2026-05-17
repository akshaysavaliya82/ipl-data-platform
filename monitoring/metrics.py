"""Prometheus metrics for the IPL Data Platform."""

from prometheus_client import Counter, Gauge, Histogram, Info

# Application info
app_info = Info("ipl_platform", "IPL Data Platform information")
app_info.info({
    "version": "1.0.0",
    "app_name": "IPL Real-Time Analytics Lakehouse Platform",
})

# Ingestion metrics
records_ingested = Counter(
    "ipl_records_ingested_total",
    "Total number of records ingested",
    ["source", "layer"],
)
ingestion_errors = Counter(
    "ipl_ingestion_errors_total",
    "Total ingestion errors",
    ["source", "error_type"],
)
ingestion_duration = Histogram(
    "ipl_ingestion_duration_seconds",
    "Time spent on ingestion operations",
    ["source"],
)

# Kafka metrics
kafka_messages_produced = Counter(
    "ipl_kafka_messages_produced_total",
    "Total Kafka messages produced",
    ["topic"],
)
kafka_messages_consumed = Counter(
    "ipl_kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic", "consumer_group"],
)
kafka_consumer_lag = Gauge(
    "ipl_kafka_consumer_lag",
    "Kafka consumer lag",
    ["topic", "partition"],
)

# Spark job metrics
spark_job_duration = Histogram(
    "ipl_spark_job_duration_seconds",
    "Time spent on Spark jobs",
    ["job_name", "layer"],
)
spark_job_records_processed = Counter(
    "ipl_spark_records_processed_total",
    "Total records processed by Spark jobs",
    ["job_name", "layer"],
)

# API metrics
api_requests = Counter(
    "ipl_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)
api_request_duration = Histogram(
    "ipl_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
)

# Data quality metrics
dq_checks_run = Counter(
    "ipl_dq_checks_total",
    "Total data quality checks run",
    ["check_type", "result"],
)
dq_check_duration = Histogram(
    "ipl_dq_check_duration_seconds",
    "Data quality check duration",
    ["check_type"],
)
