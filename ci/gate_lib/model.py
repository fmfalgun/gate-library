"""Shared data types and constants for the gate-library tooling.

Single purpose: define Item, Finding, Repo and the table of link fields, so
every other module speaks the same vocabulary and none imports another's
internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .config import Config

KINDS = ("topic", "question")
KIND_FOLDERS = {"topic": "topics", "question": "questions"}
KIND_SUFFIXES = {"topic": ".md", "question": ".yaml"}
FOLDER_KINDS = {folder: kind for kind, folder in KIND_FOLDERS.items()}
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
SLUG_MAX_LENGTH = 80
SCHEMA_VERSION = "1.0.0"
BASE_URL = "https://fmfalgun.github.io/gate-library/"
STATUS_ORDER = ("learning", "revised", "exam-ready")
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"


@dataclass(frozen=True)
class LinkSpec:
    """One row of the spec's relation table (section 6).

    owner is the only kind allowed to store the field, target is the kind it
    points to, reverse is the computed name on the target side (equal to the
    field name when the link is symmetric).
    """

    owner: str
    target: str
    reverse: str
    symmetric: bool = False


# `syllabus` and `xrefs` are link fields too, but they point outside the slug
# space, so they are handled by their own rules (G9, G21) and not listed here.
LINK_FIELDS: dict[str, LinkSpec] = {
    "topics": LinkSpec("question", "topic", "questions"),
    "prerequisites": LinkSpec("topic", "topic", "required_by"),
    "related": LinkSpec("topic", "topic", "related", symmetric=True),
}
TOPIC_ONLY_FIELDS = ("syllabus", "xrefs")


@dataclass(frozen=True)
class Finding:
    """One validation result: which rule, how serious, where, and why.

    slugs lists the items involved so the index can attach a warning to the
    items it concerns.
    """

    rule: str
    severity: str
    file: str
    field: str
    message: str
    slugs: tuple[str, ...] = ()

    def render(self) -> str:
        """Return the one-line form printed to the terminal."""
        where = f"{self.file} [{self.field}]" if self.field else self.file
        return f"{self.severity.upper()} {self.rule} {where}: {self.message}"


def error(rule: str, file: str, field_name: str, message: str, slugs: tuple[str, ...] = ()) -> Finding:
    """Build an error Finding; errors block commits and fail CI."""
    return Finding(rule, SEVERITY_ERROR, file, field_name, message, slugs)


def warning(rule: str, file: str, field_name: str, message: str, slugs: tuple[str, ...] = ()) -> Finding:
    """Build a warning Finding; warnings are printed and recorded only."""
    return Finding(rule, SEVERITY_WARNING, file, field_name, message, slugs)


@dataclass
class Item:
    """One content file: its place, its data and (for topics) its Markdown body.

    data is empty and error is set when the file could not be parsed; checks
    skip such items because G3 already reports them.
    """

    folder_kind: str
    stem: str
    path: str
    data: dict
    body: str
    error: str | None = None

    @property
    def slug(self) -> str:
        """The item's ID: its filename without the extension."""
        return self.stem

    @property
    def kind(self) -> str:
        """The kind implied by the folder the file sits in."""
        return self.folder_kind

    def values(self, field_name: str) -> list[str]:
        """Return the string entries of a field, whether it holds a list or one string.

        A missing field gives an empty list; non-string entries are ignored
        because the schema check (G3) reports them.
        """
        raw = self.data.get(field_name)
        entries = raw if isinstance(raw, list) else [raw]
        return [entry for entry in entries if isinstance(entry, str)]


@dataclass
class Repo:
    """Everything the checks need: root, config, items, stray paths and 'today'."""

    root: Path
    config: Config
    items: list[Item]
    stray_paths: list[str]
    today: date
    by_slug: dict[str, Item] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Index items by slug; the first file wins so G2 can report the rest."""
        for item in self.items:
            self.by_slug.setdefault(item.slug, item)

    def resolve(self, slug: str) -> str:
        """Follow a redirect once; redirect chains are not allowed."""
        return self.config.redirects.get(slug, slug)

    def items_of(self, kind: str) -> list[Item]:
        """Return the parsed items of one kind, in path order."""
        return [item for item in self.items if item.kind == kind and not item.error]


def owned_links(item: Item) -> list[tuple[str, LinkSpec, str]]:
    """List every (field, spec, target) link the item stores on a field it may own."""
    found = []
    for name, spec in LINK_FIELDS.items():
        if spec.owner == item.kind:
            found.extend((name, spec, target) for target in item.values(name))
    return found


def misplaced_link_fields(item: Item) -> list[str]:
    """Return link fields present on an item of a kind that may not own them (G4)."""
    owned_elsewhere = [name for name, spec in LINK_FIELDS.items() if spec.owner != item.kind]
    if item.kind != "topic":
        owned_elsewhere.extend(TOPIC_ONLY_FIELDS)
    return [name for name in owned_elsewhere if name in item.data]


def syllabus_ref_parts(reference: str) -> tuple[str, str, str] | None:
    """Split `<paper>:<subject-id>/<item-id>` into its three parts, or None when malformed."""
    paper, colon, rest = reference.partition(":")
    subject, slash, item_id = rest.partition("/")
    return (paper, subject, item_id) if colon and slash and paper and subject and item_id else None
