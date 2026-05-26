# Manual TODO — Raids + Dungeons

Things the user is doing by hand. Bot/scraper should leave these slots alone.

---

## 🖼  Images (user uploading 2026-05-23)

**Source:** raid maps/images coming from a Discord sherpa server the user joined — same artist/style across all raids, so visual language stays consistent across the toolkit. Reddit has some but they're inconsistent in style — prefer the Discord set.

Per-encounter images (maps, callout diagrams, platform reference, hidden chest landmarks) drop into:

```
raids/images/<activity-slug>/<encounter-slug>/
   ├── overview.png            ← whole-encounter map / arena layout
   ├── setup.png               ← what you see on pull
   ├── callouts.png            ← annotated callout positions
   ├── damage-phase.png        ← DPS positioning
   └── hidden-chest.png        ← landmark for hidden chest (if any)
```

YAMLs reference them via the `images:` block on each encounter:

```yaml
images:
  overview:     "images/root-of-nightmares/cataclysm/overview.png"
  setup:        ""
  callouts:     ""
  damage_phase: ""
  hidden_chest: ""
```

Image slots are pre-reserved with `""` so the user can drop files in
and update the YAML in one pass without restructuring.

**Status:** all encounters have empty image slots awaiting upload.

---

## 📝 Pass-2 synthesis re-pass (after Pass-1 destinypedia baseline)

**Reality check from the Root of Nightmares Pass-2 pilot (2026-05-25):**

The original Pass-2 plan assumed multiple Tier-1 *written* mechanics
sources. After actually running it, the web source landscape is:

| Source | What it actually has | Authority for |
|---|---|---|
| destinypedia | mechanics + lore (Pass-1 baseline) | mechanics (Tier 1) |
| blueberries.gg | loot tables + master challenges | loot + challenges (Tier 1 for those) |
| help.bungie.net | platform / account / known-issue | nothing raid-specific |
| Datto / Esoterickk / Skarrow9 | YouTube only | unlocks via Pass-3 transcripts |
| IGN / Polygon / KontrolFreek | edited gaming media | Tier 3 (general reference) |
| r/raidsecrets | community megathreads | cheese + secret chests (Tier 2) |

So **Pass-2 deliverable** is now:

1. **Loot table fix** — cross-check `potential_drops` against
   blueberries.gg. Pass-1 numbers were partial / wrong for several
   encounters (caught in RoN: Cataclysm had Rufus's Fury listed; it's
   actually Briar's Contempt + Koraxis + Nessa's).
2. **Master Challenge data** — NEW `master_challenge:` block per
   encounter, from blueberries challenges page.
3. **Cheese + secret chests** — from r/raidsecrets megathreads (already
   scraped to `darth-bot/data/scrape/reddit-raidsecrets/`).
4. **Mechanics depth** → DEFERRED to Pass-3 (YouTube transcripts).

Don't expect blueberries / Bungie help to corroborate mechanics —
they don't have them in written form. Document Tier-1 mechanics
disputes as `permutations:` ONLY when destinypedia is internally
contradictory; for everything else, the destinypedia baseline holds
until Pass-3 lands.

**Activities pending Pass-2:**
- ✅ Root of Nightmares (this pass)
- ⬜ Salvation's Edge, Desert Perpetual, Vow of the Disciple, Deep Stone
  Crypt, Garden of Salvation, Last Wish, King's Fall, Vault of Glass,
  Crota's End
- ⬜ All 10 dungeons

---

## 🎥 Pass-3 YouTube enrichment

Curate creator-specific video IDs per activity (Datto, Esoterickk, Salvager,
Skarrow9), pull transcripts via `youtube-transcript-api`, embed into KB
under `data/scrape/youtube/<activity-slug>/`. NOT a source of truth — just
extra signal for the bot's RAG retrieval.
