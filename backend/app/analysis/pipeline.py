from app.analysis.deterministic import (
    DeterministicCandidate,
    analyze_added_lines,
    verify_candidates,
)
from app.analysis.unified_diff import added_lines_from_patch
from app.integrations.github_public import PublicPullRequestFile


def analyze_patched_files(
    files: list[PublicPullRequestFile],
) -> list[DeterministicCandidate]:
    """Analyze supplied diff patches only; never read or execute repository content."""
    findings: list[DeterministicCandidate] = []
    for file in files:
        if file.patch is None:
            continue
        added_lines = added_lines_from_patch(file.path, file.patch)
        findings.extend(
            verify_candidates(
                added_lines,
                analyze_added_lines(file.path, added_lines),
            )
        )
    return findings
