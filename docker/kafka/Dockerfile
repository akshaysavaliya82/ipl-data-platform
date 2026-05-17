FROM python:3.12-slim

WORKDIR /opt/app

RUN pip install --no-cache-dir \
    confluent-kafka==2.3.0 \
    kafka-python==2.0.2 \
    structlog==24.1.0 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    prometheus-client==0.20.0 \
    pyyaml==6.0.0

COPY . .

ENV PYTHONPATH="/opt/app:${PYTHONPATH}"

CMD ["python", "-m", "kafka.producers.ball_event_producer"]
