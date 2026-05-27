import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  api, sumStats, STAT_KEYS, STAT_LABEL, ARMOR_SLOTS, ARMOR_ARCHETYPES,
  type ArmorStats, type ArmorSlot, type CharacterSummary, type Item, type UserProfile,
} from "@/lib/api";
import { loadBuilds, type BuildTemplate } from "@/lib/builds";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const CLASS_COLOR: Record<string, string> = {
  hunter: "text-hunter",
  titan:  "text-titan",
  warlock:"text-warlock",
};

// Stretch target by selection count. Hard floor is always 100.
const STRETCH_BY_COUNT: Record<number, number> = { 1: 200, 2: 200, 3: 125, 4: 100 };

// Per-slot top-K prune before the cartesian product. K=12 → 12^5 = ~248k
// combos worst-case; the exotic filter knocks it down further. Fast on
// modern hardware; tune up if results feel sparse.
const TOP_K_PER_SLOT = 12;

// ============================================================
// Helpers
// ============================================================

type StatKey = keyof ArmorStats;
type Combo = {
  pieces: Item[];
  /** Raw stat totals from the 5 armor pieces (pre-mod). */
  totals: ArmorStats;
  /** Per-stat count of +10 mods + per-stat count of +5 mods. */
  modPlan: ModPlan;
  /** Stat totals AFTER applying the mod plan. */
  withMods: ArmorStats;
  /** Lexicographic score tuple — see scoreCombo */
  score: number[];
  activations: number;
  stretchHits: number;
  surplus: number;
  rawSum: number;
  totalPower: number;
  /** Mod slots consumed by the plan (out of 5). */
  modsUsed: number;
};

/** Armor stat mod plan — assignment of stat mods to the 5 piece slots.
 *  Each piece has 1 mod socket; +10 (major) and +5 (minor) both fit. */
type ModPlan = {
  /** Number of +10 mods per stat. */
  plus10: Partial<Record<StatKey, number>>;
  /** Number of +5 mods per stat. */
  plus5:  Partial<Record<StatKey, number>>;
  /** Total mod slots consumed (sum across plus10 + plus5). */
  used: number;
};

const MOD_BUDGET = 5;  // 5 armor pieces, 1 stat mod socket each
const PLUS10 = 10;
const PLUS5  = 5;

function isArmor(item: Item): boolean {
  return !!item.stats && ARMOR_SLOTS.includes(item.slot as ArmorSlot);
}

function selStatSum(item: Item, selected: StatKey[]): number {
  if (!item.stats) return 0;
  let s = 0;
  for (const k of selected) s += item.stats[k] ?? 0;
  return s;
}

function sumArmorStats(pieces: Item[]): ArmorStats {
  return pieces.reduce<ArmorStats>(
    (acc, p) => sumStats(acc, p.stats),
    { weapons: 0, health: 0, class: 0, grenade: 0, super: 0, melee: 0 },
  );
}

/**
 * Plan armor stat mods to hit the score targets for selected stats.
 *
 * Strategy (5 slot budget, one stat mod per armor piece):
 *  1. For each selected stat under 100: allocate +10 mods to reach 100,
 *     using +5 only when a single +5 closes the last gap (avoids
 *     "wasting" a slot on +10 when +5 suffices).
 *  2. Remaining slots: if stretch target > 100, push each selected
 *     stat toward stretch — +10 first, fall back to +5 if needed.
 *  3. Hard cap at 5 mod slots; we stop allocating once full.
 *
 * Returns a plan that may be UNDER-satisfying (some stats below 100)
 * if 5 slots can't cover all selected. The scoreCombo then evaluates
 * post-mod totals — combos that get more activations win.
 */
