FROM bitnami/spark:3.5

USER root

RUN pip install --no-cache-dir \
    delta-spark==3.1.0 \
    pyspark==3.5.0 \
    pandas==2.2.0 \
    structlog==24.1.0 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    pyyaml==6.0.0

COPY . /opt/app
WORKDIR /opt/app

ENV PYTHONPATH="/opt/app:${PYTHONPATH}"
