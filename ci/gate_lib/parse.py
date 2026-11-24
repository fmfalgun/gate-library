"""Reads content files into a Repo.

Single purpose: turn the two content folders into Item objects (topics are
Markdown with YAML front matter, questions are plain YAML), recording anything
that is not a clean `<slug>.<ext>` as a stray path instead of guessing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from .config import load_config
from .model import FOLDER_KINDS, KIND_SUFFIXES, Item, Repo

_FENCE = "---"


class _TextDatesLoader(yaml.SafeLoader):
    """A YAML loader that keeps `2026-11-24` as text instead of a date object.

    The schema and the date rule (G19) both want strings, so the implicit
    timestamp resolver is removed from this loader only.
    """


_TextDatesLoader.yaml_implicit_resolvers = {
    first_char: [(tag, regex) for tag, regex in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first_char, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class ContentError(ValueError):
    """Raised when a file has no usable front matter or YAML mapping."""


def load_yaml_mapping(yaml_text: str) -> dict:
    """Parse YAML text that must be a mapping; raises ContentError otherwise."""
    try:
        data = yaml.load(yaml_text, Loader=_TextDatesLoader)  # noqa: S506 - SafeLoader subclass
    except yaml.YAMLError as problem:
        raise ContentError(f"not valid YAML ({problem})") from problem
    if not isinstance(data, dict):
        raise ContentError("content must be a key: value mapping")
    return data


def split_front_matter(text: str) -> tuple[str, str]:
    """Split a document into (front-matter YAML text, Markdown body).

    The block must start on the first line with `---` and end at the next
    line that is exactly `---`. Raises ContentError otherwise.
    """
    lines = text.lstrip("﻿").splitlines(keepends=True)
    if not lines or lines[0].strip() != _FENCE:
        raise ContentError("file must start with a '---' front matter line")
    for index in range(1, len(lines)):
        if lines[index].strip() == _FENCE:
            return "".join(lines[1:index]), "".join(lines[index + 1:])
    raise ContentError("front matter is not closed by a second '---' line")


def parse_item(root: Path, path: Path, kind: str) -> Item:
    """Read one content file into an Item.

    Never raises for bad content: the problem is stored in Item.error so the
    checker can report it as G3 and carry on with the other files.
    """
    relative = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
        if kind == "topic":
            yaml_text, body = split_front_matter(text)
            return Item(kind, path.stem, relative, load_yaml_mapping(yaml_text), body)
        return Item(kind, path.stem, relative, load_yaml_mapping(text), "")
    except (OSError, UnicodeDecodeError, ContentError) as problem:
        return Item(kind, path.stem, relative, {}, "", error=str(problem))


def discover(root: Path) -> tuple[list[Item], list[str]]:
    """Find every content item; return (items, stray paths).

    A stray path is anything in a content folder that is not a plain file
    with the kind's extension (a subfolder, another extension): G1 reports them.
    """
    items: list[Item] = []
    strays: list[str] = []
    for folder, kind in FOLDER_KINDS.items():
        directory = root / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix == KIND_SUFFIXES[kind]:
                items.append(parse_item(root, path, kind))
            else:
                strays.append(path.relative_to(root).as_posix())
    return items, strays


def load_repo(root: Path, today=None) -> Repo:
    """Load config and content from `root` into a Repo.

    `today` defaults to the current UTC date; tests pass a fixed date.
    Raises ConfigError when config/ is broken.
    """
    items, strays = discover(root)
    current_day = today or datetime.now(timezone.utc).date()
    return Repo(root, load_config(root), items, strays, current_day)
