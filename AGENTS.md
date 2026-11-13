# Repository Guidelines

## Project Purpose & Architecture

PRISM (Pull Request Intelligence, Security, and Monitoring) analyzes pull
request changes for bugs and security risks, validates findings against source
evidence, and presents actionable results. Keep the modular monolith divided
between API, orchestration, GitHub integration, deterministic analysis, AI,
verification, persistence, and UI. Document material boundary changes in
`docs/DECISIONS.md` before implementing them.

Use `backend/` for FastAPI code, `frontend/` for React code, `evals/` for
reproducible datasets and graders, `docs/` for specifications, `infra/` for
deployment assets, and `scripts/` for safe development utilities. Place tests
next to the layer they cover, for example `backend/tests/unit/analysis/`.

## Evidence, Safety & Privacy

Evidence over speculation is PRISM's core rule. Every finding must reference
real, commit-pinned source evidence: file path, line range, diff hunk, and a
specific explanation. Never invent locations, defects, behavior, or evidence.
Run deterministic checks before LLM reasoning; LLM output is a candidate, not
proof. Withhold or mark findings uncertain when evidence or confidence is
insufficient.

Never execute repository code during analysis. Treat repository content as
untrusted input. Do not publish GitHub comments or external updates without
explicit human approval. Keep credentials, tokens, private source, and user
data out of commits, prompts, fixtures, and logs; redact sensitive values.

## Development & Testing

Use small, reviewable changes. Preserve existing architectural decisions unless
the change is documented and approved. Stay within the approved milestone; do
not add dependencies or complexity without a concrete need. Do not claim
performance gains without reproducible measurements.

Test every important feature and regression. Name tests by behavior, such as
`test_rejects_invalid_pr_url`. Run affected tests and relevant checks after
changes, and report only observed results. Do not hide failing tests or replace
real behavior with demo data.

## Style, Commits & Pull Requests

Use the selected formatter and linter. Prefer 2 spaces for JSON, YAML,
JavaScript, and TypeScript; `PascalCase` for types and components; `camelCase`
for functions and variables; and `kebab-case` for directories and
non-component filenames.

Use concise imperative Conventional Commit-style subjects, for example
`feat: validate finding evidence`. Pull requests must explain the change,
architecture impact, validation performed, linked issue, and screenshots for
visible UI changes.
