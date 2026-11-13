# Security Boundaries

## Trust Model

PR URLs, webhook payloads, diffs, repository files, analyzer output, and LLM
output are untrusted. PRISM must not execute repository code or dereference
arbitrary URLs. Live GitHub access is limited to explicit GitHub API endpoints
and authorized repositories.

## Required Controls

- Parse only supported `https://github.com/{owner}/{repo}/pull/{number}` URLs.
- Verify GitHub webhook signatures over the raw request body using constant-time
  comparison; deduplicate persisted event identities.
- Use least-privilege GitHub App installation tokens and do not persist
  short-lived tokens unless justified by a secure design.
- Enforce input, file, diff, context, retry, and rate limits.
- Pin findings to a head SHA and revalidate before publication.
- Require explicit human approval before publishing a GitHub review comment.
- Keep secrets in environment configuration, redact logs, and never commit
  `.env` files or private repository contents.
- Treat `GROQ_API_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, and
  `DIRECT_DATABASE_URL` as secrets. Do not print them in diagnostics; use a
  pooled database URL for application traffic and a direct URL only for
  migrations.
- Retain only data necessary for review history and document deletion policy.

Security claims remain planned until an implementation and corresponding test
provide verification evidence.
