"""
darth-bot/kb/manifest.py
========================
Reads the Bungie Destiny manifest cache from the Destiny Voyager toolkit
(`manifest_cache/DestinyInventoryItemDefinition.json`) and exposes
a tiny lookup function for item / perk / exotic detail.

This is the fastest, most authoritative source for:
  - Exotic descriptions ("what does Celestial Nighthawk do?")
  - Perk descriptions ("what is Triple Tap?")
  - Shader / cosmetic lookups ("is there an all black shader?")
  - Stat values, slot info

If the manifest isn't cached locally, this module silently returns
empty results — the bot will fall through to live search instead.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Optional

from ..config import DESTINY_VOYAGER_MANIFEST


_TABLE = "DestinyInventoryItemDefinition"


@lru_cache(maxsize=1)
def _items() -> dict:
    f = DESTINY_VOYAGER_MANIFEST / f"{_TABLE}.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def lookup_by_name(query: str, *, limit: int = 10) -> list[dict]:
    """
    Fuzzy substring search over item names. Returns top matches as compact dicts.
    """
    items = _items()
    if not items:
        return []
    q = query.lower().strip()
    matches = []
    for h, defn in items.items():
        dp = defn.get("displayProperties", {})
        name = dp.get("name") or ""
        if not name or "REDACTED" in name.upper():
            continue
        nl = name.lower()
        score = 0
        if nl == q:
            score = 100
        elif nl.startswith(q):
            score = 80
        elif q in nl:
            score = 50
        else:
            continue
        matches.append((score, _compact(defn)))
    matches.sort(key=lambda t: -t[0])
    return [m[1] for m in matches[:limit]]


def _compact(defn: dict) -> dict:
    dp = defn.get("displayProperties", {})
    inv = defn.get("inventory", {})
    return {
        "hash": defn.get("hash"),
        "name": dp.get("name"),
        "description": (dp.get("description") or "").strip(),
        "type": defn.get("itemTypeDisplayName"),
        "tier": inv.get("tierTypeName"),
        "item_type": defn.get("itemType"),
    }


def format_for_context(query: str, *, limit: int = 6) -> str:
    """One-shot helper — returns plaintext suitable for LLM context."""
    results = lookup_by_name(query, limit=limit)
    if not results:
        return ""
    lines = [f"Manifest matches for '{query}':"]
    for r in results:
        bits = [r["name"], f"[{r.get('tier','?')}]", f"({r.get('type','?')})"]
        lines.append("  " + " ".join(b for b in bits if b))
        if r.get("description"):
            lines.append(f"    {r['description'][:280]}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Crimson"
    print(format_for_context(q))