function planMods(totals: ArmorStats, selected: StatKey[], stretch: number): ModPlan {
  const plan: ModPlan = { plus10: {}, plus5: {}, used: 0 };
  const proj: Record<string, number> = { ...totals };

  function addPlus10(s: StatKey): boolean {
    if (plan.used >= MOD_BUDGET) return false;
    plan.plus10[s] = (plan.plus10[s] ?? 0) + 1;
    plan.used += 1;
    proj[s] += PLUS10;
    return true;
  }
  function addPlus5(s: StatKey): boolean {
    if (plan.used >= MOD_BUDGET) return false;
    plan.plus5[s] = (plan.plus5[s] ?? 0) + 1;
    plan.used += 1;
    proj[s] += PLUS5;
    return true;
  }

  // Phase 1: hit floor 100 on each selected stat, cheaper-first.
  for (const s of selected) {
    while (proj[s] < 100 && plan.used < MOD_BUDGET) {
      const gap = 100 - proj[s];
      if (gap <= PLUS5 && gap > 0) {
        addPlus5(s);
      } else {
        addPlus10(s);
      }
    }
  }

  // Phase 2: if stretch target > 100 and slots left, push toward stretch.
  // Prefer +10 first (more efficient), fall back to +5 for tight gaps.
  if (stretch > 100 && plan.used < MOD_BUDGET) {
    for (const s of selected) {
      while (proj[s] < stretch && plan.used < MOD_BUDGET) {
        const gap = stretch - proj[s];
        if (gap <= PLUS5 && gap > 0) {
          addPlus5(s);
        } else {
          addPlus10(s);
        }
      }
    }
  }
  return plan;
}

function applyModPlan(totals: ArmorStats, plan: ModPlan): ArmorStats {
  const out = { ...totals };
  for (const [s, n] of Object.entries(plan.plus10)) {
    out[s as StatKey] += (n ?? 0) * PLUS10;
  }
  for (const [s, n] of Object.entries(plan.plus5)) {
    out[s as StatKey] += (n ?? 0) * PLUS5;
  }
  return out;
}

function scoreCombo(totals: ArmorStats, pieces: Item[], selected: StatKey[], stretch: number) {
  // Plan mods first, then score using POST-MOD totals.
  const modPlan = planMods(totals, selected, stretch);
  const withMods = applyModPlan(totals, modPlan);

  let activations = 0;
  let stretchHits = 0;
  let surplus = 0;
  let rawSum = 0;
  for (const s of selected) {
    const v = withMods[s] ?? 0;
    if (v >= 100) activations++;
    if (v >= stretch) stretchHits++;
    surplus += Math.max(0, v - 100);
    rawSum += v;
  }
  const totalPower = pieces.reduce((p, x) => p + (x.power ?? 0), 0);
  // Score tuple (descending):
  //  1. activations after mods
  //  2. stretch hits after mods
  //  3. NEGATIVE mods-used  (fewer mods = better — more flexibility for utility mods)
  //  4. surplus above 100 across selected stats
  //  5. raw sum of selected stats
  //  6. total armor power
  return {
    score: [activations, stretchHits, -modPlan.used, surplus, rawSum, totalPower],
    activations, stretchHits, surplus, rawSum, totalPower,
    modPlan, withMods, modsUsed: modPlan.used,
  };
}

function compareScore(a: number[], b: number[]): number {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return b[i] - a[i];  // desc
  }
  return 0;
}

// ============================================================
// Optimizer core
// ============================================================

/**
 * Theme lock entry — user says "I want N pieces of set X in the combo."
 * Multiple themes may be specified; the sum of counts must be ≤ 5.
 * Any remaining slots are unconstrained.
 */
export interface ThemeLock {
  setName: string;
  count: number;
}

