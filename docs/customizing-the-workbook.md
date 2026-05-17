# Customizing the workbook

Every sheet in `my_loadouts.xlsx` is meant to be edited. Here's a sheet-by-sheet rundown of what's safe to change and what's auto-managed.

---

## `START HERE`

- **Safe to edit:** anything. This is just onboarding text.
- **Auto-managed:** no.

---

## `PRIORITIES`

Your exotic chase list + campaign queue + farming routes + grinding mechanics + current mod section. Ships with empty tables and one or two example rows (italic grey).

- **Safe to edit:** every cell. Replace the example rows with your own priorities.
- **Auto-managed:** no.

---

## `EXOTIC MISSIONS`

10 seeded missions covering current rotation + legacy farms. Columns: `#`, `Mission`, `Exotic Reward`, `Source`, `Status`, `Priority`, `Steps / Notes`.

- **Safe to edit:** Status (`TODO` / `In Progress` / `DONE` / `Optional`), Priority (1 = highest), Notes.
- **Add rows:** any new exotic mission Bungie releases — just append.
- **Auto-managed:** no (the seed list is only inserted on first workbook creation).

---

## `WISHLIST`

DIM-CSV-compatible columns: `#`, `Name`, `Tier`, `Type`, `Element / Subclass`, `Source`, `Owned?`, `Notes / Desired Roll`.

- **Safe to edit:** any cell. Easiest workflow is to export your DIM CSV (see `getting-dim-csv-export.md`) and paste rows in.
- **Auto-managed:** no.

---

## `HUNTER BUILDS` / `TITAN BUILDS` / `WARLOCK BUILDS`

One row per build. Columns: `#`, `Build Name`, `Subclass`, `Exotic Armor`, `Kinetic`, `Energy`, `Heavy`, `Notes / Activity`.

Each sheet ships with 3 italic-grey **example** rows showing the format. Replace them with your own.

- **Safe to edit:** every cell.
- **Auto-managed:** no.
- **Tip:** if a build also has a DIM share URL, add that URL via `python add_loadout.py` — the decoder will produce a full breakdown in `DIM LOADOUTS (FULL)`.

---

## `MOD REFERENCE`

Has three sections:

1. **Your build focus** (auto-populated from your `user_config.json` — archetype, goals, primary class)
2. **Recommended armor mods** (auto-populated from `mod_recommender.py` based on goals + archetype)
3. **Artifact perks** + **stats** + **per-piece energy** (empty — fill in each season)

- **Safe to edit:** every cell, including the recommendations.
- **Auto-managed:** sections 1 and 2 are regenerated each time you run `init_workbook.py`. To refresh the recommendations after changing your goals/archetype, edit `user_config.json` and re-run `python init_workbook.py` — but be warned, that wipes any manual edits to this sheet.
- **Want a different recommendation set?** Edit `mod_recommender.py` and PR your changes.

---

## `DIM LOADOUTS (FULL)`

**Do not edit by hand.** This sheet is overwritten in full every time you run `python decode_dim.py`. Any manual edits will be lost.

To update what shows here:
- Add/remove DIM URLs in `user_config.json` (or use `python add_loadout.py`)
- Edit the source loadout in DIM itself
- Re-run `python decode_dim.py`

---

## Backing up before regenerating

If you want to rebuild the template from scratch (e.g., after a major schema update) but keep your customizations:

1. Copy `my_loadouts.xlsx` to `my_loadouts_backup.xlsx` first
2. Run `python init_workbook.py` (it'll ask before overwriting — answer `y`)
3. Open both files side-by-side and copy your edits across

---

## Customizing colors / styling

The workbook uses three class colors (`HEX`):
- Hunter — `#2563EB` (blue)
- Titan — `#DC2626` (red)
- Warlock — `#7C3AED` (purple)

Plus a neutral dark `#111827` for section headers and `#F59E0B` for accent. Edit these constants at the top of `init_workbook.py` and regenerate.
