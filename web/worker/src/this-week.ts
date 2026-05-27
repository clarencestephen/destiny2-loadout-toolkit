/**
 * "This Week" data layer — aggregates Bungie Vendor + Milestone API
 * responses into a single shape consumed by both Darth Bot (Discord)
 * and the Destiny Voyager web app.
 *
 * Phase 1+2 ships the five vendor handlers: Xur, Ada-1, Banshee-44,
 * Rahool, Eververse. Phase 3 adds Milestones / Activities. Phase 4
 * adds TWID / news.
 *
 * Cache strategy (all KV-backed):
 *   twk:vendor:<user_id>:<vendor_hash>   → 60min TTL
 *   twk:milestones:<user_id>             → 15min TTL
 *   twk:twid:latest                       → 6h TTL, global
 */

import { bungieGet } from "./bungie";

type Env = {
  DV_KV: KVNamespace;
  BUNGIE_API_BASE: string;
  BUNGIE_API_KEY: string;
};

type StoredUser = {
  access_token: string;
  membership_type: number;
  membership_id: string;
  primary_class?: string;
};

// ============================================================
// Vendor hash registry — sourced from DestinyVendorDefinition.
// These are stable across the lifetime of D2 (Bungie doesn't
// re-hash vendors). Adding new vendors: look up the hash from
// the manifest and add an entry here.
// ============================================================

export const VENDORS = {
  xur:        { hash: 2190858386, name: "Xûr, Agent of the Nine" },
  ada1:       { hash:  350061650, name: "Ada-1" },
  banshee:    { hash:  672118013, name: "Banshee-44" },
  rahool:     { hash: 2255782930, name: "Master Rahool" },
  eververse:  { hash: 3361454721, name: "Tess Everis (Eververse)" },
} as const;

export type VendorKey = keyof typeof VENDORS;

// ============================================================
// Public shape — what the API endpoint returns.
// ============================================================

export interface VendorItem {
  hash: number;
  name: string;
  type: string;        // "Hand Cannon" / "Helmet" / "Engram"
  tier: string;        // "Exotic" / "Legendary" / "Rare"
  icon_url: string;
  description?: string;
  cost?: Array<{ currency_hash: number; quantity: number }>;
}

export interface VendorWeek {
  vendor: VendorKey;
  display_name: string;
  available: boolean;             // false if Xur is between Tuesday-Friday, etc.
  location?: { name: string; planet: string };
  refresh_in_seconds: number;     // seconds until vendor refresh (Bungie returns nextRefreshDate)
  items: VendorItem[];
  notes?: string;                 // human-readable extra context
}

export interface ThisWeekResponse {
  vendors: Record<VendorKey, VendorWeek | null>;
  generated_at: string;
  // milestones?: ActivityWeek[];  // Phase 3
  // twid?: TWIDPost;              // Phase 4
}

// ============================================================
// Cache helpers
// ============================================================

const VENDOR_TTL_SECONDS = 60 * 60;  // 1h

async function cachedVendor(
  env: Env,
  userId: string,
  vendorKey: VendorKey,
  fetcher: () => Promise<VendorWeek | null>,
): Promise<VendorWeek | null> {
  const cacheKey = `twk:vendor:${userId}:${VENDORS[vendorKey].hash}`;
  const cached = await env.DV_KV.get(cacheKey, "json");
  if (cached) return cached as VendorWeek | null;
  const fresh = await fetcher();
  if (fresh !== null) {
    await env.DV_KV.put(cacheKey, JSON.stringify(fresh), {
      expirationTtl: VENDOR_TTL_SECONDS,
    });
  }
  return fresh;
}

// ============================================================
// Generic vendor fetcher — used by all 5 handlers below.
// Components requested:
//   400 = Vendors (vendor metadata, nextRefreshDate)
//   402 = VendorSales (the actual items + costs)
//   304 = ItemStats (armor/weapon stat sheets)
//   310 = ItemReusablePlugs (perk choices)
//   305 = ItemSockets (currently rolled perks)
// ============================================================

