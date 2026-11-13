# Testing Strategy

Use deterministic, isolated tests by default. Do not require live GitHub,
LLM, database, Redis, or Docker credentials for ordinary unit tests.

| Layer | Focus | Examples |
| --- | --- | --- |
| Unit | Pure parsing, validation, state transition, and evidence logic | invalid URL rejection; line-range validation |
| Integration | API, persistence, worker, and provider boundaries | idempotent review creation; stale SHA handling |
| Security | Trust boundaries and abuse cases | bad webhook signature; SSRF-shaped URL rejection |
| Frontend | User-visible state and accessibility | skipped-file coverage; approval disabled by default |
| Evaluation | Precision, recall, evidence validity, latency, cost | clean PR produces no unsupported finding |

Each regression receives a focused test. Fixtures must be minimal, synthetic
where practical, and free of secrets. Report exact commands and observed
results in `docs/STATUS.md`; no test is considered passed until executed.
