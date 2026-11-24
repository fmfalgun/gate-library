"""Syllabus rules: G9 (topic references exist) and G10 (syllabus files are valid).

Single purpose: keep the syllabus data well formed and make sure every topic
points at a syllabus item that really exists in the current syllabus files.
"""

from __future__ import annotations

import re
from collections import Counter

from ..model import SLUG_MAX_LENGTH, SLUG_PATTERN, Finding, Repo, error, syllabus_ref_parts
from ..schema import field_label, load_validators


def syllabus_item_ids(repo: Repo) -> set[tuple[str, str, str]]:
    """Return every (paper, subject-id, item-id) in the current syllabus files.

    Malformed files are tolerated (missing keys are skipped): G10 reports them.
    """
    found = set()
    for paper, data in repo.config.syllabi.items():
        for subject in data.get("subjects", []) if isinstance(data.get("subjects"), list) else []:
            for entry in subject.get("items", []) if isinstance(subject, dict) and isinstance(subject.get("items"), list) else []:
                if isinstance(entry, dict) and isinstance(subject.get("id"), str) and isinstance(entry.get("id"), str):
                    found.add((paper, subject["id"], entry["id"]))
    return found


def check_g09_syllabus_refs(repo: Repo) -> list[Finding]:
    """G9: every `syllabus` entry of a topic is `<paper>:<subject>/<item>` and exists."""
    known = syllabus_item_ids(repo)
    findings = []
    for item in repo.items_of("topic"):
        for reference in item.values("syllabus"):
            parts = syllabus_ref_parts(reference)
            if parts is None:
                message = f"'{reference}' must look like <paper>:<subject-id>/<item-id>"
            elif parts not in known:
                message = f"'{reference}' is not in the current config/syllabus files"
            else:
                continue
            findings.append(error("G9", item.path, "syllabus", message, (item.slug,)))
    return findings


def _structure_problems(paper: str, data: dict) -> list[str]:
    """List problems the schema cannot express: paper/filename match, slug IDs, duplicate IDs."""
    problems = []
    if data.get("paper") != paper:
        problems.append(f"'paper' is '{data.get('paper')}' but the file is named {paper}.json")
    subjects = [entry for entry in data.get("subjects", []) if isinstance(entry, dict)] if isinstance(data.get("subjects"), list) else []
    for subject_id, count in Counter(entry.get("id") for entry in subjects).items():
        if count > 1:
            problems.append(f"subject id '{subject_id}' is used more than once")
    for subject in subjects:
        problems.extend(_item_id_problems(subject))
    return problems


def _item_id_problems(subject: dict) -> list[str]:
    """List item-ID problems inside one subject: not a slug, or repeated."""
    ids = [entry.get("id") for entry in subject.get("items", []) if isinstance(entry, dict)] if isinstance(subject.get("items"), list) else []
    problems = [
        f"item id '{item_id}' in '{subject.get('id')}' is not a valid slug"
        for item_id in ids if isinstance(item_id, str)
        and (not re.fullmatch(SLUG_PATTERN, item_id) or len(item_id) > SLUG_MAX_LENGTH)
    ]
    problems.extend(
        f"item id '{item_id}' is used more than once in '{subject.get('id')}'"
        for item_id, count in Counter(ids).items() if count > 1
    )
    return problems


def check_g10_syllabus_files(repo: Repo) -> list[Finding]:
    """G10: syllabus files pass their schema, IDs are unique slugs, every source_url is set."""
    validator = load_validators(repo.root)["syllabus"]
    findings = []
    for paper, data in sorted(repo.config.syllabi.items()):
        file = f"config/syllabus/{paper}.json"
        findings.extend(error("G10", file, field_label(found), found.message) for found in validator.iter_errors(data))
        findings.extend(error("G10", file, "", problem) for problem in _structure_problems(paper, data))
    return findings
