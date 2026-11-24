"""Computes the link graph: reverse links and cycle detection.

Single purpose: derive every link in both directions from the stored
(owner-side) links, and find cycles in the directed link fields.
"""

from __future__ import annotations

from .model import LINK_FIELDS, Item, Repo

# Keys present in each kind's `links` object in index.json (spec section 8).
KIND_LINK_KEYS = {
    "topic": ("prerequisites", "required_by", "related", "questions"),
    "question": ("topics",),
}


def stored_targets(repo: Repo, item: Item, field_name: str) -> list[str]:
    """Return the item's targets for one field, redirects followed, missing ones dropped."""
    resolved = (repo.resolve(target) for target in item.values(field_name))
    return sorted({target for target in resolved if target in repo.by_slug})


def _empty_links(repo: Repo) -> dict[str, dict[str, list[str]]]:
    """Create an all-empty links object for every item, shaped by its kind."""
    return {
        item.slug: {key: [] for key in KIND_LINK_KEYS[item.kind]}
        for item in repo.by_slug.values() if not item.error
    }


def _add_item_links(repo: Repo, item: Item, links: dict[str, dict[str, list[str]]]) -> None:
    """Add one item's stored links, and the matching reverse links, to `links`."""
    for name, spec in LINK_FIELDS.items():
        if spec.owner != item.kind:
            continue
        for target in stored_targets(repo, item, name):
            links[item.slug][name].append(target)
            links.get(target, {}).setdefault(spec.reverse, []).append(item.slug)


def compute_links(repo: Repo) -> dict[str, dict]:
    """Return every item's complete `links` object, both directions.

    Lists are sorted and de-duplicated. Symmetric links appear on both items
    because the reverse name of a symmetric field is the field itself.
    """
    links = _empty_links(repo)
    for item in repo.by_slug.values():
        if not item.error:
            _add_item_links(repo, item, links)
    for per_item in links.values():
        for key, values in per_item.items():
            per_item[key] = sorted(set(values))
    return links


def _enter(child: str, edges: dict[str, list[str]], state: dict[str, int],
           path: list[str], stack: list) -> None:
    """Start visiting `child`: mark it on the current path and push its neighbours."""
    state[child] = 1
    path.append(child)
    stack.append((child, iter(sorted(edges.get(child, [])))))


def _walk(start: str, edges: dict[str, list[str]], state: dict[str, int]) -> list[str] | None:
    """Depth-first walk from `start`; return a cycle as a path, or None.

    state maps a node to 1 (on the current path) or 2 (finished).
    """
    path: list[str] = []
    stack: list = []
    _enter(start, edges, state, path, stack)
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            state[node] = 2
            stack.pop()
            path.pop()
        elif state.get(child) == 1:
            return path[path.index(child):] + [child]
        elif child not in state:
            _enter(child, edges, state, path, stack)
    return None


def find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """Return one cycle in the directed graph as [a, b, ..., a], or None if acyclic."""
    state: dict[str, int] = {}
    for start in sorted(edges):
        if start not in state:
            cycle = _walk(start, edges, state)
            if cycle:
                return cycle
    return None
