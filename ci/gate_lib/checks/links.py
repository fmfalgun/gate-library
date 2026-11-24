"""Link rules: G4 (link fields), G5 (targets), G6 (cycles, self-links), G7 (symmetric pairs), G8 (duplicates).

Single purpose: check that every stored link is allowed, points at something
real of the right kind, is stored exactly once, and is never repeated in a list.
"""

from __future__ import annotations

from collections import Counter

from ..graph import find_cycle, stored_targets
from ..model import LINK_FIELDS, Finding, Item, Repo, error, misplaced_link_fields, owned_links, warning

_SYMMETRIC_FIELDS = tuple(name for name, spec in LINK_FIELDS.items() if spec.symmetric)
_LIST_FIELDS = ("tags", "show_on", "syllabus", "xrefs", *LINK_FIELDS)


def check_g04_link_fields(repo: Repo) -> list[Finding]:
    """G4: every link field sits on the kind that owns it."""
    return [
        error("G4", item.path, name, f"'{name}' is not allowed on a {item.kind} file", (item.slug,))
        for item in repo.items if not item.error
        for name in misplaced_link_fields(item)
    ]


def _target_finding(repo: Repo, item: Item, field_name: str, target: str, wanted: str) -> Finding | None:
    """Return the G5 finding for one link target, or None when the link is fine.

    A target reached through a redirect is a warning (update the link); a
    missing target or one of the wrong kind is an error.
    """
    destination = repo.by_slug.get(repo.resolve(target))
    slugs = (item.slug,)
    if destination is None:
        return error("G5", item.path, field_name, f"'{target}' does not exist", slugs)
    if destination.kind != wanted:
        return error("G5", item.path, field_name, f"'{target}' is a {destination.kind}; {field_name} needs a {wanted}", slugs)
    if target != destination.slug:
        return warning("G5", item.path, field_name, f"'{target}' was renamed to '{destination.slug}'; update the link", slugs)
    return None


def check_g05_link_targets(repo: Repo) -> list[Finding]:
    """G5: every link target exists (or resolves through a redirect) and is the right kind."""
    found = (
        _target_finding(repo, item, name, target, spec.target)
        for item in repo.items for name, spec, target in owned_links(item)
    )
    return [finding for finding in found if finding]


def _cycle_finding(repo: Repo) -> Finding | None:
    """Return a G6 finding when `prerequisites` has a cycle anywhere in the repo."""
    edges = {item.slug: stored_targets(repo, item, "prerequisites") for item in repo.items if not item.error}
    cycle = find_cycle(edges)
    if not cycle:
        return None
    start = repo.by_slug[cycle[0]]
    return error("G6", start.path, "prerequisites", "cycle: " + " -> ".join(cycle), tuple(sorted(set(cycle))))


def check_g06_cycles_and_self_links(repo: Repo) -> list[Finding]:
    """G6: no self-links in any field; no cycles in prerequisites."""
    findings = [
        error("G6", item.path, name, "an item cannot link to itself", (item.slug,))
        for item in repo.items
        for name, _spec, target in owned_links(item)
        if repo.resolve(target) == item.slug
    ]
    cycle = _cycle_finding(repo)
    return findings + ([cycle] if cycle else [])


def _mutual_pairs(repo: Repo, name: str) -> list[tuple[str, str]]:
    """Return (a, b) with a < b where each item lists the other in the symmetric field `name`."""
    stored = {item.slug: set(stored_targets(repo, item, name)) for item in repo.items if not item.error}
    return [
        (slug, other)
        for slug, targets in sorted(stored.items())
        for other in sorted(targets)
        if slug < other and slug in stored.get(other, set())
    ]


def check_g07_symmetric_pairs(repo: Repo) -> list[Finding]:
    """G7: a `related` pair is stored in one file only, never both."""
    return [
        error("G7", repo.by_slug[slug].path, name,
              f"'{slug}' and '{other}' list each other; keep the link in the newer file only", (slug, other))
        for name in _SYMMETRIC_FIELDS
        for slug, other in _mutual_pairs(repo, name)
    ]


def check_g08_duplicate_entries(repo: Repo) -> list[Finding]:
    """G8: no list repeats an entry."""
    findings = []
    for item in repo.items:
        for name in _LIST_FIELDS:
            repeated = [value for value, count in Counter(item.values(name)).items() if count > 1]
            findings.extend(
                error("G8", item.path, name, f"'{value}' appears more than once", (item.slug,))
                for value in sorted(repeated)
            )
    return findings
