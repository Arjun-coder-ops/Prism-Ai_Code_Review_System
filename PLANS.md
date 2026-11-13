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

**Progress:** documentation, source scaffolding, dependency locks, static
checks, frontend checks, and local Compose runtime validation are complete.
The reviewed initial Alembic migration was applied to the local PostgreSQL
volume; Redis, `/health`, `/ready`, and the frontend endpoint were observed
healthy. A Neon-compatible async persistence boundary is included, using
`DATABASE_URL` for application traffic and `DIRECT_DATABASE_URL` for
migrations. Full current-suite host testing remains unverified because Python
3.15's async event-loop setup hangs before async tests execute; see
`docs/STATUS.md`.

## Subsequent Milestones

1. Public PR analysis MVP.
2. Durable asynchronous review engine.
3. GitHub App and signed webhooks.
4. Hybrid analysis, evidence verification, and human-approved publication.
5. Repository and test intelligence.
6. Evaluation, hardening, UI polish, and deployment readiness.

Milestone 1 implementation remains pending the documented verification gap and
the required GitHub/LLM credentials; Groq will be primary and Gemini fallback.

### Milestone 1 progress — public review intake (in progress)

- Implemented strict canonical GitHub PR URL validation before network access.
- Implemented fixed-base public GitHub metadata retrieval and idempotent queued
  review-run persistence. It uses no repository clone or execution path.
- Implemented initial deterministic unified-diff analysis and exact-evidence
  verification for narrowly defined dynamic-execution patterns.
- Deferred: public file pagination, durable worker dispatch, finding
  persistence, UI presentation, LLM provider adapter, and any publication.
