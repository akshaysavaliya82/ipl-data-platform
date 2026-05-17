# IPL Real-Time Analytics Lakehouse Platform

A production-grade, end-to-end data engineering platform for IPL cricket analytics using modern lakehouse architecture with real-time streaming and batch processing capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Cricsheet │  │ Kaggle IPL   │  │ Cricbuzz │  │  Synthetic   │   │
│  │  Datasets │  │  Datasets    │  │   APIs   │  │  Simulator   │   │
│  └─────┬─────┘  └──────┬───────┘  └─────┬────┘  └──────┬───────┘   │
└────────┼───────────────┼────────────────┼──────────────┼────────────┘
         │               │                │              │
         ▼               ▼                ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Kafka Producers  │  Batch Ingestion  │  Match Simulator   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│   Kafka     │    │   Spark     │    │   Airflow       │
│  Streaming  │    │  Structured │    │  Orchestration  │
│  Pipeline   │    │  Streaming  │    │  (4 DAGs)       │
└──────┬──────┘    └──────┬──────┘    └────────┬────────┘
       │                  │                    │
       ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MEDALLION ARCHITECTURE                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │ BRONZE       │  │ SILVER       │  │ GOLD                 │     │
│  │ Raw JSON     │  │ Cleaned      │  │ Analytics-ready      │     │
│  │ Immutable    │  │ Parquet      │  │ Aggregated tables    │     │
│  │ Partitioned  │  │ Deduplicated │  │ Player stats, Team   │     │
│  │              │  │ Type-cast    │  │ stats, Venue, Toss   │     │
│  └──────────────┘  └──────────────┘  └──────────────────────┘     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS WAREHOUSE (dbt)                        │
│  ┌───────────────────┐  ┌──────────────────────────────────────┐   │
│  │  Dimension Tables │  │  Fact Tables                         │   │
│  │  dim_player       │  │  fact_ball_events (incremental)      │   │
│  │  dim_team         │  │  fact_match_summary (incremental)    │   │
│  │  dim_venue        │  │  fact_player_performance             │   │
│  │  dim_match        │  │                                      │   │
│  └───────────────────┘  └──────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌─────────────┐ ┌──────────────────┐
│  FastAPI REST    │ │  Streamlit  │ │  Data Quality    │
│  API (8000)      │ │  Dashboard  │ │  Framework       │
│  /players        │ │  (8501)     │ │  Null checks     │
│  /matches        │ │  Live Match │ │  Duplicate checks│
│  /teams          │ │  Team Stats │ │  Schema checks   │
│  /venues         │ │  Player     │ │  Freshness checks│
│  /analytics      │ │  Venue      │ │                  │
│  /win-probability│ │  Fantasy    │ │                  │
└──────────────────┘ └─────────────┘ └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.12 |
| **Batch Processing** | Apache Spark (PySpark) |
| **Stream Processing** | Kafka + Spark Structured Streaming |
| **Orchestration** | Apache Airflow |
| **Data Warehouse** | PostgreSQL + dbt |
| **Storage Format** | Parquet, Delta Lake |
| **REST API** | FastAPI |
| **Dashboard** | Streamlit + Plotly |
| **Data Quality** | Custom validation framework |
| **Monitoring** | Prometheus + Structlog |
| **Infrastructure** | Docker Compose, Terraform (AWS) |
| **CI/CD** | GitHub Actions |

## Project Structure

