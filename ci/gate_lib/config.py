"""Loads and shape-checks the files under config/.

Single purpose: turn config/*.json and config/syllabus/*.json into one
immutable Config object, failing loudly with a ConfigError when a file is
missing or has the wrong shape. Syllabus *content* is validated by rule G10,
not here: this module only requires each file to be a JSON object.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when a config file is missing, not JSON, or has the wrong shape."""


@dataclass(frozen=True)
class RepoAlias:
    """One registered repo alias from config/repos.json, used by xrefs."""

    alias: str
    base_url: str
    exists_check: str


@dataclass(frozen=True)
class Config:
    """All configuration the checks and the generator read.

    syllabi maps a paper code (the file name) to its parsed syllabus dict.
    """

    sites: frozenset[str]
    repos: dict[str, RepoAlias]
    tags: frozenset[str]
    redirects: dict[str, str]
    syllabi: dict[str, dict]


def _read_json(path: Path, expected: type):
    """Read a JSON file and require its top level to be `expected`.

    Raises ConfigError (never returns a wrong shape) so a bad config stops
    the run with a message naming the file.
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as problem:
        raise ConfigError(f"{path.name}: cannot read ({problem.strerror})") from problem
    except json.JSONDecodeError as problem:
        raise ConfigError(f"{path.name}: not valid JSON ({problem})") from problem
    if not isinstance(value, expected):
        raise ConfigError(f"{path.name}: expected a JSON {expected.__name__}")
    return value


def _parse_repos(raw: list) -> dict[str, RepoAlias]:
    """Build RepoAlias objects keyed by alias."""
    repos = {}
    for entry in raw:
        try:
            repos[entry["alias"]] = RepoAlias(entry["alias"], entry["base_url"], entry["exists_check"])
        except (KeyError, TypeError) as problem:
            raise ConfigError(f"repos.json: an entry is malformed ({problem})") from problem
    return repos


def _load_syllabi(folder: Path) -> dict[str, dict]:
    """Load every current syllabus file (not the archive/ subfolder), keyed by file stem."""
    return {path.stem: _read_json(path, dict) for path in sorted(folder.glob("*.json"))}


def load_config(root: Path) -> Config:
    """Load every file in <root>/config into a Config.

    Raises ConfigError when any file is missing or malformed.
    """
    folder = root / "config"
    return Config(
        sites=frozenset(_read_json(folder / "sites.json", list)),
        repos=_parse_repos(_read_json(folder / "repos.json", list)),
        tags=frozenset(_read_json(folder / "tags.json", list)),
        redirects=_read_json(folder / "redirects.json", dict),
        syllabi=_load_syllabi(folder / "syllabus"),
    )
