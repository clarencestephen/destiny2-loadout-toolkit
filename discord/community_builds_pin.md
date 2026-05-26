# `#destiny-voyager` — Community Builds pin

Pinned message in the `#destiny-voyager` channel. Holds the content that
Bungie's About filter rejected (see `clan_creation.md` lessons-learned).

Post as a Discord **embed** with Sith Purple (`#B432FF`) accent, matching
the brand pattern used by `#welcome` and `#imperial-law`.

**Embed title:** `▲ COMMUNITY BUILDS`
**Color:** `#B432FF` (Sith Purple)
**Footer:** `Order 66 · community-builds · v1` *(idempotency marker — bump
to `v2` if `setup_server.py` re-posts)*

**Body:**

```
Two open Destiny 2 tools made for Order 66 — and for anyone who wants
to help shape them:

🌌  **Destiny Voyager**
Loadout optimizer · wishlist organizer · Bungie API stats tracker. The
companion web app for the clan.
→ https://destiny-voyager.clarencestephen.com

🤖  **Darth Bot**
The AI assistant living in this Discord. Answers build, raid, and
catalyst questions using your real inventory + Bungie's manifest +
scraped raid wikis. Local LLM (Qwen3 via Ollama) + RAG pipeline,
running on a homelab box.

Try: `/sanity`  `/ask`  `/build`  `/raid`  `/catalyst`  or @-mention
Darth Bot in any allowed channel.

**How you help**
• Just use the bot — every question helps us tune the retrieval and
  catch hallucinations
• AI / ML / LLM curious? Drop questions in #engineering-bay — happy
  to walk through the RAG pipeline, the embeddings, the manifest
  cache, the works
• Code contributor? GitHub: https://github.com/clarencestephen/destiny-voyager

Both projects are in active development. The clan is the test bed,
the feedback loop, and the reason we built them in the first place.
```

---

## Why this lives here and not in the Bungie About

Bungie's automated content filter blocks external tool/service URLs in
the clan About field. See `clan_creation.md` § Lessons learned.

This pin is the canonical place to point new members for Destiny Voyager
and Darth Bot context. Reference it from:

- `#welcome` (Imperial Transmission embed) — already mentions Destiny
  Voyager + Charlemagne; add a `📌 see pinned in #destiny-voyager`
  line on the next marker bump
- `#bounty-office` — when promoting `@Padawan` → `@Imperial Trooper`,
  mods can point to this pin so new clan members see the tools
- `#engineering-bay` — for the AI/ML-curious crowd; this is where the
  technical conversation actually happens

## Posting the pin

Option 1 — manual (fastest):
1. Open `#destiny-voyager`
2. Paste the body above as a regular message (Discord doesn't let
   users post rich embeds without a bot — markdown rendering is fine)
3. Right-click → Pin Message

Option 2 — via `setup_server.py` (idempotent, brand-consistent):
1. Add a `COMMUNITY_BUILDS_BODY` constant to `messages.py` with the
   body string above
2. Add a `COMMUNITY_BUILDS_MARKER = "Order 66 · community-builds · v1"`
3. Wire a new step in `setup_server.py` that posts to `#destiny-voyager`
   with the same idempotency pattern used by `#welcome` and `#imperial-law`
4. Re-run `python3 discord/setup_server.py`
