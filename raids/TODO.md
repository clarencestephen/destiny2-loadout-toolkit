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

Per-encounter cross-reference using WebFetch against:
- Bungie help articles (mechanic clarifications, known issues)
- Datto / Esoterickk written-form guides
- r/raidsecrets pinned megathreads (already scraped, supplemental tier)

Conflict on mechanics → document BOTH as `permutations:`, never pick a winner silently.

---

## 🎥 Pass-3 YouTube enrichment

Curate creator-specific video IDs per activity (Datto, Esoterickk, Salvager,
Skarrow9), pull transcripts via `youtube-transcript-api`, embed into KB
under `data/scrape/youtube/<activity-slug>/`. NOT a source of truth — just
extra signal for the bot's RAG retrieval.
