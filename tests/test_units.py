"""Unit tests for small pure helpers: cycle finding, status ranking, syllabus refs.

Single purpose: pin the behaviour of functions the rule tests only reach indirectly.
"""

from __future__ import annotations

from gate_lib.coverage import best_status
from gate_lib.graph import find_cycle
from gate_lib.model import syllabus_ref_parts
from gate_lib.checks.topics import section_lines


def test_find_cycle_returns_the_loop_or_none():
    """An acyclic graph gives None; a loop is returned closed on its first node."""
    assert find_cycle({"a": ["b"], "b": ["c"], "c": []}) is None
    assert find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]


def test_best_status_picks_the_highest():
    """exam-ready beats revised beats learning; no topics gives 'none'."""
    assert best_status(["learning", "exam-ready", "revised"]) == "exam-ready"
    assert best_status([]) == "none"


def test_syllabus_ref_parts_requires_all_three_parts():
    """Only <paper>:<subject>/<item> parses; anything shorter is None."""
    assert syllabus_ref_parts("da:linear-algebra/rank") == ("da", "linear-algebra", "rank")
    assert syllabus_ref_parts("da:linear-algebra") is None and syllabus_ref_parts("rank") is None


def test_section_split_ignores_headings_inside_code_fences():
    """A '## ' line inside a fenced block is not a section heading."""
    body = "## Summary\n```\n## not a heading\n```\n## Intuition\ntext\n"
    assert [name for name, _ in section_lines(body)] == ["Summary", "Intuition"]