```
ipl-data-platform/
├── ingestion/              # Data ingestion layer
│   ├── simulators/         # Live match simulator
│   ├── sources/            # Sample data & Cricsheet parser
│   └── parsers/            # Data parsers
├── kafka/                  # Kafka streaming pipeline
│   ├── config/             # Topic configurations
│   ├── producers/          # Ball event producer
│   └── consumers/          # Spark Structured Streaming consumer
├── spark_jobs/             # Spark ETL jobs
│   ├── bronze/             # Raw data ingestion
│   ├── silver/             # Data cleaning & transformation
│   ├── gold/               # Analytics aggregations
│   └── utils/              # Spark session & I/O utilities
├── dbt/                    # dbt transformations
│   ├── models/
│   │   ├── staging/        # Staging views
│   │   ├── intermediate/   # Ephemeral batting/bowling stats
│   │   └── marts/
│   │       ├── core/       # Dimension tables
│   │       └── analytics/  # Fact tables (incremental)
│   ├── macros/             # Custom macros & tests
│   └── snapshots/          # SCD snapshots
├── airflow/                # Airflow DAGs
│   └── dags/               # 4 DAGs: ingestion, ETL, streaming, DQ
├── api/                    # FastAPI REST API
│   ├── core/               # Database configuration
│   ├── models/             # Pydantic schemas
│   ├── routers/            # API endpoints
│   └── services/           # Business logic
├── dashboard/              # Streamlit dashboard
│   ├── pages/              # 5 dashboard pages
│   ├── components/         # Charts & KPI components
│   └── utils/              # Data loaders
├── data_quality/           # Data quality framework
│   ├── checks/             # Validators (null, dup, schema, freshness)
│   ├── expectations/       # Great Expectations configs
│   └── reports/            # Quality reports
├── monitoring/             # Monitoring & logging
│   ├── logger.py           # Structlog configuration
│   └── metrics.py          # Prometheus metrics
├── config/                 # Application configuration
│   └── settings.py         # Pydantic settings management
├── infrastructure/         # Infrastructure as Code
│   ├── terraform/          # AWS Terraform configs
│   └── scripts/            # DB initialization scripts
├── docker/                 # Dockerfiles
│   ├── api/                # FastAPI Dockerfile
│   ├── dashboard/          # Streamlit Dockerfile
│   ├── spark/              # Spark Dockerfile
│   ├── kafka/              # Kafka producer Dockerfile
│   └── airflow/            # Airflow Dockerfile
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Full service orchestration
├── Makefile                # Development commands
├── pyproject.toml          # Project configuration
└── .env.example            # Environment template
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Make (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/ipl-data-platform.git
cd ipl-data-platform

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Access services:
# - API:        http://localhost:8000/docs
# - Dashboard:  http://localhost:8501
# - Airflow:    http://localhost:8081 (admin/admin)
# - Spark UI:   http://localhost:8080
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Generate sample data
make generate-data

# Start the API
make run-api

# In another terminal, start the dashboard
make run-dashboard
```

## Components

### 1. Data Ingestion

- **Match Simulator**: Generates realistic ball-by-ball IPL events
- **Sample Data Generator**: Creates 200+ matches, 40+ players, ball-by-ball records
- **Cricsheet Parser**: Parses real IPL data from Cricsheet format

```bash
# Generate sample data
make generate-data

# Run a live match simulation
make run-simulation
```

### 2. Streaming Pipeline

Kafka producers simulate live match events:
- Ball-by-ball events
- Score updates
- Wicket events
- Match state changes

Spark Structured Streaming consumers process events in real-time with windowed aggregations.

### 3. Batch ETL (Medallion Architecture)

| Layer | Description | Format |
|-------|-------------|--------|
| **Bronze** | Raw immutable data with metadata | Parquet (partitioned by season) |
| **Silver** | Cleaned, deduplicated, type-cast | Parquet |
| **Gold** | Analytics aggregations | Parquet/Delta |

Gold layer analytics include:
- Player performance (batting/bowling stats)
- Match summaries with competitiveness metrics
- Team statistics with win percentages
- Venue analytics (bat-first vs chase)
- Toss impact analysis
- Powerplay/death overs analysis

### 4. dbt Transformations

Star-schema data warehouse with:
- **Staging models**: Clean views over raw data
- **Intermediate models**: Batting/bowling statistics (ephemeral)
- **Dimension tables**: `dim_player`, `dim_team`, `dim_venue`, `dim_match`
- **Fact tables**: `fact_ball_events`, `fact_match_summary`, `fact_player_performance` (incremental)
- **SCD snapshots**: Team statistics tracking over time
- **Custom macros**: Schema generation, positive value tests

