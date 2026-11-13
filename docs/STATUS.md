# Project Status

**Last updated:** 2026-11-13

## Completed and verified locally

- Milestone 0: FastAPI/React foundation, Compose services, environment-based
  configuration, initial Alembic schema, and CI configuration.
- Milestone 1: canonical public GitHub PR intake, bounded diff-only retrieval,
  deterministic evidence validation, and Groq-primary/Gemini-fallback adapters.
  LLM adapters are not called without configured keys.
- Milestone 2: durable review runs, Celery dispatch on `prism.review`, Redis
  results, atomic PostgreSQL claims, a 10-minute stale-worker lease, bounded
  retries for transient GitHub outages, permanent-failure persistence, finding
  persistence, status retrieval, and a polling frontend.

The worker keeps one asyncio loop per prefork process. This avoids asyncpg
connections being reused across per-task event loops; a regression test covers
the failure that exposed this requirement.

## Observed verification

- Python 3.12 container gate: Ruff PASS, Mypy PASS, and **39 passed** backend
  tests with 84% total coverage. The integration tests use local Compose
  PostgreSQL/Redis and deterministic fake GitHub-diff clients.
- Frontend: ESLint PASS, Vitest **1 passed**, TypeScript/Vite production build
  PASS.
- Compose: configuration validation and image builds PASS. PostgreSQL and Redis
  are healthy; backend, worker, and frontend are running.
- Runtime: a harmless nonexistent ID was dispatched through Redis/Celery and
  returned `missing`. A real public `octocat/Hello-World#1` submission
  completed through FastAPI → PostgreSQL → Redis → Celery → GitHub diff API →
  deterministic analysis → persisted API status. No repository code was
  executed and no GitHub comment was published.
- Frontend proxy: `GET /api/v1/reviews/{id}` through Vite returned the completed
  persisted result.

## Verification matrix

| Component | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend quality | Containerized Ruff, Mypy, `pytest -q` | PASS | 39 tests, Python 3.12.16. |
| Review processor | `tests/integration/test_review_processor.py` | PASS | Idempotency, concurrency, stale recovery, permanent/transient failures. |
| Frontend quality | `npm run lint && npm run test && npm run build` | PASS | 1 test; production build completed. |
| Compose runtime | `docker compose build`; `up -d` | PASS | App services running; database and Redis healthy. |
| Celery delivery | `process_review_run.delay(<random UUID>)` | PASS | Worker consumed task and returned `missing`. |
| Public end-to-end flow | Local POST/GET for `octocat/Hello-World#1` | PASS | Completed; zero findings is an abstaining result. |
| Neon PostgreSQL | Credentialed connection | NOT VERIFIED | No Neon URL is configured. |
| Groq/Gemini | Credentialed request | NOT VERIFIED | No provider keys are configured. |
| GitHub App/webhooks | Credentialed integration | NOT VERIFIED | Milestone 3 work remains. |

## Next step

Implement Milestone 3 GitHub App authentication, signed webhook verification,
and least-privilege installation access. Preserve the human approval gate for
all review publication.
