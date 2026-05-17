FROM apache/airflow:2.8.1-python3.12

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY pyproject.toml /opt/app/pyproject.toml

RUN pip install --no-cache-dir \
    apache-airflow==2.8.1 \
    pyspark==3.5.0 \
    kafka-python==2.0.2 \
    pandas==2.2.0 \
    sqlalchemy==2.0.0 \
    psycopg2-binary==2.9.9 \
    structlog==24.1.0 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0

COPY --chown=airflow:root . /opt/app
WORKDIR /opt/app

ENV PYTHONPATH="/opt/app:${PYTHONPATH}"
