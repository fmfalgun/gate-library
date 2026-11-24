"""Layout rules: G1 (files and slugs), G2 (unique slugs), redirect integrity.

Single purpose: check that files are where and what their names say they are.
"""

from __future__ import annotations

import re
from collections import Counter

from ..model import SLUG_MAX_LENGTH, SLUG_PATTERN, Finding, Item, Repo, error

_PYQ_SLUG = re.compile(r"^gate-[0-9]{4}-[a-z0-9]+-s[0-9]+-q[0-9]{2,}$")
_GENERATED_SLUG = re.compile(r"^gen-[a-z0-9]+(-[a-z0-9]+)*-[0-9]{3}$")


def _question_pattern_problem(item: Item) -> str | None:
    """Return the problem with a question slug's pattern (spec section 2), or None."""
    origin = item.data.get("origin")
    if origin == "pyq" and not _PYQ_SLUG.match(item.stem):
        return "a PYQ slug must look like gate-<year>-<paper>-s<session>-q<nn>"
    if origin == "generated" and not _GENERATED_SLUG.match(item.stem):
        return "a generated question slug must look like gen-<topic-slug>-<nnn>"
    return None


def _stem_findings(item: Item) -> list[Finding]:
    """G1 findings for one item's filename: slug format, kind pattern, filename = slug field."""
    problems = []
    if not re.fullmatch(SLUG_PATTERN, item.stem) or len(item.stem) > SLUG_MAX_LENGTH:
        problems.append(f"filename '{item.stem}' is not a valid slug (a-z, 0-9, hyphens; max {SLUG_MAX_LENGTH})")
    if item.kind == "question":
        problems.append(_question_pattern_problem(item))
    declared = item.data.get("slug")
    if declared is not None and declared != item.stem:
        problems.append(f"front matter slug '{declared}' differs from the filename '{item.stem}'")
    return [error("G1", item.path, "slug", message, (item.slug,)) for message in problems if message]


def check_g01_layout(repo: Repo) -> list[Finding]:
    """G1: only `topics/*.md` and `questions/*.yaml`; filename equals slug; slug patterns."""
    findings = [
        error("G1", path, "", "not a plain file of the folder's kind (topics: .md, questions: .yaml): remove or move it")
        for path in repo.stray_paths
    ]
    for item in repo.items:
        findings.extend(_stem_findings(item))
    return findings


def check_g02_unique_slugs(repo: Repo) -> list[Finding]:
    """G2: slugs are unique across kinds, and none equals a redirect source."""
    counts = Counter(item.slug for item in repo.items)
    findings = []
    for item in repo.items:
        if counts[item.slug] > 1:
            findings.append(error("G2", item.path, "slug", f"slug '{item.slug}' is used by more than one file", (item.slug,)))
        if item.slug in repo.config.redirects:
            findings.append(error("G2", item.path, "slug", f"slug '{item.slug}' is also a key in config/redirects.json", (item.slug,)))
    return findings


def check_redirects(repo: Repo) -> list[Finding]:
    """G2 (redirect side): sources have no file, targets exist, no chains or loops."""
    findings = []
    for old, new in sorted(repo.config.redirects.items()):
        file = "config/redirects.json"
        if old in repo.by_slug:
            findings.append(error("G2", file, old, f"redirect source '{old}' still has a file"))
        if new not in repo.by_slug:
            findings.append(error("G2", file, old, f"redirect target '{new}' does not exist"))
        if new in repo.config.redirects:
            findings.append(error("G2", file, old, f"'{old}' -> '{new}' is a chain or loop; point '{old}' at the final slug"))
    return findings
