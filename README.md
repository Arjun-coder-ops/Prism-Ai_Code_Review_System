# PRISM

PRISM (Pull Request Intelligence, Security, and Monitoring) is an
evidence-driven pull-request risk intelligence system. It is being implemented
as a modular monolith: FastAPI, PostgreSQL, Redis/Celery, and a React dashboard.

## Current Status

Milestone 0 is runtime-verified in local Compose. The API exposes liveness and
readiness endpoints; the frontend is a deliberately minimal foundation screen.
The persistence layer uses versioned Alembic migrations and accepts Neon-style
pooled application URLs plus direct migration URLs. GitHub, review, and
publication functionality remain unimplemented. Groq is the configured future
primary LLM provider and Gemini the fallback; no provider credentials are
stored in this repository.

## Local Development

1. Copy `.env.example` to `.env` for local service defaults.
2. Create a virtual environment and install the locked backend development
   environment: `python -m venv .venv` then
   `.venv\\Scripts\\python -m pip install -r backend\\requirements.lock -e ".\\backend[dev]"`.
3. Install frontend dependencies: `npm --prefix frontend install`.
4. Run API checks: `.venv\\Scripts\\python -m pytest backend/tests`.
5. Run frontend checks: `npm --prefix frontend test` and
   `npm --prefix frontend run build`.

`docker compose up --build` starts the local PostgreSQL, Redis, API, and web
services. Run `docker compose exec -T backend alembic -c alembic.ini upgrade
head` once to apply the reviewed local schema migration.

See `docs/` for architecture, API, security, testing, evaluation, and status.
