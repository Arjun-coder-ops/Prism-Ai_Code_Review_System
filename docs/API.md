# Initial API Contract

All endpoints return typed JSON and use a stable error envelope with a machine
readable code and safe human message. `/health`, `/ready`, and review intake
are implemented; retrieval and approval endpoints remain planned.

| Method and path | Purpose | Success |
| --- | --- | --- |
| `GET /health` | Process liveness, no dependency check | `200 {"status":"ok"}` |
| `GET /ready` | Readiness, including configured dependencies | `200` ready; `503` otherwise |
| `POST /api/v1/reviews` | Validate a canonical public GitHub PR URL, retrieve fixed-source metadata, and queue an idempotent review run | `202` with review ID and head SHA |
| `GET /api/v1/reviews/{id}` | Retrieve state, coverage, and findings | `200` review representation |
| `POST /api/v1/reviews/{id}/approve-publication` | Record a human approval | `202` only for a current review |

`POST /api/v1/reviews` accepts `{ "pull_request_url": "https://github.com/owner/repo/pull/123" }`.
It rejects unsupported,
credential-bearing, query-bearing, and noncanonical URLs before network access.
The GitHub adapter calls only the fixed public pull-request endpoint, never a
URL supplied by repository content. Findings include a
commit-pinned file path, start/end line, category, severity, confidence,
evidence, recommendation, and verification status. Publication endpoints must
not publish without a separately verified, explicit approval.