### 5. Airflow DAGs

| DAG | Schedule | Description |
|-----|----------|-------------|
| `ipl_daily_ingestion` | Daily | Data generation + Bronze ingestion + validation |
| `ipl_batch_etl` | 6 AM daily | Silver + Gold transforms + dbt run/test |
| `ipl_streaming_orchestration` | Hourly | Kafka producer + health checks |
| `ipl_data_quality` | 7 AM daily | Null/duplicate/schema/freshness checks |

### 6. REST API (FastAPI)

```
GET  /api/v1/players/             # Player statistics
GET  /api/v1/players/top-batsmen  # Top batsmen
GET  /api/v1/players/top-bowlers  # Top bowlers
GET  /api/v1/matches/             # Match data
GET  /api/v1/matches/seasons      # Season summaries
GET  /api/v1/matches/recent       # Recent matches
GET  /api/v1/teams/               # Team statistics
GET  /api/v1/teams/compare        # Head-to-head comparison
GET  /api/v1/teams/rankings       # Team rankings
GET  /api/v1/venues/              # Venue statistics
GET  /api/v1/venues/best-batting  # Best batting venues
GET  /api/v1/venues/chase-friendly # Chase-friendly venues
POST /api/v1/analytics/win-probability   # Win probability
POST /api/v1/analytics/fantasy-score     # Fantasy score
GET  /api/v1/analytics/pressure-index    # Pressure index
```

Interactive docs at `/docs` (Swagger UI) and `/redoc`.

### 7. Streamlit Dashboard

Five interactive dashboard pages:
1. **Overview**: KPIs, team wins, season trends, toss impact
2. **Live Match**: Real-time simulation with win probability gauges
3. **Team Analytics**: Season performance, toss impact, H2H comparison
4. **Player Analytics**: Batting/bowling analysis, phase-wise stats, player search
5. **Fantasy Insights**: Score calculator, dream team builder, impact players

### 8. Data Quality Framework

Custom validation framework with:
- **Null checks**: Required field validation across all datasets
- **Duplicate checks**: Primary key uniqueness validation
- **Schema checks**: Field presence and type validation
- **Freshness checks**: File modification time monitoring
- **Automated reports**: JSON reports with timestamps

### 9. Advanced Analytics

- **Win Probability Model**: Heuristic model using target, score, wickets, overs
- **Fantasy Score Calculator**: Points for batting, bowling, fielding
- **Pressure Index**: Match situation assessment
- **Strike Rate Trends**: Phase-wise batting analysis

## Development

### Available Make Commands

```bash
make help           # Show all commands
make setup          # Initial project setup
make lint           # Run linting (ruff)
make format         # Auto-format code
make test           # Run unit tests
make test-cov       # Tests with coverage
make generate-data  # Generate sample datasets
make quality-check  # Run data quality checks
make run-api        # Start FastAPI (port 8000)
make run-dashboard  # Start Streamlit (port 8501)
make docker-up      # Start Docker services
make docker-down    # Stop Docker services
make clean          # Clean generated files
```

### Running Tests

```bash
# Unit tests
make test

# With coverage
make test-cov

# Specific test file
PYTHONPATH=. pytest tests/unit/test_api.py -v
```

### CI/CD

GitHub Actions workflows:
- **CI Pipeline**: Lint, test, validate dbt, validate Docker, validate Airflow DAGs
- **Release Pipeline**: Build & test on tag push, Docker image builds

## AWS Deployment Guide

Terraform configurations are provided for:
- **S3**: Data lake with lifecycle policies (Bronze → Standard-IA → Glacier)
- **RDS**: PostgreSQL with encryption and backups
- **MSK**: Managed Kafka cluster

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Configuration

All configuration is managed through environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `ipl_analytics` | Database name |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `SPARK_MASTER` | `local[*]` | Spark master URL |
| `DATA_LAKE_PATH` | `/opt/data/lake` | Data lake root |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |

## License

MIT License
