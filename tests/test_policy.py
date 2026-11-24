"""Rules that need git (G17), a network stub (G21 online) or run-time built files (G22).

Single purpose: prove the attempt log is append-only, online xref problems only
warn, and secrets or oversized files are caught. Fake secrets are assembled
here, never stored in fixture files, so they cannot trip gitleaks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import all_findings, load, make_repo, rule_ids
from gate_lib import rules
from gate_lib.checks import questions, xrefs

PYQ = "questions/gate-2024-cs-s2-q23.yaml"


def git(root: Path, *arguments: str) -> None:
    """Run a git command in `root` with a throwaway identity; raise on failure."""
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.org", *arguments],
                   check=True, capture_output=True)


def committed_repo(tmp_path: Path) -> Path:
    """Build the valid repo, commit it, and return its root (G17 compares against HEAD)."""
    root = make_repo(tmp_path)
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    return root


def g17_findings(root: Path):
    """Return only the G17 findings for the repo in its current state."""
    return [found for found in questions.check_g17_attempt_log(load(root))]


def test_g17_accepts_an_appended_attempt(tmp_path):
    """Adding a new, later entry at the end is allowed."""
    root = committed_repo(tmp_path)
    path = root / PYQ
    text = path.read_text().replace("    result: right\n", "    result: right\n  - date: 2026-11-08\n    result: skipped\n")
    path.write_text(text)
    assert g17_findings(root) == []


def test_g17_rejects_an_edited_old_attempt(tmp_path):
    """Changing an old entry fails G17 (acceptance check)."""
    root = committed_repo(tmp_path)
    path = root / PYQ
    path.write_text(path.read_text().replace("result: wrong", "result: right"))
    assert "G17" in rule_ids(g17_findings(root))


def test_g17_rejects_a_removed_attempt(tmp_path):
    """Dropping an old entry fails G17."""
    root = committed_repo(tmp_path)
    path = root / PYQ
    path.write_text(path.read_text().replace("  - date: 2026-11-02\n    result: wrong\n    reason: trap\n", ""))
    assert "G17" in rule_ids(g17_findings(root))


def test_g17_rejects_dates_going_backwards(tmp_path):
    """A new entry dated before the previous one fails G17 even without git history."""
    root = make_repo(tmp_path)
    path = root / PYQ
    path.write_text(path.read_text().replace("    result: right\n", "    result: right\n  - date: 2026-11-01\n    result: skipped\n"))
    assert "G17" in rule_ids(all_findings(root))


def test_g17_uses_the_base_ref_from_the_environment(tmp_path, monkeypatch):
    """GATE_BASE_REF decides what the log is compared with (CI passes the push or PR base)."""
    root = committed_repo(tmp_path)
    path = root / PYQ
    path.write_text(path.read_text().replace("result: wrong", "result: right"))
    git(root, "commit", "-q", "-am", "edit")
    monkeypatch.setenv(rules.BASE_REF_VARIABLE, "HEAD~1")
    assert "G17" in rule_ids(rules.run_offline_checks(load(root)))


def test_g17_skips_a_repo_without_history(tmp_path):
    """No .git directory (a fresh export) means nothing to compare with, so no error."""
    assert g17_findings(make_repo(tmp_path)) == []


def xref_repo(tmp_path: Path) -> Path:
    """Valid repo whose graph-basics topic has one dsa-library and one library-data xref."""
    root = make_repo(tmp_path)
    path = root / "topics/graph-basics.md"
    path.write_text(path.read_text().replace("status: learning", "xrefs:\n  - dsa-library:concepts/arrays\n  - library-data:tools/nmap\nstatus: learning"))
    return root


def test_g21_online_finds_both_repos_when_present(tmp_path):
    """No warning when the index lists the slug and the manifest lists the file."""
    pages = {"https://fmfalgun.github.io/dsa-library/api/v1/index.json": {"items": {"arrays": {}}},
             "https://fmfalgun.github.io/library-data/data/tools/manifest.json": ["nmap.json"]}
    assert xrefs.check_g21_online(load(xref_repo(tmp_path)), pages.__getitem__) == []


def test_g21_online_warns_when_missing_or_unreachable(tmp_path):
    """A missing target and an unreachable repo are both warnings, never errors."""
    def fetch(url):
        """Fake network: dsa-library answers without the slug, library-data is unreachable."""
        if "dsa-library" in url:
            return {"items": {}}
        raise OSError("offline")
    findings = xrefs.check_g21_online(load(xref_repo(tmp_path)), fetch)
    assert len(findings) == 2 and {found.severity for found in findings} == {"warning"}


def test_g21_offline_rejects_bad_shape(tmp_path):
    """An xref without <alias>:<folder>/<slug> shape is an offline error."""
    root = make_repo(tmp_path)
    path = root / "topics/graph-basics.md"
    path.write_text(path.read_text().replace("status: learning", "xrefs:\n  - just-a-word\nstatus: learning"))
    assert "G21" in rule_ids(all_findings(root), "error")


def test_g22_flags_a_secret_in_docs(tmp_path):
    """A secret-looking string in a scanned folder is an error; the match is never echoed."""
    root = make_repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "leak.md").write_text("key " + "AKIA" + "A" * 16 + "\n")
    findings = [found for found in all_findings(root) if found.rule == "G22"]
    assert findings and "AKIA" not in findings[0].message


def test_g22_flags_a_file_over_one_megabyte(tmp_path):
    """A content file over 1 MB is an error."""
    root = make_repo(tmp_path)
    path = root / "topics" / "graph-basics.md"
    path.write_text(path.read_text() + "x" * 1_000_001)
    assert any(found.rule == "G22" and "1 MB" in found.message for found in all_findings(root))
