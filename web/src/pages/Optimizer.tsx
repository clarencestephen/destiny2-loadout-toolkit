import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  api, sumStats, STAT_KEYS, STAT_LABEL, ARMOR_SLOTS,
  type ArmorStats, type ArmorSlot, type Item, type UserProfile,
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
  totals: ArmorStats;
  /** Lexicographic score tuple — see scoreCombo */
  score: number[];
  activations: number;
  stretchHits: number;
  surplus: number;
  rawSum: number;
  totalPower: number;
};

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

function scoreCombo(totals: ArmorStats, pieces: Item[], selected: StatKey[], stretch: number): Omit<Combo, "pieces" | "totals" | "score"> & { score: number[] } {
  let activations = 0;
  let stretchHits = 0;
  let surplus = 0;
  let rawSum = 0;
  for (const s of selected) {
    const v = totals[s] ?? 0;
    if (v >= 100) activations++;
    if (v >= stretch) stretchHits++;
    surplus += Math.max(0, v - 100);
    rawSum += v;
  }
  const totalPower = pieces.reduce((p, x) => p + (x.power ?? 0), 0);
  return {
    score: [activations, stretchHits, surplus, rawSum, totalPower],
    activations, stretchHits, surplus, rawSum, totalPower,
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

function optimize(
  items: Item[],
  cls: "Warlock" | "Hunter" | "Titan",
  selected: StatKey[],
  lockedExoticId: string | null,
): { combos: Combo[]; stretch: number; pruned: Record<ArmorSlot, number> } {
  const stretch = STRETCH_BY_COUNT[selected.length] ?? 100;

  // Build per-slot pools. Only armor for this class (or class-neutral
  // class-items, which are class-locked but tagged as class-specific
  // by the manifest anyway).
  const pool: Record<ArmorSlot, Item[]> = {
    Helmet: [], Gauntlets: [], Chest: [], Legs: [], Class: [],
  };
  for (const it of items) {
    if (!isArmor(it)) continue;
    if (it.class !== cls && it.class !== "Any") continue;
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
  const [results, setResults] = useState<Combo[]>([]);
  const [stretchTarget, setStretchTarget] = useState<number>(100);
  const [optimizing, setOptimizing] = useState(false);

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
        const { combos, stretch } = optimize(items, cls, selected, lockedExoticId);
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
          <ComboCard key={i} combo={combo} rank={i + 1} selected={selected} stretch={stretchTarget} />
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

function ComboCard({ combo, rank, selected, stretch }: { combo: Combo; rank: number; selected: StatKey[]; stretch: number }) {
  return (
    <Card className="p-4 border-saber/30">
      <div className="flex items-center justify-between mb-3">
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
        <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-muted">
          power {combo.totalPower}
        </span>
      </div>

      {/* Stat totals — highlight selected, dim others */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-4">
        {STAT_KEYS.map((s) => {
          const v = combo.totals[s];
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
              <div className="font-display text-lg leading-none mt-0.5">{v}</div>
              {sel && !activated && (
                <div className="font-mono text-[9px] mt-1">+{100 - v} to activate</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pieces */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 font-ui text-sm">
        {combo.pieces.map((p) => (
          <div key={p.instance_id} className="flex items-baseline gap-2">
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-muted w-20 shrink-0">
              {p.slot}
            </span>
            <span className={p.tier === "Exotic" ? "text-amber-300" : ""}>{p.name}</span>
            <span className="text-muted text-xs ml-auto">pw {p.power}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
