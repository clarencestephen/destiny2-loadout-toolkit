# Darth Bot

A Destiny 2 chatbot for the DARTH_BANKAI Discord — answers in the brand voice, draws on your real vault, and isn't allergic to specifics.

> *"The dark side has better frame rates."*

---

## What it does

| Question | How it answers |
|---|---|
| *"How do I get Crimson catalyst?"* | KB lookup on light.gg + manifest description + live search for current quest steps. |
| *"Good PvP build with my current weapons?"* | Pulls your **real inventory** from `destiny-voyager/user_config.json` and recommends based on what you actually own. |
| *"Summarize Salvation's Edge encounters."* | KB lookup on destinypedia / scraped raid guides. |
| *"Easiest solo ops map?"* | Live Brave search — meta changes weekly. |
| *"Why do I keep dying?"* | Asks ONE clarifying follow-up instead of guessing. |
| *"Is there an all black shader?"* | Manifest fuzzy lookup + live search. |
| *"How do I jump better?"* | KB on class-specific jump mechanics. |
| *"What should I do next?"* | Inventory-aware advisory — looks at what you have unlocked, what's tagged. |

---

## Architecture

```
Discord question
   │
   ▼
router.py        ← classifies: build / quest / raid / cosmetic / advisory / etc.
   │
   ├── inventory.py   ←  reads Destiny Voyager user_config.json + INVENTORY sheet
   ├── kb/manifest.py ←  Bungie manifest cached by destiny-voyager/decode_dim.py
   ├── kb/retrieve.py ←  chromadb top-K over scraped light.gg / reddit / destinypedia
   └── search.py      ←  Brave Search API (free 2k/mo) for current meta
   │
   ▼
llm.py           ←  Qwen 3 8B via ollama
   │
   ▼
Discord response (chunked if long)
```

Everything but the ChromaDB embeddings runs locally. No data leaves your machine unless you opt into Brave Search.

---

## Setup

### 1. Install ollama and pull the model

```bash
# https://ollama.com/download (one binary)
ollama pull qwen3:8b
ollama serve   # runs at http://localhost:11434
```

### 2. Install Python deps

```bash
cd darth-bot
pip install -r requirements.txt
```

### 3. Create a Discord bot

Same flow as the other bots in this repo:
1. https://discord.com/developers/applications → New Application → name it "Darth Bot"
2. Bot tab → Reset Token → copy
3. OAuth2 → URL Generator → scopes `bot` + `applications.commands`
4. Bot Permissions: `Send Messages`, `Read Message History`, `Use Slash Commands`, `Embed Links`
5. Invite to your server with the generated URL

### 4. Set env vars

Append to `/home/cs/.env`:
```bash
DARTH_BOT_DISCORD_TOKEN=<your_bot_token>
# DISCORD_GUILD_ID is already set to your server
BRAVE_SEARCH_API_KEY=<optional — sign up at api.search.brave.com for 2k free/mo>
```

Mirror in `/mnt/a/master_secrets.md` per your secrets workflow.

### 5. Populate the knowledge base (one-time, ~15-30 min)

```bash
# Scrape ~100 light.gg pages, ~100 top reddit posts, 9 raid wiki pages
python3 -m darth-bot.kb.scrape --all

# Chunk + embed into chromadb (~5 min)
python3 -m darth-bot.kb.embed
```

Both are re-runnable. The scraper is polite (1.2s between requests) — let it cook.

The Bungie manifest is already cached by `destiny-voyager/decode_dim.py`, so the bot uses that directly with no extra setup.

### 6. Run it

```bash
python3 -m darth-bot.bot
```

In Discord:
- `/sanity` — verify ollama + kb + inventory are reachable
- `/ask <question>` — any Destiny question
- `/build <activity>` — uses your inventory
- `/raid <name>` — encounter rundown
- `/catalyst <weapon>` — quest steps
- `@Darth Bot <question>` — mention from any allowed channel

---

## Channels it answers in

Restricted to: `destiny-voyager`, `smugglers-cache`, `engineering-bay`, `trooper-comms`, `the-cantina`, `lfg-storyline`, `lfg-raids`, `lfg-dungeons`. Edit `ALLOWED_CHANNEL_NAMES` in `config.py` to expand.

---

## Files

```
darth-bot/
├── README.md                — this file
├── requirements.txt
├── __init__.py
├── bot.py                   — Discord entry + slash commands
├── config.py                — env vars + constants
├── llm.py                   — Qwen via ollama (sync + streaming)
├── router.py                — classifier + orchestrator
├── inventory.py             — reads Destiny Voyager cache
├── search.py                — Brave Search wrapper
├── kb/
│   ├── __init__.py
│   ├── manifest.py          — Bungie manifest lookup
│   ├── scrape.py            — one-time scrapers (light.gg, reddit, destinypedia)
│   ├── embed.py             — chunk + embed into chromadb
│   └── retrieve.py          — top-K retrieval
├── prompts/
│   └── system.md            — DARTH_BANKAI brand voice system prompt
└── data/                    — gitignored
    ├── chroma/              — vector store
    └── scrape/              — raw scraped markdown
```

---

## Roadmap

- **v0.2** — streaming responses (edit message as tokens arrive)
- **v0.3** — `/farm <exotic>` with weekly RNG calculator
- **v0.4** — multi-turn conversation memory (per-user, ephemeral)
- **v0.5** — voice mode via Voxta integration (you already have it set up)
- **v0.6** — proactive: weekly reset announcement post each Tuesday
