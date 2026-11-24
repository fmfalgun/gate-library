"""Builds the generated outputs (api/v1/*, README rule list) deterministically.

Single purpose: turn a validated Repo into the exact text of every generated
file, compare it with what is on disk (rule G20), and write it. Output is
byte-stable: sorted keys, 2-space indent, trailing newline, no timestamps.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import coverage, graph
from .checks.xrefs import split_xref, xref_url
from .model import BASE_URL, KIND_FOLDERS, SCHEMA_VERSION, Finding, Item, Repo, error
from .rules import render_rules_markdown

API_DIR = "api/v1"
README_START = "<!-- rules:start -->"
README_END = "<!-- rules:end -->"
HASHED_PATTERNS = (("topics", "*.md"), ("questions", "*.yaml"), ("config", "*.json"), ("config/syllabus", "*.json"))

_TOPIC_FIELDS = ("title", "summary", "status", "confidence", "syllabus", "prerequisites", "related", "sources", "tags", "show_on", "created", "updated")
_QUESTION_FIELDS = ("origin", "exam", "source_url", "type", "marks", "topics", "stem", "options", "answer", "solution",
                    "fastest_method", "trap", "difficulty", "attempts", "show_on", "created", "updated")
_SORTED_LISTS = frozenset({"tags", "show_on", "syllabus", "prerequisites", "related", "topics"})
_DEFAULTS = {
    "tags": [], "prerequisites": [], "related": [], "sources": [], "attempts": [], "show_on": coverage.DEFAULT_SHOW_ON,
    "exam": None, "source_url": None, "options": None, "fastest_method": None, "trap": None, "difficulty": None,
}


def dumps(value: object) -> str:
    """Serialize to the repo's canonical JSON text (sorted keys, 2 spaces, final newline)."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def content_hash(root: Path) -> str:
    """SHA-256 over every content and config file: path and bytes, in path order."""
    paths = sorted(path for folder, pattern in HASHED_PATTERNS for path in (root / folder).glob(pattern) if path.is_file())
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _field_value(item: Item, name: str) -> object:
    """Return a field for the index: its value, or the documented default; scalar lists sorted."""
    value = item.data.get(name, _DEFAULTS.get(name))
    return sorted(value) if name in _SORTED_LISTS and isinstance(value, list) else value


def _base_entry(repo: Repo, item: Item, links: dict) -> dict:
    """Build the entry parts shared by both kinds: identity, url, links, extension keys."""
    names = _TOPIC_FIELDS if item.kind == "topic" else _QUESTION_FIELDS
    entry = {name: _field_value(item, name) for name in names}
    entry.update(slug=item.slug, kind=item.kind, path=item.path, url=BASE_URL + item.path, links=links)
    entry["extra"] = {key: value for key, value in item.data.items() if key.startswith("x_")}
    return entry


def _topic_entry(repo: Repo, item: Item, links: dict, by_topic: dict[str, list[Item]]) -> dict:
    """Build a topic's index entry: base fields plus computed questions, years, stats and papers."""
    entry = _base_entry(repo, item, links)
    questions = by_topic.get(item.slug, [])
    years = {q.data["exam"]["year"] for q in questions if q.data.get("origin") == "pyq" and isinstance(q.data.get("exam"), dict)}
    refs = ({"ref": ref, "url": xref_url(repo, ref)} for ref in item.values("xrefs") if split_xref(ref))
    entry.update(
        questions=[q.slug for q in questions], pyq_years=sorted(years), question_stats=coverage.question_stats(questions),
        papers=coverage.papers_of(item), xrefs=sorted(refs, key=lambda found: found["ref"]),
    )
    return entry


def _warning_records(findings: list[Finding]) -> list[dict]:
    """Turn offline warnings into the index's `diagnostics.warnings` records, sorted."""
    records = [
        {"rule": found.rule, "slugs": sorted(found.slugs), "message": found.message}
        for found in findings if found.severity == "warning"
    ]
    return sorted(records, key=lambda record: (record["rule"], record["slugs"], record["message"]))


def build_index(repo: Repo, findings: list[Finding]) -> dict:
    """Build the full index.json object from a validated Repo and its offline findings."""
    links = graph.compute_links(repo)
    by_topic = coverage.topic_questions(repo)
    items = {}
    for item in repo.items:
        if item.error:
            continue
        items[item.slug] = (
            _topic_entry(repo, item, links[item.slug], by_topic) if item.kind == "topic"
            else _base_entry(repo, item, links[item.slug])
        )
    tags: dict[str, list[str]] = {}
    for item in repo.items:
        for tag in item.values("tags"):
            tags.setdefault(tag, []).append(item.slug)
    return {
        "schema_version": SCHEMA_VERSION, "content_hash": content_hash(repo.root),
        "counts": {f"{kind}s": len(repo.items_of(kind)) for kind in KIND_FOLDERS},
        "items": items, "redirects": dict(repo.config.redirects),
        "tags": {tag: sorted(slugs) for tag, slugs in tags.items()},
        "diagnostics": {"warnings": _warning_records(findings)},
    }