async function fetchVendor(
  env: Env,
  user: StoredUser,
  vendorHash: number,
): Promise<{ vendor: any; sales: any; itemStats: any; reusablePlugs: any; sockets: any } | null> {
  try {
    const profile = await bungieGet(
      env,
      `/Destiny2/${user.membership_type}/Profile/${user.membership_id}/Character/${primaryCharacterId(user)}/Vendors/${vendorHash}/?components=400,402,304,310,305`,
      user.access_token,
    );
    return {
      vendor:        profile?.vendor?.data,
      sales:         profile?.sales?.data ?? {},
      itemStats:     profile?.itemComponents?.stats?.data ?? {},
      reusablePlugs: profile?.itemComponents?.reusablePlugs?.data ?? {},
      sockets:       profile?.itemComponents?.sockets?.data ?? {},
    };
  } catch (e) {
    return null;
  }
}

// Vendor calls in Bungie's API need a character ID. Use the
// primary character if we have it cached, else fall back to
// fetching the character list.
function primaryCharacterId(user: StoredUser): string {
  // Stored separately in KV when the user logs in; if missing we
  // fall back to the "0" sentinel which Bungie accepts for some
  // account-level vendor lookups (Eververse, Xur post-character-select).
  return (user as any).primary_character_id ?? "0";
}

// Convert a Bungie nextRefreshDate ISO string → seconds remaining.
function refreshIn(isoDate?: string): number {
  if (!isoDate) return 0;
  const target = new Date(isoDate).getTime();
  if (!Number.isFinite(target)) return 0;
  return Math.max(0, Math.floor((target - Date.now()) / 1000));
}

// ============================================================
// Per-vendor handlers
// ============================================================

/** Xur — exotic Friday vendor. Returns available=false Tue-Thu. */
export async function getXur(env: Env, user: StoredUser): Promise<VendorWeek | null> {
  const raw = await fetchVendor(env, user, VENDORS.xur.hash);
  if (!raw || !raw.vendor) {
    // Xur is between weeks — return unavailable rather than null so
    // the UI can render "Xur returns Friday".
    return {
      vendor: "xur",
      display_name: VENDORS.xur.name,
      available: false,
      refresh_in_seconds: nextFridayInSeconds(),
      items: [],
      notes: "Xûr returns Friday at the weekly reset.",
    };
  }
  // Xur's items: items in his sales map, filtered to exotic/legendary
  // weapons + armor + the weekly Exotic Engram.
  const items: VendorItem[] = [];
  for (const [_, sale] of Object.entries(raw.sales as Record<string, any>)) {
    if (!sale.itemHash) continue;
    items.push(saleToItem(sale));
  }
  return {
    vendor: "xur",
    display_name: VENDORS.xur.name,
    available: true,
    location: parseXurLocation(raw.vendor),
    refresh_in_seconds: refreshIn(raw.vendor?.nextRefreshDate),
    items,
  };
}

/** Ada-1 — armor mods + Synthweave rotation. */
export async function getAda1(env: Env, user: StoredUser): Promise<VendorWeek | null> {
  const raw = await fetchVendor(env, user, VENDORS.ada1.hash);
  if (!raw) return null;
  const items: VendorItem[] = [];
  for (const [_, sale] of Object.entries(raw.sales as Record<string, any>)) {
    if (!sale.itemHash) continue;
    items.push(saleToItem(sale));
  }
  return {
    vendor: "ada1",
    display_name: VENDORS.ada1.name,
    available: true,
    refresh_in_seconds: refreshIn(raw.vendor?.nextRefreshDate),
    items,
    notes: "Armor mods rotate daily; transmog (Synthweave) is unlimited.",
  };
}

/** Banshee-44 — gunsmith. Weekly weapons + focusing. */
export async function getBanshee(env: Env, user: StoredUser): Promise<VendorWeek | null> {
  const raw = await fetchVendor(env, user, VENDORS.banshee.hash);
  if (!raw) return null;
  const items: VendorItem[] = [];
  for (const [_, sale] of Object.entries(raw.sales as Record<string, any>)) {
    if (!sale.itemHash) continue;
    items.push(saleToItem(sale));
  }
  return {
    vendor: "banshee",
    display_name: VENDORS.banshee.name,
    available: true,
    refresh_in_seconds: refreshIn(raw.vendor?.nextRefreshDate),
    items,
    notes: "Weekly weapon stock + Enhancement Cores + weapon focusing.",
  };
}

/** Master Rahool — engram decryption focus rotation. */
export async function getRahool(env: Env, user: StoredUser): Promise<VendorWeek | null> {
  const raw = await fetchVendor(env, user, VENDORS.rahool.hash);
  if (!raw) return null;
  const items: VendorItem[] = [];
  for (const [_, sale] of Object.entries(raw.sales as Record<string, any>)) {
    if (!sale.itemHash) continue;
    items.push(saleToItem(sale));
  }
  return {
    vendor: "rahool",
    display_name: VENDORS.rahool.name,
    available: true,
    refresh_in_seconds: refreshIn(raw.vendor?.nextRefreshDate),
    items,
    notes: "Cryptarch decryption / engram focusing rotation.",
  };
}

