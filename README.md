# Distributed Job Queue

A mini distributed job queue (similar to RabbitMQ/Celery): submit tasks via REST API, workers process them from Redis with priority, retries, and a dead-letter queue. Includes a React dashboard for monitoring.

## Features

- **REST API** (FastAPI) to submit and list jobs, filter by status/type, get stats
- **Worker** consumes from Redis priority queues (high → normal → low)
- **Retry system**: configurable max retries; failed jobs are re-queued until max, then moved to DLQ
- **Dead-letter queue (DLQ)** for jobs that exceed max retries
- **Job priority queue**: three levels (high, normal, low)
- **Dashboard** (React + Vite): stats, queue lengths, job list, submit form; auto-refresh every 5s
- **Persistence**: PostgreSQL for job metadata and status; Redis for queues

## Tech stack

- **Backend**: FastAPI, Redis, PostgreSQL, SQLAlchemy (sync + async)
- **Worker**: Python, Redis, PostgreSQL
- **Dashboard**: React, TypeScript, Vite
- **Run everything**: Docker Compose

## Quick start with Docker

```bash
# From repo root
docker compose up --build
```

- **API**: http://localhost:8000  
- **Docs**: http://localhost:8000/docs  
- **Dashboard**: http://localhost:3000  

Dashboard talks to the API via proxy (dev) or via nginx when using the dashboard container.

## Run locally (without Docker)

1. **Redis & PostgreSQL** running (e.g. locally or in Docker).

2. **Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp ../.env.example .env   # edit if needed
   uvicorn app.main:app --reload
   ```

3. **Worker**
   ```bash
   cd worker
   pip install -r requirements.txt
   python worker.py
   ```

4. **Dashboard**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
   Open http://localhost:3000 (Vite proxies `/api` to the backend).

## API overview

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/jobs` | Submit a job (`job_type`, `payload`, `priority`) |
| GET    | `/jobs` | List jobs (optional `status`, `job_type`, `limit`, `offset`) |
| GET    | `/jobs/stats` | Dashboard stats (counts by status + queue lengths) |
| GET    | `/jobs/{id}` | Get one job |

## Job types (built-in)

- `echo` – returns `{"echo": "<message>", "at": "..."}` (payload: `{"message": "hello"}`).
- `sleep` – sleeps N seconds (payload: `{"seconds": 2}`).
- `random_fail` – fails randomly ~60% of the time (good for testing retries and DLQ).

Add more in `worker/handlers.py` using the `@register("job_type")` decorator.

## Project layout

```
backend/          # FastAPI app
  app/
    main.py       # App, CORS, lifespan
    config.py     # Settings
    db.py         # SQLAlchemy sync + async
    models.py     # Job model
    queue_service.py  # Redis enqueue / DLQ / queue lengths
    api/jobs.py   # REST routes
worker/           # Job consumer
  worker.py       # Loop: dequeue → process → update DB / retry / DLQ
  handlers.py     # Job type handlers
  queue_client.py # Redis dequeue / DLQ
dashboard/        # React app
  src/
    api.ts        # API client
    App.tsx       # Stats, submit form, job table
docker-compose.yml
```

## Environment

See `.env.example`. Key variables:

- `JOBQUEUE_REDIS_URL` – Redis connection URL.
- `JOBQUEUE_DATABASE_URL` – PostgreSQL (sync) for worker and migrations.
- `JOBQUEUE_DATABASE_URL_ASYNC` – PostgreSQL (async) for FastAPI.
- `JOBQUEUE_MAX_RETRIES` – Max retries before moving to DLQ (default 3).

## License

MIT
