/**
 * Destiny Voyager — Worker API
 *
 * Routes:
 *   GET  /api/health             → liveness
 *   GET  /api/auth/login         → returns Bungie OAuth URL
 *   GET  /api/auth/callback      → handles OAuth callback, sets session cookie
 *   POST /api/auth/logout        → clear session
 *   GET  /api/me                 → current user (requires session)
 *   GET  /api/inventory          → vault + equipped + character inventory
 *   PUT  /api/tags               → set/clear tag on an item
 *
 * KV schema (binding: DV_KV):
 *   session:<sid>          → { bungie_id, expires_at }
 *   user:<bungie_id>       → { refresh_token, access_token, expires_at,
 *                              membership_type, membership_id,
 *                              primary_class, build_focus, item_tags }
 *   oauth_state:<state>    → { code_verifier, created_at }   (5min TTL)
 */

import { Hono } from "hono";
import { setCookie, getCookie, deleteCookie } from "hono/cookie";
import { cors } from "hono/cors";
import {
  buildAuthRedirect,
  exchangeCode,
  refreshAccessToken,
  type StoredUser,
} from "./auth";
import { bungieGet } from "./bungie";

export interface Env {
  DV_KV: KVNamespace;
  ENV: string;
  BUNGIE_API_KEY: string;
  BUNGIE_CLIENT_ID: string;
  BUNGIE_CLIENT_SECRET?: string;
  BUNGIE_OAUTH_AUTHORIZE_URL: string;
  BUNGIE_OAUTH_TOKEN_URL: string;
  BUNGIE_API_BASE: string;
  PUBLIC_BASE_URL: string;
  OAUTH_REDIRECT_PATH: string;
  SESSION_SECRET: string;
  // Python backend (FastAPI on Hostinger VPS or local dev)
  BACKEND_BASE_URL: string;
}

const app = new Hono<{ Bindings: Env; Variables: { user: StoredUser } }>();

app.use(
  "*",
  cors({
    origin: (origin) =>
      origin?.endsWith(".clarencestephen.com") ||
      origin?.endsWith(".pages.dev") ||
      origin === "http://localhost:5173"
        ? origin
        : "",
    credentials: true,
  }),
);

// ============================================================
// Health
// ============================================================
app.get("/api/health", (c) =>
  c.json({ status: "ok", version: "0.1.0", env: c.env.ENV }),
);

// ============================================================
// Auth — OAuth with Bungie
// ============================================================
app.get("/api/auth/login", async (c) => {
  const { url, state, codeVerifier } = await buildAuthRedirect(c.env);
  await c.env.DV_KV.put(
    `oauth_state:${state}`,
    JSON.stringify({ code_verifier: codeVerifier, created_at: Date.now() }),
    { expirationTtl: 300 },
  );
  return c.json({ url });
});

app.get("/api/auth/callback", async (c) => {
  const code = c.req.query("code");
  const state = c.req.query("state");
  if (!code || !state) return c.text("Missing code or state", 400);

  const raw = await c.env.DV_KV.get(`oauth_state:${state}`);
  if (!raw) return c.text("State expired or unknown — try signing in again.", 400);
  const { code_verifier } = JSON.parse(raw);
  await c.env.DV_KV.delete(`oauth_state:${state}`);

  let tokens;
  try {
    tokens = await exchangeCode(c.env, code, code_verifier);
  } catch (e: any) {
    return c.text(`Token exchange failed: ${e.message}`, 500);
  }

  // Fetch membership info
  const userResp = await bungieGet(
    c.env,
    "/User/GetMembershipsForCurrentUser/",
    tokens.access_token,
  );
  const memberships = userResp?.destinyMemberships ?? [];
  const primary =
    memberships.find((m: any) => m.crossSaveOverride === m.membershipType) ??
    memberships[0];
  if (!primary) return c.text("No Destiny memberships on this account.", 400);

  const stored: StoredUser = {
    bungie_id: tokens.membership_id,
    membership_type: primary.membershipType,
    membership_id: primary.membershipId,
    display_name: primary.displayName,
    refresh_token: tokens.refresh_token,
    access_token: tokens.access_token,
    access_expires_at: Math.floor(Date.now() / 1000) + (tokens.expires_in - 60),
    refresh_expires_at:
      Math.floor(Date.now() / 1000) + (tokens.refresh_expires_in - 3600),
    created_at: Date.now(),
    item_tags: {},
  };
  await c.env.DV_KV.put(`user:${stored.bungie_id}`, JSON.stringify(stored));

  // Issue a session cookie
  const sid = crypto.randomUUID();
  await c.env.DV_KV.put(
    `session:${sid}`,
    JSON.stringify({ bungie_id: stored.bungie_id, expires_at: Date.now() + 30 * 86400_000 }),
    { expirationTtl: 30 * 86400 },
  );
  setCookie(c, "dv_sid", sid, {
    httpOnly: true,
    secure: c.env.ENV === "production",
    sameSite: "Lax",
    path: "/",
    maxAge: 30 * 86400,
  });

  // Redirect to the app
  return c.redirect(`${c.env.PUBLIC_BASE_URL}/app`);
});