/** Eververse / Tess Everis — bright dust weekly + silver featured. */
export async function getEververse(env: Env, user: StoredUser): Promise<VendorWeek | null> {
  const raw = await fetchVendor(env, user, VENDORS.eververse.hash);
  if (!raw) return null;
  const items: VendorItem[] = [];
  for (const [_, sale] of Object.entries(raw.sales as Record<string, any>)) {
    if (!sale.itemHash) continue;
    // Eververse has hundreds of permanent silver items; the weekly
    // refresh is identifiable by `overrideStyleItemHash` being set
    // OR by the sale being marked as a featured/discount line.
    // For now we surface everything and let the UI filter.
    items.push(saleToItem(sale));
  }
  return {
    vendor: "eververse",
    display_name: VENDORS.eververse.name,
    available: true,
    refresh_in_seconds: refreshIn(raw.vendor?.nextRefreshDate),
    items,
    notes: "Weekly Bright Dust featured + Silver-exclusive items. UI should filter to bright-dust-only by default.",
  };
}

// ============================================================
// Helpers
// ============================================================

function saleToItem(sale: any): VendorItem {
  // The manifest lookup (name / type / tier / icon / description)
  // happens client-side using the slim manifest the frontend already
  // loads. Server-side we just emit the hash + raw cost info; the
  // client decorates.
  const costs = (sale.costs ?? []).map((c: any) => ({
    currency_hash: c.itemHash,
    quantity: c.quantity,
  }));
  return {
    hash: sale.itemHash,
    name: "",          // populated by client via manifest
    type: "",
    tier: "",
    icon_url: "",
    cost: costs,
  };
}

/** Xur's location is encoded as a vendorLocationIndex (0/1/2/3 →
 *  EDZ / Nessus / Tower hangar / Tower hangar) per community lore.
 *  Bungie's vendor metadata doesn't expose a human-readable label,
 *  so we look up by index. */
function parseXurLocation(vendorMeta: any): { name: string; planet: string } | undefined {
  const idx = vendorMeta?.vendorLocationIndex;
  if (idx === undefined) return undefined;
  // Community-consensus location table. Bungie has rotated through
  // these consistently since D2 launch.
  const map: Record<number, { name: string; planet: string }> = {
    0: { name: "Winding Cove",        planet: "EDZ"    },
    1: { name: "Watcher's Grave",     planet: "Nessus" },
    2: { name: "Hangar",              planet: "Tower"  },
    3: { name: "Giant's Scar",        planet: "Io"     },  // pre-DCV; left for posterity
  };
  return map[idx];
}

/** Seconds until next Friday 17:00 UTC (10am PT, D2 weekly reset).
 *  Used when Xur isn't currently active to drive the "returns in X"
 *  countdown. */
function nextFridayInSeconds(): number {
  const now = new Date();
  const target = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 17, 0, 0));
  // Bump to the next Friday if today is past Friday-reset or before it
  const day = target.getUTCDay();   // 0=Sun ... 5=Fri ... 6=Sat
  let daysUntilFriday = (5 - day + 7) % 7;
  if (daysUntilFriday === 0 && now.getTime() > target.getTime()) daysUntilFriday = 7;
  target.setUTCDate(target.getUTCDate() + daysUntilFriday);
  return Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
}

// ============================================================
// Main entry point — aggregates all vendors in parallel.
// ============================================================

export async function getThisWeek(env: Env, user: StoredUser): Promise<ThisWeekResponse> {
  const userId = user.membership_id;
  const [xur, ada1, banshee, rahool, eververse] = await Promise.all([
    cachedVendor(env, userId, "xur",       () => getXur(env, user)),
    cachedVendor(env, userId, "ada1",      () => getAda1(env, user)),
    cachedVendor(env, userId, "banshee",   () => getBanshee(env, user)),
    cachedVendor(env, userId, "rahool",    () => getRahool(env, user)),
    cachedVendor(env, userId, "eververse", () => getEververse(env, user)),
  ]);
  return {
    vendors: { xur, ada1, banshee, rahool, eververse },
    generated_at: new Date().toISOString(),
  };
}
