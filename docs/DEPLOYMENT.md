# Deployment & Infrastructure Guide

## 1. Local Development
Start PostgreSQL, Redis, and OpenSearch with Docker Compose:
```bash
docker compose up -d
```
Initialize the database and storage:
```bash
python scripts/setup-dev.py
```
Start the backend:
```bash
uvicorn recursive_osint.main:app --app-dir backend/src --reload --port 8000
```
Start the frontend:
```bash
npm --prefix apps/web run dev
```

## 2. Docker Production Deployment
The full stack (PostgreSQL, Redis, OpenSearch, Backend API, Worker, Next.js Web) can be deployed with Docker Compose:
```bash
docker compose -f docker-compose.yml up -d --build
```
Access the dashboard at `http://localhost:3000` and Swagger API docs at `http://localhost:8000/docs`.
