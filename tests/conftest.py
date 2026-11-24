"""Shared pytest helpers: build a throwaway repo from fixtures and run the checks on it.

Single purpose: give every test file the same way to assemble a repo
(real schema/config/templates + the valid fixture + optional overlays).
"""

from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "ci"))

from gate_lib import emit, parse, rules  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures"
TODAY = date(2026, 11, 24)
README_STUB = "# fixture repo\n\n<!-- rules:start -->\n<!-- rules:end -->\n"


def overlay(source: Path, target: Path) -> None:
    """Copy every file under `source` onto `target`, replacing files that already exist.

    Used to lay a rule fixture over the valid repo: a fixture file with the
    same path as a valid file replaces it, a new path is added.
    """
    shutil.copytree(source, target, dirs_exist_ok=True)


def make_repo(tmp_path: Path, *overlays: str, generate_first: bool = False) -> Path:
    """Assemble a repo in tmp_path: real schema/config/templates + valid fixture + overlays.

    With generate_first the generated api/ and README are written before the
    overlays are applied, so an overlay can make them stale (rule G20).
    Returns the repo root.
    """
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    for folder in ("schema", "config", "templates"):
        shutil.copytree(REPO_ROOT / folder, root / folder)
    shutil.copytree(FIXTURES / "valid", root, dirs_exist_ok=True)
    (root / "README.md").write_text(README_STUB, encoding="utf-8")
    if generate_first:
        write_generated(root)
    for name in overlays:
        overlay(FIXTURES / name, root)
    return root


def load(root: Path):
    """Load the repo at `root` with the fixed test date."""
    return parse.load_repo(root, TODAY)


def write_generated(root: Path) -> None:
    """Validate the repo and write its generated files; fails the test if validation fails."""
    repo = load(root)
    findings = rules.run_offline_checks(repo)
    errors = [found for found in findings if found.severity == "error"]
    assert not errors, [found.render() for found in errors]
    emit.write_outputs(root, emit.build_outputs(repo, findings))


def all_findings(root: Path, include_stale: bool = False):
    """Return offline findings, plus G20 staleness findings when include_stale is set."""
    repo = load(root)
    findings = rules.run_offline_checks(repo)
    if include_stale:
        findings += emit.stale_findings(repo, emit.build_outputs(repo, findings))
    return findings


def rule_ids(findings, severity: str | None = None) -> set[str]:
    """Return the set of rule IDs among findings, optionally only one severity."""
    return {found.rule for found in findings if severity is None or found.severity == severity}
