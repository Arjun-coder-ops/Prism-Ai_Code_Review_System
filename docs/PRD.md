# PRISM Product Requirements

## Problem and Users

PRISM helps GitHub developers and maintainers assess pull-request risk before
merge. It should identify plausible correctness, security, reliability, and
test-coverage issues without manufacturing feedback on clean changes.

## MVP Scope

Milestone 1 accepts a correctly formed public GitHub pull-request URL,
retrieves permitted PR metadata and changed files, parses diffs, runs safe
deterministic checks, and displays structured candidate findings. Findings are
persisted against the reviewed head SHA and are displayed only after line and
evidence validation. A deterministic fake AI provider supports reproducible
tests; live provider access is optional and explicit.

## Requirements

- Reject malformed, unsupported, and non-GitHub URLs before any network call.
- Analyze only supported text files within explicit size, file-count, and
  context limits; report skipped coverage.
- Link every finding to a valid changed file and source location at one commit.
- Withhold findings lacking sufficient source evidence or confidence.
- Keep review completion separate from GitHub publication; a person must
  approve publication.
- Never execute code retrieved from an analyzed repository.

## Non-Goals

The MVP does not merge PRs, guarantee correctness, execute untrusted code,
support all languages, provide payments, or claim autonomous review authority.
