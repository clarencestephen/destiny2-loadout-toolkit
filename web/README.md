# Destiny Voyager — Web

Cloudflare Pages + Workers + KV. **Free at clan scale, $5/mo if it grows.**

> *"The dark side has better frame rates."*

---

## Stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | Vite + React + TypeScript + Tailwind + shadcn/ui patterns | Modern, fast, ages well |
| Backend | Cloudflare Worker (Hono) | 100k req/day free |
| Storage | Cloudflare KV | 1k writes/day free; users barely write |
| Auth | Bungie OAuth (PKCE) | No password, refresh tokens server-side |
| Hosting | Cloudflare Pages | Free, custom domain, auto-deploy from main |

## Layout

```
web/
├── index.html                 entry
├── vite.config.ts
├── tailwind.config.js          DARTH_BANKAI palette
├── package.json
├── src/
│   ├── main.tsx                router root
│   ├── App.tsx                  shell + nav
│   ├── styles.css               cosmic backdrop
│   ├── pages/
│   │   ├── Landing.tsx          public landing + Sign in with Bungie
│   │   └── Dashboard.tsx        authed inventory grid
│   ├── components/
│   │   ├── BrandMark.tsx        Vader-helmet-in-triangle SVG
│   │   └── ui/                  shadcn-style primitives
│   └── lib/
│       ├── api.ts               typed fetch wrapper
│       └── utils.ts             cn() helper
└── worker/
    ├── wrangler.toml
    ├── package.json
    └── src/
        ├── index.ts             Hono router + endpoints
        ├── auth.ts              OAuth PKCE
        └── bungie.ts            X-API-Key wrapper
```

## Local dev

```bash
# In one terminal — Worker
cd web/worker
npm install
wrangler dev          # serves on :8787

# In another — Vite
cd web
npm install
npm run dev           # serves on :5173, proxies /api → :8787
```

Open http://localhost:5173. The Worker requires Bungie credentials — see **Secrets** below.

## First-time Cloudflare setup

```bash
# Log in to Cloudflare (browser auth)
wrangler login

# Create the KV namespace and copy the id into worker/wrangler.toml
cd web/worker
wrangler kv namespace create destiny-voyager        # production
wrangler kv namespace create destiny-voyager --preview   # local dev

# Drop the secrets (these prompt for input; nothing lands in git)
wrangler secret put BUNGIE_API_KEY                   # 169c1864... (your key)
wrangler secret put BUNGIE_CLIENT_ID                 # 52250
wrangler secret put BUNGIE_CLIENT_SECRET             # only if Confidential client; else skip
wrangler secret put SESSION_SECRET                   # any 32+ char random string

# Deploy the worker
wrangler deploy

# Then deploy the Pages frontend
cd ..
npm run build
wrangler pages deploy dist --project-name=destiny-voyager
```

## DNS + routes

After first Worker deploy, attach a custom route in the Cloudflare dashboard:

1. **Workers → destiny-voyager-api → Triggers → Add Custom Domain**
   Route: `destiny-voyager.clarencestephen.com/api/*`

2. **Pages → destiny-voyager → Custom domains → Add**
   Add: `destiny-voyager.clarencestephen.com`

Both will auto-issue TLS certs.

## Bungie portal updates

Once the deploy is live, update the Bungie app at https://www.bungie.net/en/Application:

- **Redirect URL:** `https://destiny-voyager.clarencestephen.com/api/auth/callback`
- **Origin Header:** `https://destiny-voyager.clarencestephen.com` (or leave blank if your client type is Public)

## Auto-deploy on push

`wrangler` supports a GitHub integration. Tutorial:
1. Go to Cloudflare dashboard → Workers & Pages → Pages → destiny-voyager → Settings → Builds & deployments → Connect to Git
2. Pick the `clarencestephen/order-66` repo, branch `main`, root directory `web`
3. Build command: `npm install && npm run build`
4. Output directory: `dist`

For the Worker side: install the `@cloudflare/wrangler-action` GitHub Action in `.github/workflows/`.

## What's NOT in v0.1 (yet)

- `/api/inventory` returns `[]` — needs the full Bungie /Profile component call + manifest decoration. Wired but stubbed.
- `/api/me` returns hardcoded primary_class — needs character lookup.
- Tag editor UI — backend route exists, frontend not yet wired.
- AI assistant chat panel — will plug into Darth Bot Worker proxy.
- Loadout sharing UI — backend not yet built.

## Roadmap

- **v0.2** — full inventory fetch + manifest decoration in Worker (with KV caching of manifest tables)
- **v0.3** — tag editor UI, drag-drop to assign tags
- **v0.4** — loadout viewer + sharing
- **v0.5** — AI assistant chat panel proxying to Darth Bot's ollama backend
- **v0.6** — mobile-friendly tweaks (the current layout works but isn't optimized)

## Roughly stars-worthy?

- ✅ Clean modern UI (Vite + Tailwind + DARTH_BANKAI palette)
- ✅ Live demo URL on a custom domain
- ✅ Inventory-aware AI bot (the unique angle)
- ✅ Open source (this repo)
- ⏳ Polished README with screenshots — TODO once v0.2 lands
- ⏳ Reddit r/destinythegame announcement post — TODO at v0.3
