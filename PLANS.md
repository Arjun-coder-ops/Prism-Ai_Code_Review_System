# PRISM Execution Plan

## Operating Rules

Follow **inspect → plan → acceptance criteria → implement → test → review →
fix → verify → document → handoff**. Milestones are not complete without
recorded, executed verification. External publication, deployment, purchases,
destructive operations, and credential use require explicit approval.

## Milestone 0 — Foundation

**Goal:** a reproducible local foundation for a safe, evidence-driven review
system.

| Workstream | Scope | Acceptance criteria |
| --- | --- | --- |
| Documentation | Requirements, API, architecture, security, tests, evaluation, and status | Documents distinguish planned from verified work. |
| Backend | FastAPI configuration, health/readiness endpoints, typed schemas, tests | Service starts; health tests pass without external credentials. |
| Frontend | Vite React shell with a non-fabricated status view | Build and component tests pass. |
| Local services | Compose definitions for PostgreSQL and Redis | Configuration is documented; Compose is verified only if run. |
| CI | Formatting, linting, type checking, tests, and builds | Workflow is committed; execution status is recorded. |

Dependencies: a supported Python and Node runtime, package installation access,
and optionally Docker. No GitHub or LLM credentials are required for fixture
based Milestone 0 verification.

**Progress:** complete and locally verified. The Python runtime is aligned to
3.12 in Docker and CI. The initial Alembic migration is applied locally;
PostgreSQL, Redis, `/health`, `/ready`, and the frontend endpoint have been
observed healthy. `DATABASE_URL` serves application traffic and
`DIRECT_DATABASE_URL` serves migrations.

## Subsequent Milestones

1. Public PR analysis MVP — complete locally.
2. Durable asynchronous review engine — complete locally.
3. GitHub App and signed webhooks.
4. Hybrid analysis, evidence verification, and human-approved publication.
5. Repository and test intelligence.
6. Evaluation, hardening, UI polish, and deployment readiness.

Credentialed LLM checks remain pending; Groq remains primary and Gemini the
bounded fallback. Deterministic analysis is the required first stage.

### Milestone 1 progress — public review intake (in progress)

- Implemented strict canonical GitHub PR URL validation before network access.
- Implemented fixed-base public GitHub metadata retrieval and idempotent queued
  review-run persistence. It uses no repository clone or execution path.
- Implemented initial deterministic unified-diff analysis and exact-evidence
  verification for narrowly defined dynamic-execution patterns.
- Implemented bounded public GitHub changed-file pagination and a pipeline that
  analyzes only supplied patch text; missing patches abstain rather than cause
  source retrieval or execution.
- Implemented Groq-primary/Gemini-fallback JSON provider adapters and
  deterministic failover tests. Live provider connectivity remains blocked on
  unconfigured credentials.
- The status endpoint and polling frontend expose only persisted findings;
  external review publication remains deliberately absent.

### Milestone 2 progress — durable asynchronous review engine (complete locally)

- Celery tasks use JSON serialization, late acknowledgement, one-task prefetch,
  bounded exponential retry, and a dedicated `prism.review` queue.
- PostgreSQL conditionally claims a review run and recovers stale in-progress
  leases, preventing duplicate concurrent processors from persisting duplicate
  findings.
- Permanent upstream failures are stored as failed runs; only unavailable
  GitHub service errors retry. Completed runs are idempotent.
- Compose-backed integration tests verify state persistence, concurrency,
  recovery, and failure classification. A real public GitHub PR completed
  through the local stack without source execution or comment publication.
