/**
 * Tiny client for the Destiny Voyager Worker API.
 * All requests go through /api/* which is proxied to the Worker in dev
 * and served by the same domain in prod (Cloudflare Pages + Workers route).
 */

export interface UserProfile {
  bungie_name: string;
  membership_id: string;
  primary_class: "hunter" | "titan" | "warlock";
  power: number;
  build_focus?: {
    archetype: string;
    goals: string[];
    target_stats: string[];
  };
}

export interface Item {
  instance_id: string;
  name: string;
  tier: string;
  type: string;
  slot: string;
  element: string;
  power: number;
  location: string;
  tag?: "favorite" | "keep" | "infuse" | "junk" | "archive";
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  category?: string;
}

export interface ChatResponse {
  answer: string;
  category: string;
  used_inventory: boolean;
  used_kb: boolean;
  used_search: boolean;
  used_manifest: boolean;
}

export interface MetaState {
  generated_at?: string;
  expansion: { current: string; year: number; current_episode?: string };
  power_levels: Record<string, unknown>;
  current_raid: { name: string; released_with?: string };
  recent_patches: Array<{
    date: string;
    title: string;
    category: string;
    url: string;
    summary: string;
  }>;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

export const api = {
  health: () => jsonFetch<{ status: string; version: string }>("/api/health"),

  me: () => jsonFetch<UserProfile>("/api/me"),

  inventory: () => jsonFetch<{ items: Item[] }>("/api/inventory"),

  setTag: (instance_id: string, tag: Item["tag"] | null) =>
    jsonFetch<{ ok: true }>("/api/tags", {
      method: "PUT",
      body: JSON.stringify({ instance_id, tag }),
    }),

  authUrl: () =>
    jsonFetch<{ url: string }>("/api/auth/login"),

  logout: () =>
    jsonFetch<{ ok: true }>("/api/auth/logout", { method: "POST" }),

  // Chat — proxied by the Worker to the Python backend (FastAPI /chat)
  chat: (question: string) =>
    jsonFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  // Meta state — current expansion, power caps, recent patches
  metaState: () =>
    jsonFetch<{ state: MetaState; prompt_block: string }>("/api/meta/state"),

  // Discord ↔ Bungie account link completion
  linkComplete: (code: string, bungie_id: string, display_name?: string) =>
    jsonFetch<{ discord_id: string; bungie_id: string; linked_at: number }>(
      "/api/link/complete",
      {
        method: "POST",
        body: JSON.stringify({ code, bungie_id, display_name }),
      },
    ),
};
