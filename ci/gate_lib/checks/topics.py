"""Topic rules: G13 (body structure), G14 (shared syllabus items), G15 (look-alike titles).

Single purpose: check the Markdown body of each topic and detect topics that
may duplicate each other.
"""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations

from ..model import Finding, Item, Repo, error, warning

REQUIRED_HEADINGS = (
    "Summary", "Intuition", "Definitions and theorems", "Formulas", "Worked examples",
    "Shortcuts", "Traps", "Revision sheet", "Connections", "Sources",
)
REVISION_MAX_LINES = 40
TITLE_SIMILARITY = 0.85
_TODO = re.compile(r"\bTODO\b")


def section_lines(body: str) -> list[tuple[str, list[str]]]:
    """Split a body into (heading, content lines) for each `## ` heading outside code fences.

    Text before the first heading is ignored; `###` follow-ups stay inside
    their section. Public because the generator reuses the split.
    """
    sections: list[tuple[str, list[str]]] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    return sections


def _trimmed_length(lines: list[str]) -> int:
    """Count a section's lines after dropping blank lines at both ends."""
    text = "\n".join(lines).strip("\n")
    return len(text.splitlines()) if text.strip() else 0


def _body_problems(item: Item) -> list[str]:
    """List G13 problems for one topic body: headings, revision length, TODO."""
    sections = section_lines(item.body)
    problems = []
    if [name for name, _ in sections] != list(REQUIRED_HEADINGS):
        problems.append("body must have exactly these '## ' headings in order: " + ", ".join(REQUIRED_HEADINGS))
    for name, lines in sections:
        if name == "Revision sheet" and _trimmed_length(lines) > REVISION_MAX_LINES:
            problems.append(f"Revision sheet is longer than {REVISION_MAX_LINES} lines")
    if _TODO.search(item.body):
        problems.append("a TODO is left in the body")
    return problems


def check_g13_topic_body(repo: Repo) -> list[Finding]:
    """G13: exact headings in order, short revision sheet, no TODO."""
    return [
        error("G13", item.path, "body", problem, (item.slug,))
        for item in repo.items_of("topic") for problem in _body_problems(item)
    ]


def check_g14_shared_syllabus_items(repo: Repo) -> list[Finding]:
    """G14 (warning): two topics list the same syllabus item, a possible duplicate topic."""
    owners: dict[str, list[Item]] = defaultdict(list)
    for item in repo.items_of("topic"):
        for reference in set(item.values("syllabus")):
            owners[reference].append(item)
    return [
        warning("G14", second.path, "syllabus", f"'{reference}' is also listed by '{first.slug}': possible duplicate topic", (first.slug, second.slug))
        for reference, items in sorted(owners.items())
        for first, second in combinations(sorted(items, key=lambda found: found.slug), 2)
    ]


def _normalize(text: str) -> str:
    """Lowercase and keep only letters and digits separated by single spaces."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def check_g15_look_alike_titles(repo: Repo) -> list[Finding]:
    """G15 (warning): similar topic titles, or a title that equals another topic's slug.

    The spec says "alias clash" but topics have no alias field; a title that
    spells another topic's slug is the closest meaningful clash (DECISIONS 6).
    """
    topics = repo.items_of("topic")
    findings = []
    for first, second in combinations(topics, 2):
        titles = (_normalize(str(first.data.get("title", ""))), _normalize(str(second.data.get("title", ""))))
        clash = titles[0] == _normalize(second.slug) or titles[1] == _normalize(first.slug)
        if clash or SequenceMatcher(None, *titles).ratio() >= TITLE_SIMILARITY:
            findings.append(warning("G15", second.path, "title", f"title is very close to '{first.slug}'", (first.slug, second.slug)))
    return findings
