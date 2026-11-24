"""Repository hygiene rule G22: no secrets in content, no oversized content files.

Single purpose: scan the content-bearing folders for secret-looking text and
files over 1 MB. gitleaks in the pre-commit hook is the second line of defence.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Finding, Repo, error

MAX_CONTENT_BYTES = 1_000_000
_SIZE_LIMITED = ("topics", "questions")
_SCANNED = (*_SIZE_LIMITED, "config", "docs", "templates")

# Each pattern is a named secret shape. Kept short and conservative: the
# hook's gitleaks run covers the long tail.
_SECRET_PATTERNS = {
    "private key header": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "assigned secret": re.compile(r"(?i)\b(api[_-]?key|secret|token|passw(or)?d)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_\-]{16,}"),
}


def _files_under(root: Path, folders: tuple[str, ...]) -> list[Path]:
    """List every file below the given top-level folders, sorted, skipping missing folders."""
    found: list[Path] = []
    for folder in folders:
        base = root / folder
        if base.is_dir():
            found.extend(sorted(path for path in base.rglob("*") if path.is_file()))
    return found


def _secret_findings(root: Path, path: Path) -> list[Finding]:
    """G22 findings for one file's secret-looking text (the matched text is never echoed)."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    relative = path.relative_to(root).as_posix()
    return [
        error("G22", relative, "", f"looks like a secret ({name}); remove it and rotate the credential")
        for name, pattern in _SECRET_PATTERNS.items() if pattern.search(text)
    ]


def check_g22_secrets_and_size(repo: Repo) -> list[Finding]:
    """G22: no secret-looking text in scanned folders; no content file over 1 MB."""
    findings: list[Finding] = []
    for path in _files_under(repo.root, _SCANNED):
        findings.extend(_secret_findings(repo.root, path))
    for path in _files_under(repo.root, _SIZE_LIMITED):
        if path.stat().st_size > MAX_CONTENT_BYTES:
            findings.append(error("G22", path.relative_to(repo.root).as_posix(), "", "file is over 1 MB"))
    return findings
