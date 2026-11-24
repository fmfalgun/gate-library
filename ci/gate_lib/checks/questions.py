"""Question rules: G11 (PYQ identity), G12 (answer consistency), G16 (look-alikes), G17 (attempt log).

Single purpose: keep every question internally consistent and its attempt
history append-only.
"""

from __future__ import annotations

import json
import subprocess
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from ..model import Finding, Item, Repo, error, warning
from ..parse import ContentError, load_yaml_mapping
from .fields import parse_date

STEM_SIMILARITY = 0.90


def _expected_pyq_slug(exam: dict) -> str | None:
    """Return the slug an exam identity implies, or None when the identity is incomplete."""
    try:
        return f"gate-{int(exam['year'])}-{exam['paper']}-s{int(exam['session'])}-q{int(exam['number']):02d}"
    except (KeyError, TypeError, ValueError):
        return None


def _pyq_problems(item: Item) -> list[tuple[str, str]]:
    """List (field, message) G11 problems for one PYQ: missing exam/source_url, slug mismatch."""
    problems = []
    if not item.data.get("source_url"):
        problems.append(("source_url", "a PYQ needs source_url (the official paper or answer key)"))
    exam = item.data.get("exam")
    if not isinstance(exam, dict):
        return problems + [("exam", "a PYQ needs exam {year, paper, session, number}")]
    expected = _expected_pyq_slug(exam)
    if expected is None or expected != item.slug:
        problems.append(("exam", f"exam identity does not match the slug (expected '{expected}')"))
    return problems


def _exam_identity(item: Item) -> tuple | None:
    """Return (year, paper, session, number) of a PYQ, or None when it has no usable exam block."""
    exam = item.data.get("exam")
    keys = ("year", "paper", "session", "number")
    return tuple(exam.get(key) for key in keys) if isinstance(exam, dict) and all(key in exam for key in keys) else None


def check_g11_pyq_identity(repo: Repo) -> list[Finding]:
    """G11: PYQ identity matches the slug and is unique; PYQs have source_url."""
    pyqs = [item for item in repo.items_of("question") if item.data.get("origin") == "pyq"]
    findings = [
        error("G11", item.path, name, message, (item.slug,))
        for item in pyqs for name, message in _pyq_problems(item)
    ]
    seen: dict[tuple, str] = {}
    for item in pyqs:
        identity = _exam_identity(item)
        if identity is not None and identity in seen:
            findings.append(error("G11", item.path, "exam", f"same exam question as '{seen[identity]}'", (item.slug,)))
        elif identity is not None:
            seen[identity] = item.slug
    return findings


def _answer_problem(item: Item) -> str | None:
    """Return what is inconsistent between a question's type, options and answer, or None."""
    kind, options, answer = item.data.get("type"), item.data.get("options"), item.data.get("answer")
    keys = set(options) if isinstance(options, dict) else set()
    if kind == "nat":
        return _nat_problem(options, answer)
    if kind not in ("mcq", "msq"):
        return None
    if not keys:
        return f"a {kind} question needs options"
    if kind == "mcq":
        return None if isinstance(answer, str) and answer in keys else "mcq answer must be one option key"
    valid = isinstance(answer, list) and answer and all(isinstance(a, str) for a in answer)
    return None if valid and set(answer) <= keys and len(set(answer)) == len(answer) else "msq answer must be a non-empty, duplicate-free subset of the option keys"


def _nat_problem(options: object, answer: object) -> str | None:
    """Return the problem with a NAT question's options/answer, or None."""
    if options:
        return "a nat question must not have options"
    if not isinstance(answer, dict) or not {"min", "max"} <= set(answer):
        return "nat answer must be {min, max}"
    low, high = answer["min"], answer["max"]
    numbers = all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in (low, high))
    return None if numbers and low <= high else "nat answer needs numeric min <= max"


def check_g12_answers(repo: Repo) -> list[Finding]:
    """G12: the answer is consistent with the question type and its options."""
    found = ((item, _answer_problem(item)) for item in repo.items_of("question"))
    return [error("G12", item.path, "answer", problem, (item.slug,)) for item, problem in found if problem]


def check_g16_look_alikes(repo: Repo) -> list[Finding]:
    """G16 (warning): two generated questions on the same topic with near-identical stems."""
    generated = [item for item in repo.items_of("question") if item.data.get("origin") == "generated"]
    findings = []
    for first, second in combinations(generated, 2):
        shared = set(first.values("topics")) & set(second.values("topics"))
        stems = (str(first.data.get("stem", "")), str(second.data.get("stem", "")))
        if shared and SequenceMatcher(None, *stems).ratio() >= STEM_SIMILARITY:
            findings.append(warning("G16", second.path, "stem", f"stem is very close to '{first.slug}'", (first.slug, second.slug)))
    return findings


def _attempt_order_problem(attempts: list) -> str | None:
    """Return a problem when attempt dates go backwards, or None (G17, file-internal part)."""
    dates = [parse_date(entry.get("date")) if isinstance(entry, dict) else None for entry in attempts]
    known = [when for when in dates if when is not None]
    return "attempt dates must not go backwards" if known != sorted(known) else None


def _committed_attempts(root: Path, path: str, ref: str) -> list | None:
    """Return the attempts list stored at `ref` for `path`, or None when it cannot be read.

    None covers: not a git repo, ref unknown (first commit), file new at ref,
    or unreadable content. Only a readable, older list can be compared.
    """
    if not (root / ".git").exists():
        return None
    done = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{path}"], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        return None
    try:
        attempts = load_yaml_mapping(done.stdout).get("attempts") or []
    except ContentError:
        return None
    return attempts if isinstance(attempts, list) else None


def check_g17_attempt_log(repo: Repo, base_ref: str = "HEAD") -> list[Finding]:
    """G17: attempts are append-only, new entries are last, and dates never go backwards.

    Compares each question with its version at `base_ref` (HEAD in the
    pre-commit hook; the push or PR base in CI).
    """
    findings = []
    for item in repo.items_of("question"):
        attempts = item.data.get("attempts") or []
        if not isinstance(attempts, list):
            continue
        problem = _attempt_order_problem(attempts)
        old = _committed_attempts(repo.root, item.path, base_ref)
        if problem is None and old is not None and attempts[:len(old)] != old:
            problem = "an earlier attempts entry was changed or removed (attempts are append-only)"
        if problem:
            findings.append(error("G17", item.path, "attempts", problem, (item.slug,)))
    return findings
