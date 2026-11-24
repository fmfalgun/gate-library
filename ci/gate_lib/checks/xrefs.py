"""Cross-repo reference rule G21: xrefs have a valid shape and alias (offline) and exist (online).

Single purpose: validate `<alias>:<folder>/<slug>` references to other repos.
Offline problems are errors; online problems are only warnings, so a change
in another repo never blocks a commit here.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Callable

from ..model import SLUG_PATTERN, Finding, Item, Repo, error, warning

# A fetcher takes a URL and returns the parsed JSON, or raises OSError/ValueError.
Fetcher = Callable[[str], object]


def split_xref(reference: str) -> tuple[str, str, str] | None:
    """Split `<alias>:<folder>/<slug>` into its three parts; None when the shape is wrong."""
    alias, colon, path = reference.partition(":")
    folder, slash, slug = path.partition("/")
    ok = colon and slash and alias and folder and re.fullmatch(SLUG_PATTERN, slug)
    return (alias, folder, slug) if ok else None


def xref_url(repo: Repo, reference: str) -> str | None:
    """Return the published URL of a registered reference, or None when it cannot be resolved.

    An `index` repo publishes Markdown at <base><folder>/<slug>.md; a
    `manifest` repo publishes records at <base>data/<folder>/<slug>.json.
    """
    parts = split_xref(reference)
    entry = repo.config.repos.get(parts[0]) if parts else None
    if entry is None or parts is None:
        return None
    _alias, folder, slug = parts
    return f"{entry.base_url}{folder}/{slug}.md" if entry.exists_check == "index" else f"{entry.base_url}data/{folder}/{slug}.json"


def _offline_problem(repo: Repo, reference: str) -> str | None:
    """Return what is wrong with one xref's shape or alias, or None when it is fine."""
    parts = split_xref(reference)
    if parts is None:
        return f"'{reference}' must look like <alias>:<folder>/<slug>"
    if parts[0] not in repo.config.repos:
        return f"alias '{parts[0]}' is not in config/repos.json"
    return None


def check_g21_offline(repo: Repo) -> list[Finding]:
    """G21 (offline): each xref has the `<alias>:<folder>/<slug>` shape and a registered alias."""
    findings = []
    for item in repo.items:
        for reference in item.values("xrefs"):
            problem = _offline_problem(repo, reference)
            if problem:
                findings.append(error("G21", item.path, "xrefs", problem, (item.slug,)))
    return findings


def _exists(entry, folder: str, slug: str, fetch: Fetcher) -> tuple[bool, str]:
    """Return (found, url consulted); raises OSError/ValueError when the repo is unreachable."""
    if entry.exists_check == "index":
        url = f"{entry.base_url}api/v1/index.json"
        index = fetch(url)
        items = index.get("items") if isinstance(index, dict) else None
        return isinstance(items, dict) and slug in items, url
    url = f"{entry.base_url}data/{folder}/manifest.json"
    manifest = fetch(url)
    return isinstance(manifest, list) and f"{slug}.json" in manifest, url


def _online_finding(repo: Repo, item: Item, reference: str, fetch: Fetcher) -> Finding | None:
    """Warn when the referenced repo cannot be read or does not contain the target."""
    parts = split_xref(reference)
    entry = repo.config.repos.get(parts[0]) if parts else None
    if entry is None or parts is None:
        return None
    slugs = (item.slug,)
    try:
        found, url = _exists(entry, parts[1], parts[2], fetch)
    except (OSError, ValueError) as problem:
        return warning("G21", item.path, "xrefs", f"could not check '{reference}': unreachable ({problem})", slugs)
    return None if found else warning("G21", item.path, "xrefs", f"'{reference}' was not found in {url}", slugs)


def check_g21_online(repo: Repo, fetch: Fetcher) -> list[Finding]:
    """G21 (online): warn about xrefs whose target is missing or whose repo is unreachable."""
    found = (_online_finding(repo, item, ref, fetch) for item in repo.items for ref in item.values("xrefs"))
    return [finding for finding in found if finding]


def fetch_json(url: str, timeout_seconds: int = 10) -> object:
    """Fetch a URL and parse it as JSON.

    Used only for `--online`. Raises OSError (network problems, HTTP errors)
    or ValueError (not JSON); callers turn both into warnings.
    """
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - fixed https base URLs from config
        return json.loads(response.read().decode("utf-8"))
