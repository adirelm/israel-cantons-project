"""Stable IDs and names for the primary map's cantons, fixed by anchor municipalities."""

from __future__ import annotations


def name_cantons(
    raw: dict[str, int], anchors: list[tuple[str, int, str]]
) -> tuple[dict[str, int], dict[int, str]]:
    """Relabel ``raw`` cantons by anchors ``(municipality, canton_id, name)``.

    Each canton must contain exactly one anchor, so the same region keeps the same
    ID and name across rebuilds. Raises ``ValueError`` otherwise.
    """
    by_raw: dict[int, list[tuple[str, int, str]]] = {}
    for anchor in anchors:
        by_raw.setdefault(raw[anchor[0]], []).append(anchor)
    shared = [", ".join(a[0] for a in group) for group in by_raw.values() if len(group) > 1]
    if shared:
        raise ValueError(f"Anchors share a canton: {'; '.join(shared)}")
    unanchored = sorted(set(raw.values()) - set(by_raw))
    if unanchored:
        members = {c: sorted(m for m, x in raw.items() if x == c)[:3] for c in unanchored}
        raise ValueError(f"Cantons with no anchor: {members}")
    relabel = {c: group[0][1] for c, group in by_raw.items()}
    return {m: relabel[c] for m, c in raw.items()}, {cid: name for _, cid, name in anchors}
