"""Syllabus coverage and question statistics.

Single purpose: compute, from validated content, how much of each paper's
syllabus the topics cover and how the practice questions have gone. Pure
functions over a Repo; no file output (emit.py writes the results).
"""

from __future__ import annotations

from .model import STATUS_ORDER, Item, Repo, syllabus_ref_parts

PUBLIC_SITE = "portfolio"
DEFAULT_SHOW_ON = [PUBLIC_SITE]
NOT_COVERED = "none"


def show_on(item: Item) -> list[str]:
    """Return the item's show_on list, or the documented default ["portfolio"] when absent."""
    raw = item.data.get("show_on")
    return list(raw) if isinstance(raw, list) else list(DEFAULT_SHOW_ON)


def is_public(item: Item) -> bool:
    """True when the item may appear on the portfolio site."""
    return PUBLIC_SITE in show_on(item)


def best_status(statuses: list[str]) -> str:
    """Return the highest status among `statuses` (learning < revised < exam-ready), or 'none'."""
    ranked = [STATUS_ORDER.index(status) for status in statuses if status in STATUS_ORDER]
    return STATUS_ORDER[max(ranked)] if ranked else NOT_COVERED


def topics_by_syllabus_ref(repo: Repo) -> dict[str, list[Item]]:
    """Map each syllabus reference to the topics that list it, sorted by slug."""
    owners: dict[str, list[Item]] = {}
    for item in repo.items_of("topic"):
        for reference in set(item.values("syllabus")):
            owners.setdefault(reference, []).append(item)
    return {reference: sorted(items, key=lambda found: found.slug) for reference, items in owners.items()}


def _view(topics: list[Item]) -> dict:
    """Describe a set of covering topics: their slugs and their best status."""
    return {"covered_by": [item.slug for item in topics], "best_status": best_status([item.data.get("status") for item in topics])}


def _percent(part: int, whole: int) -> float:
    """Return part/whole as a percentage with one decimal; 0.0 for an empty whole."""
    return round(100.0 * part / whole, 1) if whole else 0.0


def _summary(views: list[dict]) -> dict:
    """Summarize item views: counts and percentages of covered and exam-ready items."""
    covered = sum(1 for view in views if view["best_status"] != NOT_COVERED)
    ready = sum(1 for view in views if view["best_status"] == "exam-ready")
    return {
        "items": len(views), "covered": covered, "exam_ready": ready,
        "percent_covered": _percent(covered, len(views)), "percent_exam_ready": _percent(ready, len(views)),
    }


def _with_all(public_views: list[dict], all_views: list[dict]) -> dict:
    """Return the public summary with the all-topics numbers nested under `all`."""
    return {**_summary(public_views), "all": _summary(all_views)}


def _subject_block(paper: str, subject: dict, owners: dict[str, list[Item]]) -> tuple[dict, list[dict], list[dict]]:
    """Build one subject's coverage block; also return its public and all item views for roll-up."""
    items, public_views, all_views = [], [], []
    for entry in subject["items"]:
        covering = owners.get(f"{paper}:{subject['id']}/{entry['id']}", [])
        everyone, public = _view(covering), _view([item for item in covering if is_public(item)])
        items.append({"id": entry["id"], "text": entry["text"], **public, "all": everyone})
        public_views.append(public)
        all_views.append(everyone)
    # `items` is the count (spec section 8); the item list is `syllabus_items`.
    block = {"id": subject["id"], "name": subject["name"], "syllabus_items": items, **_with_all(public_views, all_views)}
    return block, public_views, all_views


def _paper_block(paper: str, data: dict, owners: dict[str, list[Item]]) -> dict:
    """Build one paper's coverage block with its subjects in syllabus order."""
    subjects, public_views, all_views = [], [], []
    for subject in data["subjects"]:
        block, public, everyone = _subject_block(paper, subject, owners)
        subjects.append(block)
        public_views.extend(public)
        all_views.extend(everyone)
    meta = {key: data[key] for key in ("name", "exam_year", "source_url", "retrieved")}
    return {**meta, "subjects": subjects, **_with_all(public_views, all_views)}


def build_coverage(repo: Repo) -> dict[str, dict]:
    """Return {paper: coverage block} for every current syllabus file, from validated content."""
    owners = topics_by_syllabus_ref(repo)
    return {paper: _paper_block(paper, data, owners) for paper, data in sorted(repo.config.syllabi.items())}


def papers_of(topic: Item) -> list[str]:
    """Return the sorted paper codes a topic's syllabus references belong to."""
    parts = (syllabus_ref_parts(reference) for reference in topic.values("syllabus"))
    return sorted({part[0] for part in parts if part})


def latest_result(question: Item) -> str | None:
    """Return the result of a question's most recent attempt, or None when never attempted."""
    attempts = question.data.get("attempts") or []
    return attempts[-1].get("result") if attempts and isinstance(attempts[-1], dict) else None


def question_stats(questions: list[Item]) -> dict:
    """Count questions and score the attempted ones.

    accuracy is the share of attempted questions whose latest attempt was
    `right`, rounded to 4 places; None when nothing was attempted.
    """
    latest = [latest_result(question) for question in questions]
    attempted = [result for result in latest if result is not None]
    accuracy = round(attempted.count("right") / len(attempted), 4) if attempted else None
    pyq = sum(1 for question in questions if question.data.get("origin") == "pyq")
    return {"total": len(questions), "pyq": pyq, "generated": len(questions) - pyq, "attempted": len(attempted), "accuracy": accuracy}


def topic_questions(repo: Repo) -> dict[str, list[Item]]:
    """Map each topic slug to the questions that link to it (redirects followed)."""
    found: dict[str, list[Item]] = {}
    for question in repo.items_of("question"):
        for target in {repo.resolve(slug) for slug in question.values("topics")}:
            found.setdefault(target, []).append(question)
    return {slug: sorted(items, key=lambda item: item.slug) for slug, items in found.items()}


def render_stats(repo: Repo) -> str:
    """Return the `--stats` text: per paper, coverage percentages and question accuracy."""
    by_topic = topic_questions(repo)
    lines = []
    for paper, block in build_coverage(repo).items():
        slugs = {slug for sub in block["subjects"] for entry in sub["syllabus_items"] for slug in entry["all"]["covered_by"]}
        questions = {q.slug: q for slug in slugs for q in by_topic.get(slug, [])}
        stats = question_stats(list(questions.values()))
        everything = block["all"]
        lines.append(
            f"{paper}: covered {everything['covered']}/{everything['items']} ({everything['percent_covered']}%), "
            f"exam-ready {everything['exam_ready']} ({everything['percent_exam_ready']}%), "
            f"questions {stats['total']} (attempted {stats['attempted']}, accuracy {stats['accuracy']})"
        )
    return "\n".join(lines)
