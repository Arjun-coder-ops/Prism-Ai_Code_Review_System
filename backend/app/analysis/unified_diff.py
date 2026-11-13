import re
from dataclasses import dataclass

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class AddedLine:
    number: int
    text: str


def added_lines_from_patch(file_path: str, patch: str) -> list[AddedLine]:
    """Map added unified-diff lines to their new-file line numbers.

    `file_path` is intentionally accepted by this boundary for callers to keep
    source provenance explicit; parsing never reads or executes repository files.
    """
    del file_path
    added_lines: list[AddedLine] = []
    new_line_number: int | None = None
    for raw_line in patch.splitlines():
        hunk_match = _HUNK_HEADER.match(raw_line)
        if hunk_match is not None:
            new_line_number = int(hunk_match.group(1))
            continue
        if new_line_number is None or raw_line.startswith("\\"):
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            added_lines.append(AddedLine(number=new_line_number, text=raw_line[1:]))
            new_line_number += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        else:
            new_line_number += 1
    return added_lines
