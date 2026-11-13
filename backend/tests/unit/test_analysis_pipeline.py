from app.analysis.pipeline import analyze_patched_files
from app.integrations.github_public import PublicPullRequestFile


def test_returns_only_evidence_verified_candidates_from_patched_files() -> None:
    findings = analyze_patched_files(
        [
            PublicPullRequestFile(
                path="src/task.py",
                status="modified",
                patch="@@ -1 +1 @@\n+subprocess.run(command, shell=True)\n",
            ),
            PublicPullRequestFile(path="README.md", status="modified", patch=None),
        ]
    )

    assert len(findings) == 1
    assert findings[0].file_path == "src/task.py"
    assert findings[0].line_number == 1