function optimize(
  items: Item[],
  cls: "Warlock" | "Hunter" | "Titan",
  selected: StatKey[],
  lockedExoticId: string | null,
  themeLocks: ThemeLock[] = [],
  archetypeFilter: string[] = [],
): { combos: Combo[]; stretch: number; pruned: Record<ArmorSlot, number> } {
  const stretch = STRETCH_BY_COUNT[selected.length] ?? 100;
  const themeReq = themeLocks.filter((t) => t.setName && t.count > 0);

  // Build per-slot pools. Only armor for this class (or class-neutral
  // class-items, which are class-locked but tagged as class-specific
  // by the manifest anyway).
  const pool: Record<ArmorSlot, Item[]> = {
    Helmet: [], Gauntlets: [], Chest: [], Legs: [], Class: [],
  };
  for (const it of items) {
    if (!isArmor(it)) continue;
    if (it.class !== cls && it.class !== "Any") continue;
    // Archetype filter — when the user has picked one or more archetypes,
    // only allow non-exotic pieces with a matching archetype. Exotics are
    // always allowed (they're a fixed slot — locking the exotic OR the
    // archetype, not both).
    if (archetypeFilter.length > 0 && it.tier !== "Exotic") {
      if (!it.archetype || !archetypeFilter.includes(it.archetype)) continue;
    }
    pool[it.slot as ArmorSlot]?.push(it);
  }

  // If an exotic is locked, isolate it. The locked piece must be in
  // pool; the OTHER slots get filtered to non-exotic only.
  const locked = lockedExoticId
    ? items.find((i) => i.instance_id === lockedExoticId) ?? null
    : null;
  const lockedSlot = locked ? (locked.slot as ArmorSlot) : null;

  for (const slot of ARMOR_SLOTS) {
    if (locked && lockedSlot === slot) {
      pool[slot] = [locked];
      continue;
    }
    if (locked && lockedSlot !== slot) {
      // Other slots: exclude exotics (only one allowed)
      pool[slot] = pool[slot].filter((p) => p.tier !== "Exotic");
    }
    // Prune to top-K by selected-stat sum
    pool[slot].sort((a, b) => selStatSum(b, selected) - selStatSum(a, selected));
    pool[slot] = pool[slot].slice(0, TOP_K_PER_SLOT);
  }

  // Pruned counts for diagnostics
  const pruned: Record<ArmorSlot, number> = {
    Helmet: pool.Helmet.length, Gauntlets: pool.Gauntlets.length,
    Chest: pool.Chest.length, Legs: pool.Legs.length, Class: pool.Class.length,
  };

  // Bail if any slot is empty
  for (const slot of ARMOR_SLOTS) {
    if (pool[slot].length === 0) {
      return { combos: [], stretch, pruned };
    }
  }

  // Cartesian product with at-most-one-exotic constraint
  const combos: Combo[] = [];
  for (const h of pool.Helmet)
    for (const g of pool.Gauntlets)
      for (const c of pool.Chest)
        for (const l of pool.Legs)
          for (const cl of pool.Class) {
            const pieces = [h, g, c, l, cl];
            // At most one exotic (unless locked exotic already in there)
            const exoticCount = pieces.filter((p) => p.tier === "Exotic").length;
            if (exoticCount > 1) continue;
            // If an exotic is locked, ensure it's actually present
            if (locked && !pieces.includes(locked)) continue;
            // Theme lock — combo must include ≥N pieces of each named set
            if (themeReq.length) {
              let ok = true;
              for (const t of themeReq) {
                const have = pieces.filter((p) => p.set === t.setName).length;
                if (have < t.count) { ok = false; break; }
              }
              if (!ok) continue;
            }
            const totals = sumArmorStats(pieces);
            const s = scoreCombo(totals, pieces, selected, stretch);
            combos.push({ pieces, totals, ...s });
          }

  combos.sort((a, b) => compareScore(a.score, b.score));
  return { combos: combos.slice(0, 5), stretch, pruned };
}

// ============================================================
// Page
// ============================================================

