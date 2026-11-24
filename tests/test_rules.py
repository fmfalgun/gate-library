"""One failing fixture per fixture-driven rule, caught with the right rule ID.

Single purpose: prove each rule fires on its fixture and that the valid
fixture passes clean. G17, G21 and G22 need git, a network stub or run-time
built files, so test_policy.py covers them; every rule is accounted for here.
"""

from __future__ import annotations

import pytest

from conftest import all_findings, make_repo, rule_ids
from gate_lib.rules import RULES

# (fixture folder, expected rule, expected severity)
CASES = [
    ("structure/g01", "G1", "error"),
    ("structure/g02", "G2", "error"),
    ("structure/g03", "G3", "error"),
    ("structure/g04", "G4", "error"),
    ("links/g05", "G5", "error"),
    ("links/g06", "G6", "error"),
    ("links/g07", "G7", "error"),
    ("structure/g08", "G8", "error"),
    ("structure/g09", "G9", "error"),
    ("content/g10", "G10", "error"),
    ("content/g11", "G11", "error"),
    ("content/g12", "G12", "error"),
    ("content/g13", "G13", "error"),
    ("links/g14", "G14", "warning"),
    ("links/g15", "G15", "warning"),
    ("links/g16", "G16", "warning"),
    ("policy/g18", "G18", "error"),
    ("policy/g19", "G19", "error"),
    ("policy/g20", "G20", "error"),
    ("policy/g21", "G21", "error"),
]
RULES_TESTED_ELSEWHERE = {"G17", "G22"}


@pytest.mark.parametrize("fixture,rule,severity", CASES, ids=[case[0] for case in CASES])
def test_fixture_triggers_its_rule(tmp_path, fixture, rule, severity):
    """Each fixture, laid over the valid repo, produces its rule at the expected severity."""
    root = make_repo(tmp_path, fixture, generate_first=(rule == "G20"))
    findings = all_findings(root, include_stale=(rule == "G20"))
    assert rule in rule_ids(findings, severity), [found.render() for found in findings]


def test_every_rule_has_a_fixture_or_a_named_test():
    """No rule in the table lacks coverage: fixtures here, or G17/G22 in test_policy.py."""
    covered = {case[1] for case in CASES} | RULES_TESTED_ELSEWHERE
    assert covered == {rule.rule_id for rule in RULES}


def test_valid_fixture_has_no_findings(tmp_path):
    """The valid fixture passes every rule with no errors and no warnings."""
    findings = all_findings(make_repo(tmp_path))
    assert findings == [], [found.render() for found in findings]


def test_g5_redirect_is_a_warning_not_an_error(tmp_path):
    """A link that resolves through a redirect warns instead of failing."""
    findings = all_findings(make_repo(tmp_path, "links/g05_redirect"))
    assert "G5" in rule_ids(findings, "warning") and not rule_ids(findings, "error")


def test_g12_rejects_msq_answer_outside_options(tmp_path):
    """An msq answer that is not a subset of its options fails G12 (acceptance check)."""
    findings = all_findings(make_repo(tmp_path, "content/g12"))
    assert any(found.rule == "G12" and "subset" in found.message for found in findings)


def test_g11_reports_mismatch_and_missing_source(tmp_path):
    """The G11 fixture has both a slug/exam mismatch and a missing source_url."""
    messages = [found.message for found in all_findings(make_repo(tmp_path, "content/g11")) if found.rule == "G11"]
    assert any("slug" in message for message in messages) and any("source_url" in message for message in messages)


def test_g13_names_the_section_problem(tmp_path):
    """Dropping the last heading is reported with the required heading list."""
    findings = all_findings(make_repo(tmp_path, "content/g13"))
    assert any(found.rule == "G13" and "Sources" in found.message for found in findings)
