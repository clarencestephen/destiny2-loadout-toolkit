"""
mod_recommender.py
==================
Curated mod / armor recommendations based on:
  - build goals       (DPS, Survivability, Fun, PvP, PvE, PvP+PvE, Weapon-swap)
  - armor archetype   (Bulwark, Brawler, Grenadier, Paragon, Specialist, Gunner)
  - primary class     (Hunter, Titan, Warlock)

Used by setup.py and setup_gui.py to seed the MOD REFERENCE sheet with
recommended mods after the user's config is captured.

This is a STARTER set. Game patches, seasonal artifacts, and personal
preference will all shift the meta. Treat suggestions as a starting point
and tune from there. Open a PR with updates anytime.
"""

# Build goals — user picks 1+ from this list during setup
GOALS = [
    "DPS",
    "Survivability",
    "PvE",
    "PvP",
    "PvP+PvE blend",
    "Fun / Off-meta",
    "Weapon-swap only",
]

# Recommended armor mods per slot, keyed by build goal.
# Keys: helmet / gauntlets / chest / legs / class_item.
# Format: list of mod names in priority order; pick top-N that fit your energy.
MOD_RECOMMENDATIONS = {
    "DPS": {
        "helmet":     ["Heavy Ammo Finder", "Heavy Ammo Scout", "Targeting (match heavy)", "Hands-On"],
        "gauntlets":  ["Loader (match heavy)", "Heavy Handed", "Grenade Kickstart"],
        "chest":      ["Weapon Surge x4 (match damage type)", "Concussive Dampener", "Sniper Resistance"],
        "legs":       ["Recuperation", "Stacks on Stacks", "Innervation", "Absolution"],
        "class_item": ["Powerful Attraction", "Bomber", "Outreach", "Distribution"],
    },
    "Survivability": {
        "helmet":     ["Heavy Ammo Finder", "Recuperation", "Hands-On"],
        "gauntlets":  ["Heavy Handed", "Grenade Kickstart", "Impact Induction"],
        "chest":      ["Resistance mods x4 (match incoming damage)", "Concussive Dampener", "Sniper Resistance"],
        "legs":       ["Recuperation", "Better Already", "Absolution", "Innervation"],
        "class_item": ["Powerful Attraction", "Bomber", "Special Finisher"],
    },
    "PvE": {
        "helmet":     ["Heavy Ammo Finder", "Heavy Ammo Scout", "Hands-On"],
        "gauntlets":  ["Loader (match primary)", "Heavy Handed", "Grenade Kickstart"],
        "chest":      ["Surge x4 (match subclass element)", "Concussive Dampener"],
        "legs":       ["Recuperation", "Stacks on Stacks", "Innervation"],
        "class_item": ["Powerful Attraction", "Bomber / Outreach", "Distribution"],
    },
    "PvP": {
        "helmet":     ["Targeting (match primary)", "Hands-On", "Special Ammo Finder"],
        "gauntlets":  ["Loader (match primary)", "Dexterity (match secondary)"],
        "chest":      ["Unflinching (match primary)", "Concussive Dampener"],
        "legs":       ["Better Already", "Recuperation", "Absolution"],
        "class_item": ["Special Finisher", "Powerful Attraction"],
    },
    "PvP+PvE blend": {
        "helmet":     ["Heavy Ammo Finder", "Targeting (match primary)", "Hands-On"],
        "gauntlets":  ["Loader (match primary)", "Heavy Handed"],
        "chest":      ["Surge x2 (subclass) + 2 Resistance", "Concussive Dampener"],
        "legs":       ["Recuperation", "Better Already", "Innervation"],
        "class_item": ["Powerful Attraction", "Bomber", "Distribution"],
    },
    "Fun / Off-meta": {
        "helmet":     ["Whatever matches your gimmick (e.g. Special Ammo Finder for shotguns)"],
        "gauntlets":  ["Heavy Handed", "Impact Induction"],
        "chest":      ["Surge x4 (match your shenanigan element)"],
        "legs":       ["Recuperation", "Stacks on Stacks"],
        "class_item": ["Powerful Attraction", "Bomber"],
    },
    "Weapon-swap only": {
        "helmet":     ["Heavy Ammo Scout", "Heavy Ammo Finder"],
        "gauntlets":  ["Loader (match heavy)", "Dexterity (match secondary)", "Heavy Handed"],
        "chest":      ["Weapon Surge x4 (match heavy)", "Unflinching (match primary)"],
        "legs":       ["Recuperation", "Stacks on Stacks"],
        "class_item": ["Powerful Attraction", "Special Finisher"],
    },
}

