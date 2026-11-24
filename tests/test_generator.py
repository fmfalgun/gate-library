"""Generated outputs: determinism, index fields, coverage numbers and public/private split.

Single purpose: prove api/v1 is byte-stable and carries the computed fields
the spec lists (links both ways, pyq_years, question_stats, coverage).
"""

from __future__ import annotations

import json

from conftest import load, make_repo, write_generated
from gate_lib import emit, rules


def outputs_of(root):
    """Return the generated {path: text} map for the repo at `root`."""
    repo = load(root)
    return emit.build_outputs(repo, rules.run_offline_checks(repo))


def test_generation_is_deterministic(tmp_path):
    """Writing twice gives identical bytes, and the second run reports nothing stale."""
    root = make_repo(tmp_path)
    write_generated(root)
    first = outputs_of(root)
    write_generated(root)
    assert outputs_of(root) == first
    repo = load(root)
    assert emit.stale_findings(repo, first) == []


def test_index_has_computed_fields(tmp_path):
    """Topics get reverse links, questions, pyq_years, stats and papers; questions get links."""
    index = json.loads(outputs_of(make_repo(tmp_path))["api/v1/index.json"])
    paths = index["items"]["shortest-paths"]
    assert index["items"]["graph-basics"]["links"]["required_by"] == ["shortest-paths"]
    assert paths["pyq_years"] == [2024] and paths["questions"] == ["gate-2024-cs-s2-q23"]
    assert paths["question_stats"] == {"total": 1, "pyq": 1, "generated": 0, "attempted": 1, "accuracy": 1.0}
    assert paths["papers"] == ["cs"] and index["items"]["gate-2024-cs-s2-q23"]["links"] == {"topics": ["shortest-paths"]}
    assert index["counts"] == {"questions": 3, "topics": 3}


def test_coverage_counts_public_topics_only(tmp_path):
    """A topic hidden from the portfolio counts under `all` but not in the public numbers."""
    root = make_repo(tmp_path)
    path = root / "topics" / "eigen-basics.md"
    path.write_text(path.read_text().replace("status: learning", "show_on: []\nstatus: exam-ready"))
    paper = json.loads(outputs_of(root)["api/v1/coverage.json"])["papers"]["da"]
    assert paper["covered"] == 0 and paper["all"]["covered"] == 1 and paper["all"]["exam_ready"] == 1


def test_coverage_marks_best_status(tmp_path):
    """The covering topic's status becomes the item's best_status."""
    paper = json.loads(outputs_of(make_repo(tmp_path))["api/v1/coverage.json"])["papers"]["cs"]
    subject = next(s for s in paper["subjects"] if s["id"] == "algorithms")
    entry = next(i for i in subject["syllabus_items"] if i["id"] == "shortest-paths")
    assert entry["covered_by"] == ["shortest-paths"] and entry["best_status"] == "learning"


def test_search_lists_every_item_slim(tmp_path):
    """search.json has one slim record per item with the documented keys."""
    search = json.loads(outputs_of(make_repo(tmp_path))["api/v1/search.json"])
    assert len(search) == 6
    assert set(search[0]) == {"slug", "kind", "title", "summary", "papers", "tags", "status"}
