FROM python:3.12-slim

WORKDIR /opt/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir \
    streamlit==1.31.0 \
    plotly==5.18.0 \
    altair==5.2.0 \
    pandas==2.2.0 \
    numpy==1.26.0 \
    requests==2.31.0 \
    structlog==24.1.0 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    pyyaml==6.0.0 \
    python-dotenv==1.0.0

COPY . .

ENV PYTHONPATH="/opt/app:${PYTHONPATH}"

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
