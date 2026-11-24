"""The G1-G22 rule table and the runner that applies every check.

Single purpose: be the one list of rules (README text, severities) and the one
place that decides which check functions run, offline and online.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from .checks import fields, hygiene, layout, links, questions, syllabus, topics, xrefs
from .model import Finding, Repo
from .schema import check_g03_schema

BASE_REF_VARIABLE = "GATE_BASE_REF"


@dataclass(frozen=True)
class Rule:
    """One validation rule as documented in spec section 7."""

    rule_id: str
    severity: str
    text: str


RULES: tuple[Rule, ...] = (
    Rule("G1", "error", "Only `topics/*.md` and `questions/*.yaml` in the content folders; filename = slug; slug format and patterns"),
    Rule("G2", "error", "Slugs are unique across kinds and are not a redirect key; redirects are well formed"),
    Rule("G3", "error", "Front matter / YAML passes its JSON Schema; unknown keys only with an `x_` prefix"),
    Rule("G4", "error", "Only the link fields of the relation table are used, each on its own kind"),
    Rule("G5", "error", "Link targets exist and are the right kind (resolving through a redirect is a warning)"),
    Rule("G6", "error", "No cycles in `prerequisites`; no self-links"),
    Rule("G7", "error", "A `related` pair is not stored in both files"),
    Rule("G8", "error", "No duplicate entries in any list"),
    Rule("G9", "error", "Syllabus refs exist in the current `config/syllabus/*.json`"),
    Rule("G10", "error", "Syllabus files are valid; item IDs are unique slugs within a subject; every `source_url` is set"),
    Rule("G11", "error", "PYQ identity `(year, paper, session, number)` is unique and matches the slug; PYQs have `source_url`"),
    Rule("G12", "error", "Answer is consistent with type: mcq answer in options; msq a non-empty subset; nat `min <= max` with no options"),
    Rule("G13", "error", "Topic body has the exact section headings in order; Revision sheet at most 40 lines; no `TODO` left"),
    Rule("G14", "warning", "Two topics list the same syllabus item: possible duplicate topic"),
    Rule("G15", "warning", "Topic title similarity >= 0.85, or a title that equals another topic's slug"),
    Rule("G16", "warning", "Two generated questions on one topic with stem similarity >= 0.90"),
    Rule("G17", "error", "Old `attempts` entries are never changed or removed (compared with `HEAD`, or `GATE_BASE_REF` in CI); new entries go last with non-decreasing dates"),
    Rule("G18", "error", "`show_on` and `tags` values come from config"),
    Rule("G19", "error", "Dates are valid and not in the future; `created <= updated`"),
    Rule("G20", "error", "`api/v1/` and the README rule list are up to date (`--check`)"),
    Rule("G21", "error offline / warning online", "`xrefs` format and alias (offline); target exists (online, CI only)"),
    Rule("G22", "error", "No secrets (gitleaks + Python scan); no content file over 1 MB"),
)

OFFLINE_CHECKS: tuple[Callable[[Repo], list[Finding]], ...] = (
    layout.check_g01_layout,
    layout.check_g02_unique_slugs,
    layout.check_redirects,
    check_g03_schema,
    links.check_g04_link_fields,
    links.check_g05_link_targets,
    links.check_g06_cycles_and_self_links,
    links.check_g07_symmetric_pairs,
    links.check_g08_duplicate_entries,
    syllabus.check_g09_syllabus_refs,
    syllabus.check_g10_syllabus_files,
    questions.check_g11_pyq_identity,
    questions.check_g12_answers,
    topics.check_g13_topic_body,
    topics.check_g14_shared_syllabus_items,
    topics.check_g15_look_alike_titles,
    questions.check_g16_look_alikes,
    fields.check_g18_allowed_values,
    fields.check_g19_dates,
    xrefs.check_g21_offline,
    hygiene.check_g22_secrets_and_size,
)


def _sorted(findings: list[Finding]) -> list[Finding]:
    """Order findings deterministically so output and the index never depend on check order."""
    return sorted(findings, key=lambda found: (found.file, found.rule, found.field, found.message))


def run_offline_checks(repo: Repo) -> list[Finding]:
    """Run every check that needs no network; return all findings, sorted.

    G17 also needs git history: it compares with `$GATE_BASE_REF` (default HEAD).
    """
    findings: list[Finding] = []
    for check in OFFLINE_CHECKS:
        findings.extend(check(repo))
    findings.extend(questions.check_g17_attempt_log(repo, os.environ.get(BASE_REF_VARIABLE, "HEAD")))
    return _sorted(findings)


def run_online_checks(repo: Repo, fetch: xrefs.Fetcher) -> list[Finding]:
    """Run the network checks (G21 online); every finding is a warning."""
    return _sorted(xrefs.check_g21_online(repo, fetch))


def render_rules_markdown() -> str:
    """Return the README rule list as Markdown, generated from RULES."""
    lines = ["| Rule | Severity | Check |", "| --- | --- | --- |"]
    lines.extend(f"| {rule.rule_id} | {rule.severity} | {rule.text} |" for rule in RULES)
    return "\n".join(lines)
