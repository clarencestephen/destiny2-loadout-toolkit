/**
 * Build template library — loads /builds.json and exposes
 * best-effort fit matching against the user's inventory.
 *
 * Match is name-based (case-insensitive) so build templates can be
 * authored without item hashes. A weapon slot's `options` list is
 * tried in priority order; the first one the user owns is the match.
 * Missing slots are returned as "needs" rather than blocking the rest.
 */
import type { ArmorStats, Item } from "./api";

export type BuildClass = "Warlock" | "Hunter" | "Titan" | "Any";
export type BuildFocus = "PvE" | "PvP" | "Both";
export type BuildSlot = "Helmet" | "Gauntlets" | "Chest" | "Legs" | "Class";

export interface ExoticArmorSpec {
  slot: BuildSlot;
  options: string[];
  drops_from?: string;
}

export interface BuildTemplate {
  id: string;
  name: string;
  class: BuildClass;
  subclass: string;
  super?: string;
  focus: BuildFocus;
  tags?: string[];
  exotic_armor: ExoticArmorSpec;
  weapons: {
    kinetic: string[];
    energy: string[];
    heavy: string[];
  };
  aspects?: string[];
  fragments?: string[];
  target_stats?: Partial<ArmorStats>;
  playstyle?: string;
  source?: string;
  _confidence?: "high" | "medium" | "low";
}

export interface BuildsManifest {
  version: string;
  generated: string;
  _notes?: string;
  builds: BuildTemplate[];
}

/** Where a single slot landed in the fit. */
export type FitSlotStatus =
  | { status: "owned"; item: Item; matchedOption: string }
  | { status: "missing"; wantedOptions: string[]; hint?: string };

/** Full per-build fit result. */
export interface BuildFit {
  build: BuildTemplate;
  /** owned / total critical slots — exotic_armor + 3 weapons = 4 */
  ownedSlots: number;
  totalSlots: number;
  /** 0..1 */
  fitPct: number;
  exoticArmor: FitSlotStatus;
  kinetic: FitSlotStatus;
  energy: FitSlotStatus;
  heavy: FitSlotStatus;
}

// ============================================================
// Loader
// ============================================================

let _cache: BuildsManifest | null = null;
let _promise: Promise<BuildsManifest> | null = null;

export async function loadBuilds(): Promise<BuildsManifest> {
  if (_cache) return _cache;
  if (_promise) return _promise;
  _promise = fetch("/builds.json", { credentials: "omit" })
    .then((r) => {
      if (!r.ok) throw new Error(`builds.json HTTP ${r.status}`);
      return r.json() as Promise<BuildsManifest>;
    })
    .then((b) => {
      _cache = b;
      return b;
    });
  return _promise;
}

// ============================================================
// Fit matching
// ============================================================

const norm = (s: string) => s.toLowerCase().trim();

/** Find the first option from `options` that the user owns in their inventory. */
function findFirstOwned(
  options: string[],
  items: Item[],
  predicate: (item: Item) => boolean = () => true,
): { item: Item; matchedOption: string } | null {
  if (!options?.length) return null;
  for (const opt of options) {
    const target = norm(opt);
    const match = items.find(
      (i) => norm(i.name) === target && predicate(i),
    );
    if (match) return { item: match, matchedOption: opt };
  }
  return null;
}

/**
 * Compute fit for a single build given the user's decorated inventory.
 * Always returns a result — missing slots are marked, not skipped.
 */
export function fitBuild(build: BuildTemplate, items: Item[]): BuildFit {
  // Restrict the search to this class (or Any)
  const classMatches = items.filter(
    (i) =>
      build.class === "Any" ||
      i.class === build.class ||
      i.class === "Any",
  );

  // Exotic armor (1 slot)
  const exoticHit = findFirstOwned(
    build.exotic_armor.options,
    classMatches,
    (i) => i.tier === "Exotic" && i.slot === build.exotic_armor.slot,
  );
  const exoticArmor: FitSlotStatus = exoticHit
    ? { status: "owned", item: exoticHit.item, matchedOption: exoticHit.matchedOption }
    : {
        status: "missing",
        wantedOptions: build.exotic_armor.options,
        hint: build.exotic_armor.drops_from,
      };

  // Weapons — match by name only (slot/element implicit)
  const k = findFirstOwned(build.weapons.kinetic, items);
  const e = findFirstOwned(build.weapons.energy, items);
  const h = findFirstOwned(build.weapons.heavy, items);

  const kinetic: FitSlotStatus = k
    ? { status: "owned", item: k.item, matchedOption: k.matchedOption }
    : { status: "missing", wantedOptions: build.weapons.kinetic };
  const energy: FitSlotStatus = e
    ? { status: "owned", item: e.item, matchedOption: e.matchedOption }
    : { status: "missing", wantedOptions: build.weapons.energy };
  const heavy: FitSlotStatus = h
    ? { status: "owned", item: h.item, matchedOption: h.matchedOption }
    : { status: "missing", wantedOptions: build.weapons.heavy };

  const slots = [exoticArmor, kinetic, energy, heavy];
  const owned = slots.filter((s) => s.status === "owned").length;

  return {
    build,
    ownedSlots: owned,
    totalSlots: slots.length,
    fitPct: owned / slots.length,
    exoticArmor,
    kinetic,
    energy,
    heavy,
  };
}

/**
 * Filter helper for showing builds applicable to a character class.
 * Always includes class="Any" builds.
 */
export function buildsForClass(builds: BuildTemplate[], cls: string | null): BuildTemplate[] {
  if (!cls) return builds;
  const c = cls.charAt(0).toUpperCase() + cls.slice(1).toLowerCase();
  return builds.filter((b) => b.class === c || b.class === "Any");
}
