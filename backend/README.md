# Destiny Voyager — Python Backend

FastAPI service that exposes the shared core (`router`, `kb`, `manifest`,
`meta_state`, `inventory`, `twab_scraper`) as HTTP endpoints. Consumed
by two clients:

- **Darth Bot (Discord)** — Python; can also import the core directly,
  but uses the API for inventory-aware commands that need cross-service
  state (Discord user → Bungie membership_id linking).
- **Destiny Voyager (web)** — Cloudflare Worker (`web/worker/`) calls
  these endpoints over HTTP. Worker owns OAuth + KV sessions; this
  service owns LLM/KB/manifest.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET    | `/health` | Liveness probe |
| POST   | `/chat` | Run the router on a question; returns full answer + sources |
| GET    | `/manifest/lookup?q=` | Manifest search (item names) |
| GET    | `/manifest/extract?text=` | Extract item names from arbitrary text |
| GET    | `/meta/state` | Current meta_state.json content (for web display) |
| GET    | `/meta/twab` | Most-recent Bungie RSS items |
| POST   | `/inventory/analyze` | Compare a user's inventory vs current PvP/PvE meta |
| POST   | `/link/start` | Begin Discord ↔ Bungie link (generates one-time code) |
| POST   | `/link/complete` | Finish the link (called from web after Bungie OAuth) |
| GET    | `/link/discord/{discord_id}` | Resolve Discord user → Bungie membership_id |

## Auth

Endpoints that act on a specific user (`/inventory/analyze`, `/link/*`)
expect a session header set by the web Worker:

    X-Session-Id: <kv-session-id>

The Worker validates the cookie, then forwards `X-Session-Id` to this
service. This service trusts the Worker (network-level boundary).

`/chat`, `/manifest/*`, `/meta/*` are unauthenticated public reads.

## Running locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

The service reads from the darth-bot module (sibling directory) via
sys.path. Make sure darth-bot is configured (env vars set, manifest
cache populated).

## Deployment

Target: **Hostinger VPS**.

```bash
# On the VPS (one-time):
git clone https://github.com/clarencestephen/destiny-voyager
cd destiny-voyager/backend
pip install -r requirements.txt

# Systemd unit at /etc/systemd/system/destiny-voyager-backend.service:
#   ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8080
#   WorkingDirectory=/path/to/destiny-voyager/backend

# Nginx reverse-proxy on the VPS forwards api.destiny-voyager.clarencestephen.com → 8080.
```

The Cloudflare Worker (`web/worker/`) is configured with the public
backend URL via `BACKEND_BASE_URL` in `wrangler.toml`.

## Token store

Discord ↔ Bungie link mappings live in SQLite (`backend/data/links.db`)
locally. In production on the VPS, this should be Postgres or, better,
shared with the Worker's Cloudflare KV via the KV REST API.
