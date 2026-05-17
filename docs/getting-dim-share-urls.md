# Getting DIM Share URLs

DIM (Destiny Item Manager) lets you share any saved loadout as a public URL. This toolkit decodes those URLs into a readable `DIM LOADOUTS (FULL)` sheet with every weapon / armor / mod / aspect / fragment resolved by name.

---

## Steps

1. Open DIM at **<https://app.destinyitemmanager.com>**
2. Sign in with your Bungie account (top right)
3. Click the **Loadouts** tab in the top nav
4. Pick a character — your saved loadouts appear in the left rail
5. **Click a loadout** to open its detail view
6. Click the **Share** button (top of the loadout view) → **Copy URL**
7. You'll have a link like:
   ```
   https://dim.gg/abc1234/Raid
   ```
8. Paste that into `setup.py` / `setup_gui.py` / `add_loadout.py` when prompted

Repeat for each loadout you want decoded. There's no limit.

---

## What gets resolved

The decoder pulls:

- **Equipped weapons** (kinetic / energy / heavy) → name
- **Equipped armor** (helmet / gauntlets / chest / legs / class item) → name
- **Subclass** + **aspects / fragments / supers / grenades / melees** → names
- **Armor mods** (`parameters.mods`) → names
- **Per-piece artifice mods** (`parameters.modsByBucket`) → names per slot

All of this lands in the `DIM LOADOUTS (FULL)` sheet, one section per loadout.

---

## What does NOT get resolved

- **Stats / power level** — DIM share URLs don't include them; they're a property of the specific instanced item.
- **Specific perk rolls on weapons** — share URLs reference items by base hash, not instance ID. Two Fatebringers with different perk rolls share the same hash.
- **Vault / inventory contents** — share URLs only encode what's *in the loadout*, not what's in your vault. For inventory tracking, use DIM's CSV export (see [getting-dim-csv-export.md](getting-dim-csv-export.md)).

---

## Troubleshooting

**"Could not find loadout in {url}"** — DIM occasionally changes its share page format. The decoder uses two terminators (`"` and `)`); if both fail, open an issue with the failing URL and we'll patch.

**The URL works but item names show as `?(12345)`** — that item's hash isn't in the manifest. Re-run `python decode_dim.py` and let it refresh the manifest cache; or delete `manifest_cache/` to force a clean re-download.

**`URLError: <urlopen error>`** — your computer can't reach `dim.gg` or `bungie.net`. Check your firewall / VPN / corporate proxy.