def _one_line(text: object, limit: int = 160) -> str:
    """Collapse whitespace and cut to `limit` characters (used for question summaries)."""
    return re.sub(r"\s+", " ", str(text)).strip()[:limit]


def _search_record(repo: Repo, item: Item) -> dict:
    """Build one slim search record; a question borrows papers from its topics."""
    if item.kind == "topic":
        return {"slug": item.slug, "kind": "topic", "title": item.data.get("title"), "summary": item.data.get("summary"),
                "papers": coverage.papers_of(item), "tags": sorted(item.values("tags")), "status": item.data.get("status")}
    topics = [repo.by_slug[repo.resolve(slug)] for slug in item.values("topics") if repo.resolve(slug) in repo.by_slug]
    papers = sorted({paper for topic in topics if topic.kind == "topic" for paper in coverage.papers_of(topic)})
    return {"slug": item.slug, "kind": "question", "title": item.slug, "summary": _one_line(item.data.get("stem", "")),
            "papers": papers, "tags": [], "status": None}


def build_search(repo: Repo) -> list[dict]:
    """Build search.json: one slim record per item, sorted by slug."""
    return [_search_record(repo, item) for item in sorted(repo.items, key=lambda found: found.slug) if not item.error]


def readme_with_rules(readme_text: str) -> str | None:
    """Return the README with its rule list regenerated, or None when the markers are missing."""
    start, end = readme_text.find(README_START), readme_text.find(README_END)
    if start == -1 or end == -1 or end < start:
        return None
    head = readme_text[:start + len(README_START)]
    return f"{head}\n{render_rules_markdown()}\n{readme_text[end:]}"


def build_outputs(repo: Repo, findings: list[Finding]) -> dict[str, str]:
    """Return {relative path: exact text} for every generated file.

    The README is included only when it exists and has the rule markers;
    stale_findings reports a README without them.
    """
    outputs = {
        f"{API_DIR}/index.json": dumps(build_index(repo, findings)),
        f"{API_DIR}/coverage.json": dumps({"schema_version": SCHEMA_VERSION, "papers": coverage.build_coverage(repo)}),
        f"{API_DIR}/search.json": dumps(build_search(repo)),
    }
    for schema_file in sorted((repo.root / "schema").glob("*.schema.json")):
        outputs[f"{API_DIR}/schema/{schema_file.name}"] = schema_file.read_text(encoding="utf-8")
    readme = repo.root / "README.md"
    updated = readme_with_rules(readme.read_text(encoding="utf-8")) if readme.is_file() else None
    if updated is not None:
        outputs["README.md"] = updated
    return outputs


def _on_disk(root: Path, relative: str) -> str | None:
    """Read a generated file's current text, or None when it does not exist."""
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else None


def stale_findings(repo: Repo, outputs: dict[str, str]) -> list[Finding]:
    """G20: report every generated file that is missing, different, or not expected."""
    findings = [
        error("G20", relative, "", "generated file is missing or out of date; run python ci/sync_index.py")
        for relative, text in sorted(outputs.items()) if _on_disk(repo.root, relative) != text
    ]
    if "README.md" not in outputs:
        findings.append(error("G20", "README.md", "", f"README.md must exist and contain {README_START} and {README_END}"))
    api_root = repo.root / API_DIR
    for path in sorted(api_root.rglob("*")) if api_root.is_dir() else []:
        relative = path.relative_to(repo.root).as_posix()
        if path.is_file() and relative not in outputs:
            findings.append(error("G20", relative, "", "unexpected file in api/v1 (generated folder)"))
    return findings


def write_outputs(root: Path, outputs: dict[str, str]) -> None:
    """Write every output and delete unexpected files in api/v1.

    Side effects: creates folders, rewrites files, unlinks leftovers in the
    generated folder only. Raises OSError on I/O failure.
    """
    for relative, text in outputs.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    api_root = root / API_DIR
    for path in sorted(api_root.rglob("*")) if api_root.is_dir() else []:
        if path.is_file() and path.relative_to(root).as_posix() not in outputs:
            path.unlink()
