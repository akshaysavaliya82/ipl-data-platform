FROM python:3.12-slim

WORKDIR /opt/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    uvicorn==0.27.0 \
    sqlalchemy==2.0.0 \
    psycopg2-binary==2.9.9 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    structlog==24.1.0 \
    prometheus-client==0.20.0 \
    httpx==0.27.0 \
    pyyaml==6.0.0 \
    python-dotenv==1.0.0

COPY . .

ENV PYTHONPATH="/opt/app:${PYTHONPATH}"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
