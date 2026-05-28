"""
darth-bot/kb/scrape_foundries.py
================================
Auto-generate web/public/foundries.json from the local Bungie manifest.
Replaces the hand-curated foundry data with a fully-automated extraction.

Source of truth: DestinyInventoryItemDefinition.json — every weapon in
Destiny 2 has a `traitIds` array. Foundry-affiliated weapons carry a
`foundry.<name>` trait (e.g. `foundry.hakke`, `foundry.tex_mechanica`,
`foundry.veist`). This is stable across seasons and updated whenever
Bungie pushes a new manifest, so re-running this script (or wiring it
into a post-manifest-bake hook) keeps the bot's `/hakke` / `/suros`
/ etc. commands current with no human input.

Each foundry's entry in the output:
    {
      "display_name": "...",
      "tagline": "...",                     # static lore copy
      "weapon_style": "...",                # static descriptive copy
      "external_link": "https://www.light.gg/...",
      "weapon_counts": {
          "total": N, "exotic": E, "legendary": L, "rare": R
      },
      "exotics": [ {name, type, element, tier, icon_url, watermark}, ... ],
      "recent_legendaries": [ ... ],        # top ~12 by iconWatermark recency
      "all_weapons":        [ ... ],        # full list for the web app to filter
    }

Note: Bungie's `inventory.tierType` codes:
    2 = Common, 3 = Uncommon, 4 = Rare, 5 = Legendary, 6 = Exotic.

Run:
    python3 -m darth_bot.kb.scrape_foundries
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from collections import defaultdict


MANIFEST_PATHS = [
    Path("/home/cs/workspace/Destiny 2/manifest_cache/DestinyInventoryItemDefinition.json"),
    Path(__file__).parent.parent.parent.parent
        / "manifest_cache" / "DestinyInventoryItemDefinition.json",
]

OUT_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "destiny2-loadout-toolkit" / "web" / "public" / "foundries.json"
)
# Fallback to repo-relative path when this script runs from inside the
# already-cloned toolkit dir.
if not OUT_PATH.parent.exists():
    OUT_PATH = (
        Path(__file__).parent.parent.parent
        / "web" / "public" / "foundries.json"
    )


# Static per-foundry copy. The lists themselves are auto-generated;
# the tagline + weapon_style are intentionally hand-written because
# "what this foundry FEELS like" doesn't change between manifest pushes.
FOUNDRY_META = {
    "hakke": {
        "display_name": "Häkke",
        "tagline": "Aggressive militarism — reliable, no-frills weapons designed for the front line.",
        "weapon_style": "Bullpup pulse rifles, double-shot fusion frames, kinetic SMGs. Foundry-style perk pool emphasizes Threat Detector + Surrounded + Outlaw.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=hakke",
    },
    "suros": {
        "display_name": "Suros",
        "tagline": "Precision engineering with futuristic styling — low recoil, smooth-shooting weapons that reward marksmanship.",
        "weapon_style": "Pulse / scout / auto rifles with the iconic red-and-white aesthetic. SUROS weapons favor precision archetypes with low-recoil patterns and high handling.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=suros",
    },
    "omolon": {
        "display_name": "Omolon",
        "tagline": "Energy-weapon specialists — fusion rifles, sidearms, and exotic-feel laser tech.",
        "weapon_style": "Heavy on fusion rifles and sidearms with the Omolon Fluid Dynamics origin trait (reload speed and stability ramp when shielded).",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=omolon",
    },
    "veist": {
        "display_name": "Veist",
        "tagline": "Bio-mechanical weapons — the Veist Stinger origin trait randomly refills the magazine from reserves on body damage.",
        "weapon_style": "Auto rifles, sniper rifles, sidearms. Veist Stinger origin trait is the foundry's calling card — sustained fire procs free-reloads.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=veist",
    },
    "tex_mechanica": {
        "display_name": "Tex Mechanica",
        "tagline": "Wild-west kinetic — hand cannons, lever-action rifles, and gambling-themed exotics that hit hard.",
        "weapon_style": "Hand cannons (the foundry's signature), lever-action scouts, and Stasis-themed lever pulses. Reward precise hits over volume of fire.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=tex-mechanica",
    },
    "daito": {
        "display_name": "Daito",
        "tagline": "Disciplined Eastern-styled weaponry — minimal output but recent additions to the catalog.",
        "weapon_style": "Sparse catalog (Bungie has only released a handful so far). Daito-branded weapons are typically scout rifles and SMGs with high range.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=daito",
    },
    "field_forged": {
        "display_name": "Field-Forged",
        "tagline": "Seasonal community-craftable weapons — generated in-fireteam from raw materials, no specific foundry parent.",
        "weapon_style": "Recent Bungie seasonal weapons that don't fall under a single foundry. Often craftable / Adept variants tied to specific seasons.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=field_forged",
    },
    "fotc": {
        "display_name": "Followers of the City",
        "tagline": "Niche faction-styled weapons — usually playlist-only or seasonal rewards.",
        "weapon_style": "Sparse, mostly Vanguard / Crucible / Gambit playlist drops carrying FotC branding.",
        "external_link": "https://www.light.gg/db/all-items/?weapon_foundry=fotc",
    },
}

# Bungie tierType code → human label
TIER_BY_CODE = {2: "Common", 3: "Uncommon", 4: "Rare", 5: "Legendary", 6: "Exotic"}

# Bungie damageType code → element label
ELEMENT_BY_CODE = {
    0: "Kinetic", 1: "Kinetic",  # 0=none / 1=kinetic (same effect)
    2: "Arc",     3: "Solar",     4: "Void",
    6: "Stasis",  7: "Strand",
}

BUNGIE_CDN = "https://www.bungie.net"


def find_manifest() -> Path | None:
    for p in MANIFEST_PATHS:
        if p.exists():
            return p
    return None


def extract_weapon(item: dict) -> dict | None:
    """Pull the fields we need from a single manifest weapon entry."""
    name = (item.get("displayProperties") or {}).get("name") or ""
    if not name:
        return None
    inv = item.get("inventory") or {}
    icon = (item.get("displayProperties") or {}).get("icon") or ""
    return {
        "name": name,
        "type": item.get("itemTypeDisplayName") or "",
        "element": ELEMENT_BY_CODE.get(item.get("defaultDamageType", 0), ""),
        "tier": TIER_BY_CODE.get(inv.get("tierType", 0), "?"),
        "tier_code": inv.get("tierType", 0),
        "icon_url": (BUNGIE_CDN + icon) if icon else "",
        "watermark": item.get("iconWatermark") or "",
        "flavor": (item.get("flavorText") or "").strip()[:200],
    }


def main():
    manifest_path = find_manifest()
    if not manifest_path:
        raise SystemExit(
            "Could not find DestinyInventoryItemDefinition.json. Looked at:\n  "
            + "\n  ".join(str(p) for p in MANIFEST_PATHS)
        )
    print(f"Reading manifest from {manifest_path} ...")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    by_foundry: dict[str, list[dict]] = defaultdict(list)
    seen_names: dict[str, set[str]] = defaultdict(set)  # dedupe per foundry by name

    for item in manifest.values():
        if item.get("itemType") != 3:           # only weapons
            continue
        if item.get("redacted"):                 # skip "Classified" entries
            continue
        for trait in item.get("traitIds") or []:
            if not trait.startswith("foundry."):
                continue
            foundry_key = trait[len("foundry."):]
            w = extract_weapon(item)
            if not w:
                continue
            if w["name"] in seen_names[foundry_key]:
                continue
            seen_names[foundry_key].add(w["name"])
            by_foundry[foundry_key].append(w)
            break  # one foundry tag per weapon

    print(f"\nFound {sum(len(v) for v in by_foundry.values()):,} unique foundry weapons "
          f"across {len(by_foundry)} foundries.")

    foundries_out: dict[str, dict] = {}
    for foundry_key, weapons in by_foundry.items():
        meta = FOUNDRY_META.get(foundry_key) or {
            "display_name": foundry_key.title(),
            "tagline":      f"{foundry_key.title()} foundry weapons (auto-extracted).",
            "weapon_style": "",
            "external_link": f"https://www.light.gg/db/all-items/?weapon_foundry={foundry_key.replace('_', '-')}",
        }

        # Sort by tier (Exotic > Legendary > Rare) then by watermark recency
        # (newer watermarks lexicographically later by filename hash).
        weapons_sorted = sorted(
            weapons,
            key=lambda w: (-(w["tier_code"] or 0), w["watermark"] or "", w["name"]),
        )
        exotics      = [w for w in weapons_sorted if w["tier_code"] == 6]
        legendaries  = [w for w in weapons_sorted if w["tier_code"] == 5]
        rares        = [w for w in weapons_sorted if w["tier_code"] == 4]

        # Bias "recent legendaries" toward ones with watermarks (sunset
        # weapons typically have empty watermark fields), then take 12.
        with_watermark = [w for w in legendaries if w["watermark"]]
        recent_legendaries = (with_watermark[:12] or legendaries[:12])

        foundries_out[foundry_key] = {
            **meta,
            "weapon_counts": {
                "total":     len(weapons),
                "exotic":    len(exotics),
                "legendary": len(legendaries),
                "rare":      len(rares),
            },
            "exotics":            exotics,
            "recent_legendaries": recent_legendaries,
            "all_weapons":        weapons_sorted,
        }

        print(
            f"  {foundry_key:15s} "
            f"total={len(weapons):3d}  "
            f"exotic={len(exotics):2d}  "
            f"legendary={len(legendaries):3d}  "
            f"rare={len(rares):2d}"
        )

    out = {
        "version":      "2.0",
        "last_curated": time.strftime("%Y-%m-%d"),
        "_notes":       (
            "AUTO-GENERATED by darth-bot/kb/scrape_foundries.py from the "
            "Bungie DestinyInventoryItemDefinition manifest. Do not hand-edit. "
            "Re-run the script whenever Bungie pushes a new manifest "
            "(typically each Episode or hotfix). Sources every weapon's "
            "foundry tag from manifest traitIds — fully automated, no "
            "community scraping or hand-curation."
        ),
        "source":       "DestinyInventoryItemDefinition.json (traitIds.foundry.*)",
        "foundries":    foundries_out,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
