# Initial Decisions

These decisions are accepted for the first implementation because they are
specified by the project brief. Revisit them only through a documented,
reviewed change.

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| Modular monolith with workers | Keeps an MVP deployable and testable while isolating slow review work. | Modules need disciplined boundaries before a service split is justified. |
| FastAPI, PostgreSQL, Redis, Celery | Typed Python APIs, relational review state, and durable async work fit the workflow. | Requires multiple local services. |
| Database-claimed review runs | A conditional PostgreSQL claim plus a bounded lease makes duplicate delivery idempotent and lets interrupted workers recover. | A live run is intentionally not re-claimed until its lease expires. |
| Minimal webhook delivery ledger | Store a delivery ID, event metadata, digest, and processing state—not raw webhook payloads—to make signed delivery handling idempotent without retaining unnecessary source or user data. | Event handlers must retrieve their needed data from the validated payload before persistence. |
| React, TypeScript, Vite | Enables a typed, responsive review dashboard without framework-specific backend coupling. | Requires a separate frontend build. |
| Deterministic-first, verified AI | Prevents unsupported LLM claims from becoming findings. | More pipeline steps and fewer speculative warnings. |
| Groq primary, Gemini fallback | Meets the approved provider priority while retaining a bounded fallback path. | Adapters, outage handling, and provider-specific evaluation are required. |
| Neon-compatible PostgreSQL | Hosted PostgreSQL can serve durable state while retaining a local Compose equivalent. | Pooled app URLs and direct migration URLs must remain separate. |
| Human-gated publication | Review comments affect collaborators and must remain accountable. | Publication is not fully automatic. |
| GitHub App tokens, later | Supports least-privilege authorization. | App setup is an external prerequisite. |

Formal ADRs are proposed for future decisions that materially change these
boundaries, providers, persistence, deployment, or security model.