export default function Optimizer() {
  const [params] = useSearchParams();
  const buildId = params.get("build");
  const [me, setMe] = useState<UserProfile | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [cls, setCls] = useState<"Hunter" | "Titan" | "Warlock" | null>(null);
  const [selected, setSelected] = useState<StatKey[]>([]);
  const [lockedExoticId, setLockedExoticId] = useState<string | null>(null);
  const [themeLocks, setThemeLocks] = useState<ThemeLock[]>([]);
  const [archetypeFilter, setArchetypeFilter] = useState<string[]>([]);
  const [results, setResults] = useState<Combo[]>([]);
  const [stretchTarget, setStretchTarget] = useState<number>(100);
  const [optimizing, setOptimizing] = useState(false);
  const [activeCharId, setActiveCharId] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    (async () => {
      try {
        const [profile, decorated] = await Promise.all([
          api.me(),
          api.inventoryDecorated(),
        ]);
        setMe(profile);
        setItems(decorated);
        const pc = profile.primary_class;
        if (pc) setCls(pc.charAt(0).toUpperCase() + pc.slice(1) as any);
        // Default active character = top-of-the-list (highest equipped power)
        if (profile.characters?.length) {
          const cached = localStorage.getItem("dv_active_char");
          const found = profile.characters.find((c) => c.id === cached);
          setActiveCharId(found ? found.id : profile.characters[0].id);
        }
      } catch (e: any) {
        setErr(`Sign in required: ${e?.message ?? e}`);
      }
    })();
  }, []);

  // Pre-fill selected stats from ?build=<id>
  useEffect(() => {
    if (!buildId) return;
    (async () => {
      try {
        const manifest = await loadBuilds();
        const b: BuildTemplate | undefined = manifest.builds.find((x) => x.id === buildId);
        if (!b) return;
        if (b.class !== "Any") setCls(b.class as any);
        if (b.target_stats) {
          const picks: StatKey[] = (Object.keys(b.target_stats) as StatKey[])
            .filter((k) => (b.target_stats?.[k] ?? 0) > 0)
            .slice(0, 4);
          setSelected(picks);
        }
      } catch { /* swallow */ }
    })();
  }, [buildId]);

  // Available exotics for the class
  const exoticOptions = useMemo(() => {
    if (!cls) return [];
    return items
      .filter((i) => isArmor(i) && i.tier === "Exotic" && (i.class === cls || i.class === "Any"))
      .sort((a, b) => a.slot.localeCompare(b.slot) || a.name.localeCompare(b.name));
  }, [items, cls]);

  // Sets the user actually owns pieces of, with the piece count.
  // Show only sets where the user has ≥2 pieces (anything less can't
  // hit a meaningful theme-bonus threshold).
  const setsOwned = useMemo(() => {
    if (!cls) return [];
    const counts: Record<string, number> = {};
    for (const it of items) {
      if (!isArmor(it)) continue;
      if (it.class !== cls && it.class !== "Any") continue;
      if (!it.set) continue;
      counts[it.set] = (counts[it.set] ?? 0) + 1;
    }
    return Object.entries(counts)
      .filter(([, n]) => n >= 2)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([setName, count]) => ({ setName, ownedCount: count }));
  }, [items, cls]);

  const themeTotal = themeLocks.reduce((s, t) => s + (t.count || 0), 0);

  function addTheme() {
    if (themeTotal >= 5) return;
    setThemeLocks((cur) => [...cur, { setName: "", count: 2 }]);
  }
  function updateTheme(i: number, patch: Partial<ThemeLock>) {
    setThemeLocks((cur) => cur.map((t, idx) => (idx === i ? { ...t, ...patch } : t)));
  }
  function removeTheme(i: number) {
    setThemeLocks((cur) => cur.filter((_, idx) => idx !== i));
  }

  function pickCharacter(id: string) {
    setActiveCharId(id);
    localStorage.setItem("dv_active_char", id);
    // Snap class to the picked character's class (drives the armor pool).
    const ch = me?.characters?.find((c) => c.id === id);
    if (ch) setCls(ch.class.charAt(0).toUpperCase() + ch.class.slice(1) as any);
  }

  function toggleStat(s: StatKey) {
    setSelected((cur) => {
      if (cur.includes(s)) return cur.filter((x) => x !== s);
      if (cur.length >= 4) return cur;  // hard cap
      return [...cur, s];
    });
  }

  function runOptimize() {
    if (!cls || selected.length === 0) return;
    setOptimizing(true);
    // Defer to next tick so the spinner can paint before the synchronous search
    setTimeout(() => {
      try {
        const activeLocks = themeLocks.filter((t) => t.setName && t.count > 0);
        const { combos, stretch } = optimize(
          items, cls, selected, lockedExoticId, activeLocks, archetypeFilter,
        );
        setResults(combos);
        setStretchTarget(stretch);
      } finally {
        setOptimizing(false);
      }
    }, 30);
  }

  // ============================================================
  // Render
  // ============================================================
  if (err) {
    return (
      <section className="container py-20 max-w-2xl">
        <h1 className="font-display text-3xl text-saber mb-3">Access required.</h1>
        <p className="text-muted font-ui mb-6">{err}</p>
        <Button onClick={() => (location.href = "/")}>Sign in with Bungie</Button>
      </section>
    );
  }

  return (
    <section className="container py-10 flex flex-col gap-6 max-w-6xl">
      <header className="flex flex-col gap-2">
        <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-muted">
          ▲ Armor Combination Search
        </span>
        <h1 className="font-display text-3xl tracking-[0.18em] font-black text-signature">
          OPTIMIZER
        </h1>
        <p className="font-ui text-sm text-muted-foreground max-w-2xl">
          Pick 1-4 stats. The optimizer prioritizes hitting the hard <strong className="text-saber">100 activation floor</strong> on each
          selected stat (99 does not activate), then maximizes the stretch target (200 for 1-2 stats, 125 for 3, 100 for 4).
          Higher armor power level breaks ties.
        </p>
      </header>

      {/* Controls */}
      <Card className="p-5 space-y-5">
        {/* Active character — drives both class pool AND equip target */}
        {me?.characters && me.characters.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
            <span className="text-muted w-20">Guardian:</span>
            {me.characters.map((ch) => (
              <button
                key={ch.id}
                onClick={() => pickCharacter(ch.id)}
                className={`px-3 py-1 rounded border transition-colors ${
                  activeCharId === ch.id ? `${CLASS_COLOR[ch.class]} border-current` : "border-border text-muted hover:text-foreground"
                }`}
              >
                {ch.class} · pw {ch.equipped_power}
              </button>
            ))}
          </div>
        )}

        {/* Class */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
          <span className="text-muted w-20">Class:</span>
          {(["Hunter", "Titan", "Warlock"] as const).map((c) => (
            <button
              key={c}
              onClick={() => { setCls(c); setLockedExoticId(null); }}
              className={`px-3 py-1 rounded border transition-colors ${
                cls === c ? `${CLASS_COLOR[c.toLowerCase()]} border-current` : "border-border text-muted hover:text-foreground"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        {/* Stats */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
          <span className="text-muted w-20">Stats:</span>
          {STAT_KEYS.map((s) => {
            const on = selected.includes(s);
            const disabled = !on && selected.length >= 4;
            return (
              <button
                key={s}
                disabled={disabled}
                onClick={() => toggleStat(s)}
                className={`px-3 py-1 rounded border transition-colors ${
                  on
                    ? "text-saber border-saber"
                    : disabled
                      ? "border-border text-muted/40 cursor-not-allowed"
                      : "border-border text-muted hover:text-foreground"
                }`}
              >
                {STAT_LABEL[s]}
              </button>
            );
          })}
          <span className="text-muted ml-2">{selected.length}/4</span>
          {selected.length > 0 && (
            <span className="text-saber ml-2 normal-case tracking-normal text-[11px]">
              floor 100 · stretch {STRETCH_BY_COUNT[selected.length]}
            </span>
          )}
        </div>

        {/* Archetype filter — restrict non-exotic pieces to one or more
            archetypes. Exotics ignore this filter (they're locked by the
            row below). When the user owns mostly pre-EoF gear with no
            archetype label, picking a filter will starve the pool. */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
          <span className="text-muted w-20">Archetype:</span>
          {ARMOR_ARCHETYPES.map((a) => {
            const on = archetypeFilter.includes(a);
            return (
              <button
                key={a}
                onClick={() => setArchetypeFilter((cur) =>
                  cur.includes(a) ? cur.filter((x) => x !== a) : [...cur, a]
                )}
                className={`px-3 py-1 rounded border transition-colors ${
                  on
                    ? "text-saber border-saber"
                    : "border-border text-muted hover:text-foreground"
                }`}
              >
                {a}
              </button>
            );
          })}
          {archetypeFilter.length > 0 && (
            <button
              onClick={() => setArchetypeFilter([])}
              className="ml-2 normal-case tracking-normal text-[11px] text-muted hover:text-saber"
            >
              clear
            </button>
          )}
        </div>

        {/* Locked exotic */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
          <span className="text-muted w-20">Exotic:</span>
          <select
            value={lockedExoticId ?? ""}
            onChange={(e) => setLockedExoticId(e.target.value || null)}
            className="bg-void/40 border border-border rounded px-2 py-1 font-ui text-xs normal-case tracking-normal min-w-[280px]"
          >
            <option value="">— none locked —</option>
            {exoticOptions.map((it) => (
              <option key={it.instance_id} value={it.instance_id}>
                {it.slot}: {it.name} (pw {it.power})
              </option>
            ))}
          </select>
        </div>

        {/* Theme / set lock — lock N pieces of one or more armor sets.
            Total count across rows is capped at 5; remaining slots are
            unconstrained. Each row's "Set" dropdown lists sets where the
            user owns ≥2 pieces (anything less can't reach a theme bonus). */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-baseline gap-3 font-mono text-[10px] tracking-[0.25em] uppercase">
            <span className="text-muted w-20">Themes:</span>
            <span className="text-muted normal-case tracking-normal text-[11px]">
              Lock N pieces of an armor set. Total ≤ 5 (any extra slots are free).
            </span>
            <span className="ml-auto text-saber">
              {themeTotal}/5 locked
            </span>
          </div>
          {themeLocks.map((t, i) => {
            const ownedPicked = setsOwned.find((s) => s.setName === t.setName);
            const maxForThis = Math.min(5, (ownedPicked?.ownedCount ?? 5));
            const otherTotal = themeLocks
              .filter((_, idx) => idx !== i)
              .reduce((s, x) => s + (x.count || 0), 0);
            const maxAllowedByBudget = 5 - otherTotal;
            return (
              <div key={i} className="flex flex-wrap items-center gap-2 ml-[5rem]">
                <select
                  value={t.setName}
                  onChange={(e) => updateTheme(i, { setName: e.target.value })}
                  className="bg-void/40 border border-border rounded px-2 py-1 font-ui text-xs min-w-[200px]"
                >
                  <option value="">— pick a set —</option>
                  {setsOwned.map((s) => (
                    <option key={s.setName} value={s.setName}>
                      {s.setName} ({s.ownedCount} owned)
                    </option>
                  ))}
                </select>
                <select
                  value={t.count}
                  onChange={(e) => updateTheme(i, { count: parseInt(e.target.value, 10) })}
                  disabled={!t.setName}
                  className="bg-void/40 border border-border rounded px-2 py-1 font-ui text-xs"
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option
                      key={n}
                      value={n}
                      disabled={n > Math.min(maxForThis, maxAllowedByBudget)}
                    >
                      {n} {n === 1 ? "piece" : "pieces"}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeTheme(i)}
                  className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted hover:text-saber px-2"
                >
                  ✕ remove
                </button>
              </div>
            );
          })}
          {themeTotal < 5 && setsOwned.length > 0 && (
            <button
              onClick={addTheme}
              className="ml-[5rem] font-mono text-[10px] uppercase tracking-[0.2em] text-saber hover:underline"
            >
              + add theme
            </button>
          )}
          {setsOwned.length === 0 && cls && (
            <div className="ml-[5rem] font-mono text-[10px] tracking-[0.2em] uppercase text-muted/60">
              (no owned sets with ≥2 pieces yet)
            </div>
          )}
        </div>

        <div className="pt-2 flex items-center gap-3">
          <Button
            onClick={runOptimize}
            disabled={!cls || selected.length === 0 || optimizing}
          >
            {optimizing ? "Searching…" : "Optimize"}
          </Button>
          {results.length > 0 && (
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-muted">
              Top {results.length} of {results.length === 5 ? "many" : "all"} combos
            </span>
          )}
        </div>
      </Card>

      {/* Results */}
      {results.length === 0 && !optimizing && (
        <div className="text-muted text-sm font-ui text-center py-8">
          {selected.length === 0 ? "Pick 1-4 stats to begin." : "Hit Optimize."}
        </div>
      )}
      <div className="grid grid-cols-1 gap-4">
        {results.map((combo, i) => (
          <ComboCard
            key={i}
            combo={combo}
            rank={i + 1}
            selected={selected}
            stretch={stretchTarget}
            activeCharId={activeCharId}
            characters={me?.characters ?? []}
          />
        ))}
      </div>

      {results.length > 0 && (
        <Link
          to="/builds"
          className="text-xs font-mono uppercase tracking-[0.25em] text-saber hover:underline mt-2"
        >
          ← back to builds
        </Link>
      )}
    </section>
  );
}

// ============================================================
// Result card
// ============================================================

function ComboCard({
  combo, rank, selected, stretch, activeCharId, characters,
}: {
  combo: Combo; rank: number; selected: StatKey[]; stretch: number;
  activeCharId: string | null; characters: CharacterSummary[];
}) {
  const [equipState, setEquipState] = useState<
    | { kind: "idle" }
    | { kind: "working" }
    | { kind: "done"; msg: string; skipped: Array<{ instance_id: string; reason: string }> }
    | { kind: "error"; msg: string }
  >({ kind: "idle" });

  async function equipNow() {
    if (!activeCharId) {
      setEquipState({ kind: "error", msg: "no active guardian selected" });
      return;
    }
    setEquipState({ kind: "working" });
    try {
      const ids = combo.pieces.map((p) => p.instance_id).filter(Boolean);
      const res = await api.equip(activeCharId, ids);
      const msg = `equipped ${res.equipped_count}/${ids.length}`;
      setEquipState({ kind: "done", msg, skipped: res.skipped });
    } catch (e: any) {
      setEquipState({ kind: "error", msg: e?.message ?? "equip failed" });
    }
  }

  return (
    <Card className="p-4 border-saber/30">
      <div className="flex items-center justify-between mb-3 gap-3">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-muted">#{rank}</span>
          <span className="font-display text-lg tracking-wide">
            {combo.activations}/{selected.length} activated
          </span>
          {combo.stretchHits > 0 && stretch > 100 && (
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-emerald-400 ml-2">
              +{combo.stretchHits} at {stretch}+
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-muted">
            power {combo.totalPower}
          </span>
          {activeCharId && (
            <Button
              onClick={equipNow}
              disabled={equipState.kind === "working"}
              variant="primary"
            >
              {equipState.kind === "working" ? "Equipping…" : "Equip"}
            </Button>
          )}
        </div>
      </div>
      {equipState.kind === "done" && (
        <div className="mb-3 px-3 py-2 rounded border border-emerald-400/40 bg-emerald-400/5 font-ui text-xs text-emerald-300">
          ✓ {equipState.msg}
          {equipState.skipped.length > 0 && (
            <div className="mt-1 text-amber-300">
              skipped: {equipState.skipped.map((s) => s.reason).join(" · ")}
            </div>
          )}
        </div>
      )}
      {equipState.kind === "error" && (
        <div className="mb-3 px-3 py-2 rounded border border-red-400/40 bg-red-400/5 font-ui text-xs text-red-300">
          ⚠ {equipState.msg}
        </div>
      )}

      {/* Stat totals — highlight selected. Shows POST-MOD totals as the
          big number, with a small subscript showing the pre-mod base
          (so you see how much the mod plan added). */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-3">
        {STAT_KEYS.map((s) => {
          const v = combo.withMods[s];            // post-mod
          const base = combo.totals[s];           // pre-mod
          const delta = v - base;
          const sel = selected.includes(s);
          const activated = sel && v >= 100;
          const stretchHit = sel && v >= stretch && stretch > 100;
          return (
            <div
              key={s}
              className={`rounded border p-2 ${
                stretchHit ? "border-emerald-400 text-emerald-400"
                : activated ? "border-saber text-saber"
                : sel ? "border-amber-400/60 text-amber-400"
                : "border-border text-muted"
              }`}
            >
              <div className="font-mono text-[9px] tracking-[0.2em] uppercase">
                {STAT_LABEL[s]}
              </div>
              <div className="font-display text-lg leading-none mt-0.5">
                {v}
                {delta > 0 && (
                  <span className="font-mono text-[9px] text-emerald-400/80 ml-1 align-top">
                    (+{delta})
                  </span>
                )}
              </div>
              <div className="font-mono text-[9px] text-muted mt-0.5">base {base}</div>
              {sel && !activated && (
                <div className="font-mono text-[9px] mt-1">+{100 - v} to activate</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Mod plan — how to mod the 5 pieces to hit those numbers */}
      {(combo.modsUsed > 0) && (
        <div className="mb-4 px-3 py-2 rounded border border-saber/30 bg-saber/5">
          <div className="flex items-baseline justify-between mb-1">
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-saber">
              Mod plan
            </span>
            <span className="font-mono text-[9px] tracking-[0.25em] uppercase text-muted">
              {combo.modsUsed}/5 mod slots used
            </span>
          </div>
          <div className="flex flex-wrap gap-2 font-ui text-xs">
            {STAT_KEYS.map((s) => {
              const n10 = combo.modPlan.plus10[s] ?? 0;
              const n5 = combo.modPlan.plus5[s] ?? 0;
              if (!n10 && !n5) return null;
              const parts: string[] = [];
              if (n10) parts.push(`${n10}× +10`);
              if (n5)  parts.push(`${n5}× +5`);
              return (
                <span key={s} className="px-2 py-0.5 rounded border border-saber/40 text-saber">
                  {STAT_LABEL[s]}: {parts.join(" · ")}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Pieces */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-ui text-sm">
        {combo.pieces.map((p) => (
          <div key={p.instance_id} className="flex items-baseline gap-2 flex-wrap">
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-muted w-20 shrink-0">
              {p.slot}
            </span>
            <span className={p.tier === "Exotic" ? "text-amber-300" : ""}>{p.name}</span>
            {p.archetype && (
              <span className="font-mono text-[9px] tracking-[0.2em] uppercase px-1.5 py-0.5 rounded border border-fuchsia-400/40 text-fuchsia-300/90">
                {p.archetype}
              </span>
            )}
            {p.set && (
              <span className="font-mono text-[9px] tracking-[0.2em] uppercase px-1.5 py-0.5 rounded border border-saber/40 text-saber/80">
                {p.set}
              </span>
            )}
            <span className="text-muted text-xs ml-auto">pw {p.power}</span>
          </div>
        ))}
      </div>
      {/* Set bonus summary — count pieces per set in this combo */}
      {(() => {
        const setCounts: Record<string, number> = {};
        for (const p of combo.pieces) {
          if (p.set) setCounts[p.set] = (setCounts[p.set] ?? 0) + 1;
        }
        const entries = Object.entries(setCounts).filter(([, n]) => n >= 2);
        if (entries.length === 0) return null;
        return (
          <div className="mt-3 pt-3 border-t border-border flex flex-wrap items-center gap-2 font-mono text-[10px] tracking-[0.2em] uppercase">
            <span className="text-muted">Set bonus:</span>
            {entries.map(([name, n]) => (
              <span
                key={name}
                className={`px-2 py-1 rounded border ${
                  n >= 4 ? "border-emerald-400 text-emerald-400"
                  : n >= 2 ? "border-saber text-saber"
                  : "border-border text-muted"
                }`}
              >
                {n}× {name}
              </span>
            ))}
          </div>
        );
      })()}
    </Card>
  );
}
