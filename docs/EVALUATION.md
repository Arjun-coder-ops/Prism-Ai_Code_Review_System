# Evaluation Plan

PRISM quality is measured with versioned fixtures and ground-truth annotations,
not anecdotes. The initial dataset must include correctness and security
regressions, clean pull requests, unsupported candidate findings, duplicate
events, stale revisions, worker failures, and missing-test scenarios.

Record pipeline version, fixture version, model identifier, policy version,
and execution environment for every evaluation run. Report precision, recall,
false-positive rate, valid-location rate, abstention rate, latency, and cost
with their definitions. Compare baseline and advanced pipelines only after
running the same fixture set. Do not claim model or performance improvements
without recorded measurements.
