# Getting a Bungie API key

You need a free Bungie API key to use this toolkit. It's used to fetch the Destiny manifest (so item hashes can be resolved into names like "Still Hunt"). Takes about 30 seconds.

**Your key stays on your computer.** This toolkit never uploads or commits it. It's written to `user_config.json`, which is `.gitignored`.

---

## Steps

1. Go to **<https://www.bungie.net/en/Application>**
2. Sign in with your Bungie account (links Steam / Xbox / PlayStation / Epic)
3. Click **Create New App** in the top right
4. Fill in:

| Field | Value |
|---|---|
| Application Name | Anything (e.g. `My Loadout Tool`) |
| Application Status | `Private` |
| Website | Anything (`https://localhost` works) |
| OAuth Client Type | `Public` (simplest) — `Confidential` also works |
| Redirect URL | `https://localhost` |
| Origin Header | *(leave blank)* |
| Scope | Default — `Read your Destiny 2 information` is enough |

5. Agree to the API terms → **Create**
6. On the new app's page, copy the value labelled **API Key** (32 hex characters)
7. Paste it when `setup.py` (or `setup_gui.py`) asks for it

---

## What if I lose my key?

Go back to <https://www.bungie.net/en/Application>, click your app name, and the API Key is shown at the top of the page. You can regenerate it from that page if it ever leaks.

## Do I need OAuth?

**No** — not for this toolkit. The decoder only hits public manifest endpoints, which require just the `X-API-Key` header. OAuth fields (`client_id` / `client_secret`) are filled in only because the portal makes them required when you create an app; this toolkit doesn't use them.

If you ever want to extend the toolkit to read your *personal* inventory / vault (not just decode DIM share URLs), then OAuth becomes relevant — and `client_id` lives in your app page.
