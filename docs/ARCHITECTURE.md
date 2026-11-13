# Architecture

## Initial Shape

PRISM is a modular monolith with a FastAPI API service, PostgreSQL durable
state, Redis-backed Celery workers, and a React dashboard. Modules communicate
through typed interfaces and persisted review state, not direct cross-layer
access.

```text
PR URL / GitHub webhook → FastAPI → PostgreSQL event/review record → queue
→ worker → diff/context retrieval → deterministic analysis → AI candidates
→ evidence verification → ranked findings → dashboard → human approval
→ GitHub publication
```

## Persistence and Provider Configuration

PostgreSQL access is asynchronous through SQLAlchemy and versioned Alembic
migrations. `DATABASE_URL` is the pooled application connection; Neon users
set `DIRECT_DATABASE_URL` to a direct connection for migrations. The URL
adapter translates Neon/libpq TLS query parameters safely for `asyncpg`.
No schema is created automatically at API startup.

The AI boundary uses provider adapters and structured outputs. Groq is the
intended primary provider; Gemini is an explicit fallback only when the primary
provider is unavailable or fails under the configured policy. Neither provider
can create a finding without deterministic context and evidence verification.

## Boundaries

- **API:** auth, input validation, status and findings retrieval; handlers are
  thin and delegate to services.
- **GitHub integration:** allowlisted API access, pagination, rate limits, and
  later token handling and publication. Public diff retrieval uses only the
  fixed GitHub REST path, bounded to GitHub's 3,000-file API limit; unsafe
  paths and malformed upstream metadata are rejected.
- **Analysis:** parses diffs and normalizes deterministic analyzer output; it
  never executes repository code. The first narrow rules flag only added
  `subprocess(..., shell=True)` and `eval(...)` lines, then retain a candidate
  only when its claimed line and exact evidence still match the unified diff.
- **AI:** provider interface, structured outputs, versioned prompts, and usage
  telemetry. Groq is primary and Gemini is fallback; it receives bounded,
  redacted context.
- **Verification:** validates SHA, file, line range, diff relevance, evidence,
  deduplication, and abstention rules.
- **Workers:** own state transitions, retries, idempotency, cancellation, and
  stale-commit checks.

Review states are `queued`, `fetching`, `indexing`, `static_analyzing`,
`ai_analyzing`, `verifying`, `awaiting_approval`, `publishing`, `completed`,
`failed`, `canceled`, and `stale`. Only documented transitions are allowed.
