import re
from dataclasses import dataclass

from app.analysis.unified_diff import AddedLine

_SHELL_TRUE = re.compile(
    r"\bsubprocess\.(?:call|check_call|check_output|Popen|run)\([^\n]*"
    r"\bshell\s*=\s*True\b"
)
_DYNAMIC_EVAL = re.compile(r"\beval\s*\(")


@dataclass(frozen=True)
class DeterministicCandidate:
    file_path: str
    line_number: int
    category: str
    severity: str
    title: str
    explanation: str
    evidence: str


def analyze_added_lines(
    file_path: str,
    added_lines: list[AddedLine],
) -> list[DeterministicCandidate]:
    """Return narrow candidates from added lines; do not infer beyond evidence."""
    candidates: list[DeterministicCandidate] = []
    for line in added_lines:
        if _SHELL_TRUE.search(line.text):
            candidates.append(
                DeterministicCandidate(
                    file_path=file_path,
                    line_number=line.number,
                    category="command-injection",
                    severity="high",
                    title="Shell command execution added",
                    explanation="The added subprocess call enables shell parsing.",
                    evidence=line.text,
                )
            )
        elif _DYNAMIC_EVAL.search(line.text):
            candidates.append(
                DeterministicCandidate(
                    file_path=file_path,
                    line_number=line.number,
                    category="dynamic-code-execution",
                    severity="high",
                    title="Dynamic evaluation added",
                    explanation=(
                        "The added eval call executes dynamically supplied code."
                    ),
                    evidence=line.text,
                )
            )
    return candidates


def verify_candidates(
    added_lines: list[AddedLine],
    candidates: list[DeterministicCandidate],
) -> list[DeterministicCandidate]:
    """Return only candidates whose claimed line and evidence match the diff."""
    line_by_number = {line.number: line.text for line in added_lines}
    return [
        candidate
        for candidate in candidates
        if line_by_number.get(candidate.line_number) == candidate.evidence
    ]
