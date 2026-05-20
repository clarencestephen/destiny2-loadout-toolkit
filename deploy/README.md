# Deployment

Infrastructure-as-code for the Destiny Voyager unified stack.

## Components

| Component | Location | Deploys via |
|---|---|---|
| FastAPI backend | Hostinger VPS `187.77.200.241` :80 → uvicorn :8080 | `deploy/install_backend.sh` |
| Web frontend | Cloudflare Pages, custom domain | `cd web && pnpm build && wrangler pages deploy dist` |
| Worker API | Cloudflare Workers, custom route | `cd web/worker && wrangler deploy` |
| Discord bot (Darth Bot) | Runs locally on the user's WSL box | `python3 -m darth-bot.bot` |

The web → backend hop goes via the Worker, which holds the session cookie
and proxies `/api/chat`, `/api/meta/*`, `/api/manifest/*`, `/api/link/complete`
to the backend (see `web/worker/src/index.ts`, function `proxyToBackend`).

## Backend (VPS) — first install

```bash
scp deploy/install_backend.sh root@187.77.200.241:/tmp/
ssh root@187.77.200.241 bash /tmp/install_backend.sh
ssh root@187.77.200.241 curl -s http://localhost/health
```

Script is idempotent — re-run after every push to update.

## Backend — DNS + TLS (one-time)

1. In Cloudflare DNS for `clarencestephen.com`, add:
   ```
   Type: A    Name: api.destiny-voyager    Content: 187.77.200.241    Proxied: OFF
   ```
   (Proxied OFF so certbot can issue a Let's Encrypt cert.)
2. Wait for propagation (~1 min), then:
   ```bash
   ssh root@187.77.200.241 certbot --nginx -d api.destiny-voyager.clarencestephen.com \
        --agree-tos --redirect -n -m clarence.stephen@gmail.com
   ```
3. Turn Cloudflare proxy back ON if you want CF-level DDoS protection.
   Set encryption mode to "Full (strict)" so CF→origin uses the LE cert.

## Worker — first deploy

```bash
cd web/worker
# Set the secret pointing at the backend
echo "https://api.destiny-voyager.clarencestephen.com" | wrangler secret put BACKEND_BASE_URL
wrangler deploy
```

For local dev (Worker → local backend):
```bash
# In one terminal:
cd backend && uvicorn main:app --reload --port 8080

# In another:
cd web/worker && wrangler dev --var BACKEND_BASE_URL:http://localhost:8080
```

## Web (Cloudflare Pages) — first deploy

```bash
cd web
pnpm install
pnpm build
wrangler pages deploy dist --project-name destiny-voyager
```

Then in CF dashboard → Pages → Custom domains, add `destiny-voyager.clarencestephen.com`.

## Discord bot — point at backend

Append to `/home/cs/.env`:

```bash
BACKEND_BASE_URL=https://api.destiny-voyager.clarencestephen.com
```

Restart the bot. `/sanity` will show the backend reachability probe.

## Verification checklist

```bash
# 1. Backend public health
curl https://api.destiny-voyager.clarencestephen.com/health

# 2. Worker proxy reaches backend
curl https://destiny-voyager.clarencestephen.com/api/meta/state | jq .state.expansion

# 3. Discord bot sees backend
# In Discord: /sanity
# Expected line: "Backend (https://api...): ✅"
```
