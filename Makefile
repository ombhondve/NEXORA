.PHONY: help install dev-backend dev-frontend test lint clean docker-up docker-down

help:
	@echo "Recursive OSINT Discovery Engine - Development Commands"
	@echo "--------------------------------------------------------"
	@echo "install         Install all dependencies (Python backend & Node web)"
	@echo "dev-backend     Start FastAPI backend with live reload"
	@echo "dev-frontend    Start Next.js frontend dev server"
	@echo "test            Run backend pytest suite"
	@echo "lint            Lint backend and frontend code"
	@echo "docker-up       Start PostgreSQL, Redis, and OpenSearch with Docker Compose"
	@echo "docker-down     Stop all Docker Compose services"
	@echo "migrate         Run Alembic database migrations"
	@echo "clean           Clean temporary and cache directories"

install:
	python -m pip install -e ".[dev]"
	npm install

dev-backend:
	cd backend && uvicorn recursive_osint.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	npm --prefix apps/web run dev

test:
	pytest backend/tests -v

lint:
	ruff check backend/src backend/tests
	npm --prefix apps/web run lint

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
