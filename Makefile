.PHONY: dev dev-build test lint typecheck clean seed reset help

help:
	@echo "Social Support AI — Development Commands"
	@echo "========================================"
	@echo "make dev         Start all Docker services"
	@echo "make dev-build   Build and start Docker services"
	@echo "make test        Run all tests"
	@echo "make test-unit   Run unit tests only"
	@echo "make test-int    Run integration tests only"
	@echo "make lint        Run Ruff linter"
	@echo "make typecheck   Run MyPy type checker"
	@echo "make seed        Seed databases with synthetic data"
	@echo "make clean       Clean temporary files and caches"
	@echo "make reset       Stop and remove all containers + volumes"

dev:
	docker compose up -d

dev-build:
	docker compose up --build -d

test:
	python -m pytest tests/ -v --cov=backend --cov-report=term-missing

test-unit:
	python -m pytest tests/unit/ -v

test-int:
	python -m pytest tests/integration/ -v

lint:
	ruff check backend/ tests/ frontend/
	ruff format --check backend/ tests/ frontend/

typecheck:
	mypy backend/ tests/

seed:
	python -m backend.seed.seed_runner

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .coverage htmlcov

reset:
	docker compose down -v
