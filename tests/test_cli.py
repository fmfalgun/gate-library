"""Command-line behaviour: --check, --new, --attempt, --stats, --explain.

Single purpose: run sync_index.main against throwaway repos and check exit
codes, file edits and printed text.
"""

from __future__ import annotations

from conftest import make_repo
import sync_index


def run(root, *arguments):
    """Run the CLI against `root` and return its exit code."""
    return sync_index.main(["--root", str(root), *arguments])


def test_check_fails_until_generated_then_passes(tmp_path):
    """--check reports stale output (G20), a normal run writes it, --check then passes."""
    root = make_repo(tmp_path)
    assert run(root, "--check") == 1
    assert run(root) == 0
    assert run(root, "--check") == 0


def test_attempt_appends_and_stamps_updated(tmp_path):
    """--attempt adds one dated entry at the end and leaves old entries untouched."""
    root = make_repo(tmp_path)
    path = root / "questions/gen-graph-basics-001.yaml"
    assert run(root, "--attempt", "gen-graph-basics-001", "wrong", "trap") == 0
    text = path.read_text()
    assert "attempts:\n  - date: " in text and "result: wrong" in text and "reason: trap" in text
    assert run(root, "--attempt", "gen-graph-basics-001", "right") == 0
    assert text.split("attempts:")[1] in path.read_text().replace("    result: right\n", "")


def test_attempt_extends_an_existing_list_before_next_key(tmp_path):
    """A second entry goes after the existing ones, not after later top-level keys."""
    root = make_repo(tmp_path)
    assert run(root, "--attempt", "gate-2024-cs-s2-q23", "skipped") == 0
    lines = (root / "questions/gate-2024-cs-s2-q23.yaml").read_text().splitlines()
    assert lines.index("    result: skipped") < lines.index("created: 2026-11-01")
    assert run(root) == 0


def test_attempt_rejects_bad_arguments(tmp_path, capsys):
    """An unknown result, reason or question is refused with exit 1 and a message."""
    root = make_repo(tmp_path)
    assert run(root, "--attempt", "gen-graph-basics-001", "maybe") == 1
    assert run(root, "--attempt", "gen-graph-basics-001", "wrong", "bored") == 1
    assert run(root, "--attempt", "no-such-question", "wrong") == 1
    assert "result must be" in capsys.readouterr().err


def test_new_creates_each_template_and_refuses_duplicates(tmp_path):
    """--new makes topic and question files from templates; a second try for the same slug fails."""
    root = make_repo(tmp_path)
    assert run(root, "--new", "topic", "matrices-intro") == 0
    assert run(root, "--new", "question-nat", "gen-matrices-intro-001") == 0
    assert (root / "topics/matrices-intro.md").is_file() and (root / "questions/gen-matrices-intro-001.yaml").is_file()
    assert "- matrices-intro" in (root / "questions/gen-matrices-intro-001.yaml").read_text()
    assert run(root, "--new", "topic", "matrices-intro") == 1
    assert run(root, "--new", "topic", "Bad Slug") == 1


def test_fresh_topic_template_is_incomplete_until_edited(tmp_path):
    """The scaffold keeps TODO markers, so G13 blocks committing it unfinished."""
    root = make_repo(tmp_path)
    run(root, "--new", "topic", "matrices-intro")
    assert run(root) == 1


def test_stats_and_explain_print(tmp_path, capsys):
    """--stats lists every paper; --explain shows links in both directions."""
    root = make_repo(tmp_path)
    assert run(root, "--stats") == 0
    assert "da: covered 1/88" in capsys.readouterr().out
    assert run(root, "--explain", "graph-basics") == 0
    assert "required_by: ['shortest-paths']" in capsys.readouterr().out
    assert run(root, "--explain", "nope") == 1