app.post("/api/auth/logout", async (c) => {
  const sid = getCookie(c, "dv_sid");
  if (sid) await c.env.DV_KV.delete(`session:${sid}`);
  deleteCookie(c, "dv_sid");
  return c.json({ ok: true });
});

// ============================================================
// Session middleware — populates c.var.user for authed endpoints
// ============================================================
app.use("/api/me", requireSession);
app.use("/api/inventory", requireSession);
app.use("/api/tags", requireSession);

async function requireSession(c: any, next: any) {
  const sid = getCookie(c, "dv_sid");
  if (!sid) return c.json({ error: "not_signed_in" }, 401);
  const sessRaw = await c.env.DV_KV.get(`session:${sid}`);
  if (!sessRaw) return c.json({ error: "session_expired" }, 401);
  const { bungie_id } = JSON.parse(sessRaw);
  const userRaw = await c.env.DV_KV.get(`user:${bungie_id}`);
  if (!userRaw) return c.json({ error: "user_missing" }, 401);
  let user: StoredUser = JSON.parse(userRaw);

  // Refresh access token if near expiry
  if (user.access_expires_at < Math.floor(Date.now() / 1000) + 60) {
    try {
      const tokens = await refreshAccessToken(c.env, user.refresh_token);
      user.access_token = tokens.access_token;
      user.access_expires_at =
        Math.floor(Date.now() / 1000) + (tokens.expires_in - 60);
      if (tokens.refresh_token) user.refresh_token = tokens.refresh_token;
      await c.env.DV_KV.put(`user:${bungie_id}`, JSON.stringify(user));
    } catch (e: any) {
      return c.json({ error: "refresh_failed", detail: e.message }, 401);
    }
  }

  c.set("user", user);
  await next();
}

// ============================================================
// /me
// ============================================================
app.get("/api/me", async (c) => {
  const u = c.get("user");
  return c.json({
    bungie_name: u.display_name,
    membership_id: u.membership_id,
    primary_class: "warlock", // TODO: derive from /Profile components
    power: 0, // TODO: derive from highest-power character
    build_focus: undefined,
  });
});

// ============================================================
// /inventory  — stub returning [] until full Bungie /Profile call wired
// ============================================================
app.get("/api/inventory", async (c) => {
  // Real impl: bungieGet(`/Destiny2/{type}/Profile/{id}/?components=102,201,205,300`)
  // then flatten + decorate with manifest. Returning [] for v0.1 scaffold.
  return c.json({ items: [] });
});

// ============================================================
// /tags
// ============================================================
app.put("/api/tags", async (c) => {
  const u = c.get("user");
  const body = await c.req.json<{ instance_id: string; tag: string | null }>();
  if (body.tag === null) delete u.item_tags[body.instance_id];
  else u.item_tags[body.instance_id] = body.tag;
  await c.env.DV_KV.put(`user:${u.bungie_id}`, JSON.stringify(u));
  return c.json({ ok: true });
});

// ============================================================
// Backend proxy — forwards LLM/KB/manifest calls to the Python FastAPI
// service on the VPS. The web frontend hits /api/* on the same origin
// (no CORS), the Worker adds session context, and the backend trusts
// us (network-level boundary). See backend/README.md.
// ============================================================
async function proxyToBackend(
  c: any,
  path: string,
  init: RequestInit & { method?: string } = {},
): Promise<Response> {
  const backend = c.env.BACKEND_BASE_URL;
  if (!backend) {
    return c.json({ error: "backend_not_configured" }, 503);
  }
  const url = backend.replace(/\/$/, "") + path;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Forwarded-By": "destiny-voyager-worker",
  };
  // Forward session id if the user is logged in — backend can resolve
  // it to a bungie_id via KV lookup we'll wire later.
  const sid = getCookie(c, "dv_session");
  if (sid) headers["X-Session-Id"] = sid;
  const body = init.method && init.method !== "GET" ? await c.req.text() : undefined;
  try {
    const r = await fetch(url, { method: init.method ?? "GET", headers, body });
    const text = await r.text();
    return new Response(text, {
      status: r.status,
      headers: { "Content-Type": r.headers.get("content-type") || "application/json" },
    });
  } catch (e: any) {
    return c.json({ error: "backend_unreachable", detail: e.message }, 502);
  }
}

// Public — no session required
app.post("/api/chat", (c) => proxyToBackend(c, "/chat", { method: "POST" }));
app.get("/api/meta/state", (c) => proxyToBackend(c, "/meta/state"));
app.get("/api/meta/twab", (c) => proxyToBackend(c, "/meta/twab"));
app.get("/api/manifest/lookup", (c) => {
  const q = c.req.query("q") ?? "";
  return proxyToBackend(c, `/manifest/lookup?q=${encodeURIComponent(q)}`);
});

// Session-gated — link/complete needs an authenticated user; the proxy
// forwards X-Session-Id which the backend resolves against the KV (or
// later, against the link DB).
app.post("/api/link/complete", (c) => proxyToBackend(c, "/link/complete", { method: "POST" }));

// ============================================================
// 404
// ============================================================
app.notFound((c) => c.json({ error: "not_found", path: c.req.path }, 404));

export default app;
