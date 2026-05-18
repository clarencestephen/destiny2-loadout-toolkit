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
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..config import DESTINY_VOYAGER_MANIFEST, SCRAPE_DIR


_TABLE = "DestinyInventoryItemDefinition"


@lru_cache(maxsize=1)
def _items() -> dict:
    """
    Returns the item dict keyed by hash. Two sources:
      1. If Destiny Voyager's manifest JSON cache is present, use it
         (richer data: tierTypeName, itemTypeDisplayName, stats, etc.)
      2. Fallback to the scraped manifest .md files in
         data/scrape/manifest/ (~15k items, name + tier + type only).
    """
    f = DESTINY_VOYAGER_MANIFEST / f"{_TABLE}.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return _items_from_scrape()


def _items_from_scrape() -> dict:
    """Build a compact item dict from the scraped manifest .md files.
    Each file has YAML frontmatter with title/source/url/tier/type/class
    plus a body with a flavor text section."""
    scrape_dir = SCRAPE_DIR / "manifest"
    if not scrape_dir.exists():
        return {}
    out: dict = {}
    fm_re = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
    line_re = re.compile(r"^([a-z_]+):\s*\"?(.*?)\"?$", re.MULTILINE)
    url_hash_re = re.compile(r"bungie:item:(\d+)")
    for path in scrape_dir.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:1500]
        except OSError:
            continue
        m = fm_re.search(text)
        if not m:
            continue
        fields = dict(line_re.findall(m.group(1)))
        name = fields.get("title", "").strip()
        if not name:
            continue
        url = fields.get("url", "")
        hash_m = url_hash_re.search(url)
        item_hash = hash_m.group(1) if hash_m else path.stem
        out[item_hash] = {
            "hash": item_hash,
            "displayProperties": {
                "name": name,
                "description": _extract_flavor(text),
            },
            "itemTypeDisplayName": fields.get("type", "").strip(),
            "inventory": {"tierTypeName": fields.get("tier", "").strip() or None},
            "itemType": None,
        }
    return out


def _extract_flavor(md_text: str) -> str:
    """Pull the flavor text or first body paragraph out of a scraped .md."""
    m = re.search(r"## Flavor\s*\n(.+?)(?:\n##|\n---|$)", md_text, re.DOTALL)
    if m:
        return m.group(1).strip()[:280]
    # Fallback — first non-frontmatter, non-heading line
    body = re.sub(r"^---.*?---", "", md_text, count=1, flags=re.DOTALL).strip()
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            return line[:280]
    return ""


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
    dp = defn.get("displayProperties") or {}
    inv = defn.get("inventory") or {}
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


def extract_named_items(text: str, *, min_len: int = 4, max_results: int = 6) -> list[dict]:
    """
    Find item names from the manifest that appear (case-insensitively) as
    substrings in `text`. Used by the router to ground the LLM and by the
    post-hoc check to flag invented item names.

    Returns most-specific (longest-name) matches first. Filters out
    very short or generic names that produce false positives.
    """
    items = _items()
    if not items:
        return []
    t = text.lower()

    # Pre-built name index, cached per process
    pairs = _name_index()
    found = {}
    for name_lower, hashes in pairs.items():
        if len(name_lower) < min_len:
            continue
        if name_lower in t:
            # Pick a canonical entry — first hash
            for h in hashes:
                defn = items.get(h)
                if defn:
                    found.setdefault(name_lower, _compact(defn))
                    break
    # Longest match first (more specific)
    results = sorted(found.values(), key=lambda d: -len(d["name"] or ""))
    return results[:max_results]


@lru_cache(maxsize=1)
def _name_index() -> dict:
    """Build name_lower → [hash, ...] map for quick scanning."""
    items = _items()
    idx: dict[str, list] = {}
    common_words = {
        "void", "arc", "solar", "stasis", "strand", "kinetic", "energy", "power",
        "the", "and", "or", "of", "by", "to", "is", "a", "an",
        "weapon", "armor", "exotic", "legendary",
    }
    for h, defn in items.items():
        name = (defn.get("displayProperties", {}).get("name") or "").strip()
        if not name or len(name) < 4:
            continue
        # Skip names that are common English words by themselves
        if name.lower() in common_words:
            continue
        idx.setdefault(name.lower(), []).append(h)
    return idx


def verify_names(text: str) -> dict:
    """
    Scan `text` for proper-noun-looking phrases that DON'T match any
    manifest item — these are likely hallucinated names. Returns
    {verified: [str], unverified_candidates: [str]}.

    Conservative: only flags Title Case phrases of 2+ words. Random
    title-case false positives are acceptable.
    """
    import re as _re
    # Title Case phrases: at least 2 words, each starting with caps
    phrases = _re.findall(
        r"\b(?:[A-Z][a-zA-Z'’]+)(?:\s+(?:of|the|[A-Z][a-zA-Z'’]+))(?:\s+[A-Z][a-zA-Z'’]+)*\b",
        text,
    )
    idx = _name_index()
    verified = []
    unverified = []
    seen = set()
    for p in phrases:
        if p in seen:
            continue
        seen.add(p)
        if p.lower() in idx:
            verified.append(p)
        else:
            unverified.append(p)
    return {"verified": verified, "unverified_candidates": unverified}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Crimson"
    print(format_for_context(q))
    print()
    extracted = extract_named_items(q)
    if extracted:
        print(f"Extracted named items ({len(extracted)}):")
        for it in extracted:
            print(f"  {it['name']}  [{it.get('tier')}, {it.get('type')}]")
