# Project Status

**Last updated:** 2026-11-13

## Completed

- Milestone 0 foundation: FastAPI health/readiness endpoints, React/Vite shell,
  Compose services, CI configuration, environment example, and documentation.
- Neon-compatible persistence foundation: async SQLAlchemy engine/session,
  Alembic configuration, and a reviewed initial migration for users, GitHub
  installations, repositories, pull requests, review runs, and findings.
- Configuration now distinguishes `DATABASE_URL` (application/pooler) from
  `DIRECT_DATABASE_URL` (migrations). No secrets were added; `.env.example`
  has placeholders for Groq primary and Gemini fallback credentials.
- Configuration enforces Groq as the primary provider and Gemini as the
  fallback; API keys use redacting `SecretStr` values. No LLM provider adapter
  has been implemented or invoked.
- Milestone 1 is now in progress: canonical public-GitHub PR intake, fixed-base
  metadata retrieval, queued review-run persistence, and a narrow
  deterministic unified-diff analyzer are implemented. The analyzer never
  executes repository code and verifies exact line evidence before retaining a
  candidate.

## Observed Verification

- Ruff and strict mypy passed after the persistence and provider-configuration
  changes.
- Alembic history reported the `20261112_0001` head revision.
- Docker Compose built `prism-backend` and `prism-frontend`, then started the
  isolated PostgreSQL, Redis, backend, and frontend services.
- PostgreSQL and Redis reported healthy. The initial migration applied to the
  new local `prism_postgres_data` volume; `alembic_version` contains
  `20261112_0001` and Redis returned `PONG`.
- `GET /health` returned `200 {"status":"ok"}`; `GET /ready` returned `200`
  with PostgreSQL and Redis both `ok`; the frontend returned HTTP `200`.
- Earlier foundation checks passed: frontend lint, Vitest (1 test), TypeScript
  build, Vite production build, and production-only npm audit (0 findings).
- The rebuilt Compose stack is running with PostgreSQL and Redis healthy;
  `/ready` reports both dependencies as `ok`. OpenAPI contains
  `POST /api/v1/reviews`; a malicious-host URL returns the intended `422`
  before any GitHub call.
- Backend static checks pass, and the complete backend suite runs in an
  isolated Linux container: **25 passed**, **86%** coverage.

## Verification Gaps and Blockers

- The current host Python 3.15 environment hangs while creating its async
  event-loop self-pipe, before async pytest tests execute. The post-change
  full backend suite therefore has **not** been counted as passing. The
  attempted ephemeral Linux test runner lost its connection before returning a
  result.
- Docker Desktop was available for the successful run above, but is currently
  unavailable again (`dockerDesktopLinuxEngine` pipe missing). Restart/recovery
  verification and fresh container retesting are not currently possible.
- No Neon, Groq, Gemini, or GitHub credentials are configured; live external
  connectivity is intentionally not verified.
- The project directory has no repository-local Git root or remote, so no
  commits or pushes were made.
- Full `npm audit` still reports seven moderate, dev-only advisories in the
  TypeScript ESLint chain. The compatible production audit remains clean.

## Verification Matrix

| Component | Command | Result | Detail / corrective action |
| --- | --- | --- | --- |
| Python dependencies | `pip install -e ".[dev]"` | PASS | `pip check` passed after adding Alembic. |
| Backend static checks | `ruff check app tests migrations`; `mypy app` | PASS | Verified after persistence changes. |
| Backend tests, current code | Isolated Linux `pytest -q` | PASS | 25 passed; 86% coverage. |
| Alembic metadata/history | `alembic -c alembic.ini history` | PASS | Initial revision is the migration head. |
| Compose model | `docker compose config --quiet` | PASS | Compose syntax validated. |
| Container images | `docker compose build backend`; `docker compose build frontend` | PASS | Both PRISM application images built. |
| Local services | `docker compose up --detach --no-build` | PASS | PostgreSQL and Redis healthy; API and frontend up. |
| Local migration | `docker compose exec -T backend alembic -c alembic.ini upgrade head` | PASS | Applied `20261112_0001` to the local volume. |
| Runtime probes | PostgreSQL/Redis CLI and HTTP requests | PASS | Migration revision, `PONG`, health/readiness, and frontend HTTP 200 observed. |
| Frontend checks | `npm run lint`; `npm test`; `npm run build` | PASS (earlier) | 1 Vitest test and production build passed before backend-only changes. |
| Production npm audit | `npm audit --omit=dev` | PASS | 0 production vulnerabilities. |
| Live Neon / LLM / GitHub | Credentialed checks | NOT VERIFIED | Credentials intentionally absent; public GitHub calls are mocked in tests. |

## Next Step

Restore Docker Desktop access and run the backend suite in a working Linux or
corrected host Python environment. Then implement Milestone 1 with deterministic
analysis first, Groq primary/Gemini fallback adapters, and evidence-verification
tests—without publishing any review comment automatically.
