"""Field-value rules: G18 (allowed values) and G19 (dates).

Single purpose: check the values of fields that do not involve other items.
"""

from __future__ import annotations

from datetime import date

from ..model import Finding, Item, Repo, error


def check_g18_allowed_values(repo: Repo) -> list[Finding]:
    """G18: show_on values are registered sites and tags are in config/tags.json."""
    findings = []
    for item in repo.items:
        for site in item.values("show_on"):
            if site not in repo.config.sites:
                findings.append(error("G18", item.path, "show_on", f"'{site}' is not in config/sites.json", (item.slug,)))
        for tag in item.values("tags"):
            if tag not in repo.config.tags:
                findings.append(error("G18", item.path, "tags", f"'{tag}' is not in config/tags.json", (item.slug,)))
    return findings


def parse_date(text: object) -> date | None:
    """Return the date for a `YYYY-MM-DD` string, or None when it is not a real date."""
    try:
        return date.fromisoformat(text) if isinstance(text, str) else None
    except ValueError:
        return None


def _date_problems(item: Item, today: date) -> list[str]:
    """List what is wrong with an item's created/updated dates."""
    problems = []
    parsed = {name: parse_date(item.data.get(name)) for name in ("created", "updated")}
    for name, value in parsed.items():
        if name in item.data and value is None:
            problems.append(f"{name} is not a valid YYYY-MM-DD date")
        elif value is not None and value > today:
            problems.append(f"{name} {value} is in the future")
    created, updated = parsed["created"], parsed["updated"]
    if created and updated and created > updated:
        problems.append("created is after updated")
    return problems


def _attempt_date_problems(item: Item, today: date) -> list[str]:
    """List attempt dates that are invalid or in the future."""
    problems = []
    for entry in item.data.get("attempts") or []:
        when = parse_date(entry.get("date")) if isinstance(entry, dict) else None
        if when is None:
            problems.append("an attempt has no valid YYYY-MM-DD date")
        elif when > today:
            problems.append(f"attempt date {when} is in the future")
    return problems


def check_g19_dates(repo: Repo) -> list[Finding]:
    """G19: valid dates, created <= updated, none in the future (attempt dates included)."""
    return [
        error("G19", item.path, "created/updated", problem, (item.slug,))
        for item in repo.items if not item.error
        for problem in _date_problems(item, repo.today) + _attempt_date_problems(item, repo.today)
    ]
