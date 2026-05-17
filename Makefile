.PHONY: help setup install lint test format run-api run-dashboard docker-up docker-down generate-data quality-check clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

setup: ## Initial project setup
	pip install -e ".[dev]"
	pre-commit install || true
	mkdir -p data/samples data/bronze data/silver data/gold data/warehouse data/monitoring

install: ## Install dependencies
	pip install -e ".[dev]"

lint: ## Run linting
	ruff check .
	ruff format --check .

format: ## Format code
	ruff format .
	ruff check --fix .

test: ## Run unit tests
	PYTHONPATH=. pytest tests/unit/ -v --tb=short

test-cov: ## Run tests with coverage
	PYTHONPATH=. pytest tests/unit/ -v --tb=short --cov=. --cov-report=html

generate-data: ## Generate sample datasets
	PYTHONPATH=. python -c "from ingestion.sources.sample_data import save_sample_data; save_sample_data('data/samples')"

quality-check: ## Run data quality checks
	PYTHONPATH=. python -m data_quality.checks.validators

run-api: ## Start FastAPI server
	PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard: ## Start Streamlit dashboard
	PYTHONPATH=. streamlit run dashboard/app.py --server.port 8501

run-simulation: ## Run a live match simulation
	PYTHONPATH=. python -c "from ingestion.simulators.match_simulator import MatchSimulator; s = MatchSimulator(speed=10); [print(e) for e in s.generate_sample_events(20)]"

docker-up: ## Start all Docker services
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-build: ## Build all Docker images
	docker compose build

docker-logs: ## View Docker logs
	docker compose logs -f

dbt-run: ## Run dbt models
	cd dbt && dbt run --profiles-dir .

dbt-test: ## Run dbt tests
	cd dbt && dbt test --profiles-dir .

clean: ## Clean generated files
	rm -rf data/bronze data/silver data/gold data/warehouse data/monitoring
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	rm -rf dbt/target dbt/dbt_packages dbt/logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
