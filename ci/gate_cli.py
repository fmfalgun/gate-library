"""File-editing commands for gate-library: scaffold a new file, log a question attempt.

Single purpose: the two commands of sync_index.py that write content files
(--new and --attempt). Both only touch one file and never rewrite old text.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from gate_lib import parse
from gate_lib.model import KIND_FOLDERS, KIND_SUFFIXES, SLUG_MAX_LENGTH, SLUG_PATTERN

TEMPLATE_KINDS = ("topic", "question-mcq", "question-msq", "question-nat")
RESULTS = ("right", "wrong", "skipped")
REASONS = ("concept", "calculation", "trap", "time", "misread")
_ATTEMPTS_LINE = re.compile(r"^attempts:\s*(\[\s*\])?\s*$")
_TOP_LEVEL = re.compile(r"^[A-Za-z_]")


def _today() -> str:
    """Return today's UTC date as YYYY-MM-DD (one clock for CI and laptops)."""
    return datetime.now(timezone.utc).date().isoformat()


def _topic_of_generated_slug(slug: str) -> str:
    """Return the topic slug inside a `gen-<topic>-<nnn>` slug, or a placeholder for other slugs."""
    match = re.fullmatch(r"gen-(.+)-[0-9]{3}", slug)
    return match.group(1) if match else "replace-with-topic-slug"


def _fill_template(root: Path, kind: str, slug: str) -> str:
    """Read <root>/templates/<kind> and fill {{slug}}, {{today}} and {{topic}}."""
    suffix = KIND_SUFFIXES["topic" if kind == "topic" else "question"]
    template = (root / "templates" / f"{kind}{suffix}").read_text(encoding="utf-8")
    filled = template.replace("{{slug}}", slug).replace("{{today}}", _today())
    return filled.replace("{{topic}}", _topic_of_generated_slug(slug))


def new_item(root: Path, kind: str, slug: str) -> int:
    """Create <folder>/<slug>.<ext> from the template. Returns 1 for a bad kind or slug, or if it exists."""
    if kind not in TEMPLATE_KINDS:
        print(f"kind must be one of: {', '.join(TEMPLATE_KINDS)}", file=sys.stderr)
        return 1
    if not re.fullmatch(SLUG_PATTERN, slug) or len(slug) > SLUG_MAX_LENGTH:
        print(f"'{slug}' is not a valid slug", file=sys.stderr)
        return 1
    repo = parse.load_repo(root)
    if slug in repo.by_slug or slug in repo.config.redirects:
        print(f"slug '{slug}' already exists (or is a redirect source)", file=sys.stderr)
        return 1
    base = "topic" if kind == "topic" else "question"
    target = root / KIND_FOLDERS[base] / f"{slug}{KIND_SUFFIXES[base]}"
    target.write_text(_fill_template(root, kind, slug), encoding="utf-8")
    print(f"created {target.relative_to(root)}")
    return 0


def _entry_lines(result: str, reason: str | None) -> list[str]:
    """Return the YAML lines of one attempts entry dated today."""
    lines = [f"  - date: {_today()}", f"    result: {result}"]
    return lines + ([f"    reason: {reason}"] if reason else [])


def _block_end(lines: list[str], start: int) -> int:
    """Return the index just after the last non-blank line of the block that starts at `start`."""
    end = start + 1
    for index in range(start + 1, len(lines)):
        if _TOP_LEVEL.match(lines[index]):
            break
        if lines[index].strip():
            end = index + 1
    return end


def _with_attempt(lines: list[str], entry: list[str]) -> list[str]:
    """Return the file's lines with `entry` appended to its attempts list (created if missing)."""
    for index, line in enumerate(lines):
        if _ATTEMPTS_LINE.match(line):
            end = _block_end(lines, index)
            head = ["attempts:"] if line.strip() != "attempts:" else [lines[index]]
            return lines[:index] + head + lines[index + 1:end] + entry + lines[end:]
    return lines + ["attempts:"] + entry


def _stamp_updated(lines: list[str]) -> list[str]:
    """Set the top-level `updated:` line to today so created <= updated keeps holding."""
    return [f"updated: {_today()}" if line.startswith("updated:") else line for line in lines]


def add_attempt(root: Path, slug: str, result: str, reason: str | None) -> int:
    """Append a dated attempt to a question file. Returns 1 for a bad argument or unknown question.

    Side effects: rewrites questions/<slug>.yaml with one new entry at the end
    of `attempts` and today's date in `updated`. Older text is untouched (G17).
    """
    path = root / KIND_FOLDERS["question"] / f"{slug}{KIND_SUFFIXES['question']}"
    problem = (
        f"result must be one of: {', '.join(RESULTS)}" if result not in RESULTS
        else f"reason must be one of: {', '.join(REASONS)}" if reason and reason not in REASONS
        else f"no question '{slug}'" if not path.is_file() else None
    )
    if problem:
        print(problem, file=sys.stderr)
        return 1
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(_stamp_updated(_with_attempt(lines, _entry_lines(result, reason)))) + "\n", encoding="utf-8")
    print(f"logged {result} for {slug}")
    return 0