# Per-class fragment / aspect hints by archetype focus stat
CLASS_HINTS = {
    "Hunter": {
        "Grenade":  "Threadrunner Strand + Threaded Specter; or Voidwalker analog via Gyrfalcons",
        "Melee":    "Liar's Handshake Arc + One-Two Punch; or Combination Blow Strand",
        "Super":    "Celestial Nighthawk Solar Golden Gun; Star-Eater Scales for any super",
        "Class":    "Caliban's Hand or Knucklehead Radar — both extend Dodge utility",
        "Health":   "Wormhusk Crown for instant heal on Dodge",
        "Weapons":  "Lucky Pants Hand Cannon DPS; Aeon Swift for fireteam buff",
    },
    "Titan": {
        "Grenade":  "Wishful Ignorance + Suspending grenades; Pyrogale Solar burn",
        "Melee":    "Synthoceps + Shoulder Charge / Throwing Hammer / Knockout",
        "Super":    "Cuirass of the Falling Star Thundercrash; Pyrogale Burning Maul",
        "Class":    "Citan's Ramparts breach barricade; Helm of Saint-14",
        "Health":   "Hoarfrost-Z Stasis crystal wall; Loreley Splendor Solar restoration",
        "Weapons":  "Heart of Inmost Light buff cycling; Aeon Safe for fireteam buff",
    },
    "Warlock": {
        "Grenade":  "Sunbracers Solar grenade spam; Osmiomancy Stasis turret freeze",
        "Melee":    "Karnstein Armlets melee restoration; Necrotic Grip poison spread",
        "Super":    "Star-Eater Scales any super; Crown of Tempests Stormcaller chain",
        "Class":    "Phoenix Protocol Well of Radiance refill; Boots of the Assembler Lumina aura",
        "Health":   "Boots of the Assembler heal aura; Karnstein Armlets",
        "Weapons":  "Getaway Artist Arc soul + buddy DPS; Aeon Soul fireteam buff",
    },
}


def recommend(goals, archetype, class_name):
    """
    Return a dict with recommended mods per armor slot + class-specific hints.

    Args:
        goals: list of strings from GOALS
        archetype: one of Bulwark / Brawler / Grenadier / Paragon / Specialist / Gunner
        class_name: Hunter / Titan / Warlock

    Returns:
        dict with keys:
          'mods': {slot: [mod list]} — deduped, prioritized by first appearance
          'class_hint': str — short tip for this class + archetype combo
    """
    archetype_to_stat = {
        "Bulwark":    "Health",
        "Brawler":    "Melee",
        "Grenadier":  "Grenade",
        "Paragon":    "Super",
        "Specialist": "Class",
        "Gunner":     "Weapons",
    }
    primary_stat = archetype_to_stat.get(archetype, "Grenade")

    if not goals:
        goals = ["PvE"]

    merged = {"helmet": [], "gauntlets": [], "chest": [], "legs": [], "class_item": []}
    seen = {slot: set() for slot in merged}
    for goal in goals:
        block = MOD_RECOMMENDATIONS.get(goal, {})
        for slot, mods in block.items():
            for m in mods:
                if m not in seen[slot]:
                    merged[slot].append(m)
                    seen[slot].add(m)

    hint = CLASS_HINTS.get(class_name, {}).get(primary_stat,
        "No specific exotic hint for this class + stat combo — pick exotic by activity.")

    return {"mods": merged, "class_hint": hint, "primary_stat": primary_stat}


if __name__ == "__main__":
    # Quick demo
    import json
    rec = recommend(["DPS", "PvE"], "Grenadier", "Warlock")
    print(json.dumps(rec, indent=2))
