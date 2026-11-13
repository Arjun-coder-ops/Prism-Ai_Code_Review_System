from app.analysis.deterministic import analyze_added_lines, verify_candidates
from app.analysis.unified_diff import added_lines_from_patch


def test_maps_added_lines_to_their_new_file_locations() -> None:
    lines = added_lines_from_patch(
        "src/task.py",
        "@@ -10,2 +10,3 @@\n context\n-old\n+new\n+another\n",
    )

    assert [(line.number, line.text) for line in lines] == [
        (11, "new"),
        (12, "another"),
    ]


def test_emits_security_candidate_with_exact_added_line_evidence() -> None:
    lines = added_lines_from_patch(
        "src/task.py",
        "@@ -1 +1 @@\n+subprocess.run(command, shell=True)\n",
    )

    candidates = analyze_added_lines("src/task.py", lines)
    verified = verify_candidates(lines, candidates)

    assert len(verified) == 1
    assert verified[0].category == "command-injection"
    assert verified[0].line_number == 1
    assert verified[0].evidence == "subprocess.run(command, shell=True)"


def test_abstains_when_candidate_evidence_is_not_present_on_the_claimed_line() -> None:
    lines = added_lines_from_patch("src/task.py", "@@ -1 +1 @@\n+safe_call()\n")
    candidates = analyze_added_lines(
        "src/task.py",
        added_lines_from_patch("src/task.py", "@@ -1 +1 @@\n+eval(input())\n"),
    )

    assert verify_candidates(lines, candidates) == []
