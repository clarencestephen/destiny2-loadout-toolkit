import { useEffect, useState } from "react";
import { api, type Item, type UserProfile } from "@/lib/api";
import { Button } from "@/components/ui/button";

const CLASS_COLOR: Record<string, string> = {
  hunter: "text-hunter",
  titan: "text-titan",
  warlock: "text-warlock",
};

const TAG_LABEL: Record<NonNullable<Item["tag"]>, string> = {
  favorite: "F", keep: "K", infuse: "I", junk: "J", archive: "A",
};
const TAG_BG: Record<NonNullable<Item["tag"]>, string> = {
  favorite: "bg-yellow-400 text-void",
  keep:     "bg-emerald-400 text-void",
  infuse:   "bg-amber-500 text-void",
  junk:     "bg-saber text-void",
  archive:  "bg-muted text-void",
};

export default function Dashboard() {
  const [me, setMe] = useState<UserProfile | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [profile, inv] = await Promise.all([api.me(), api.inventory()]);
        setMe(profile);
        setItems(inv.items);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      }
    })();
  }, []);

  if (err) {
    return (
      <div className="container py-20">
        <h1 className="font-display text-3xl text-saber">Access denied.</h1>
        <p className="mt-4 text-muted font-ui">{err}</p>
        <Button variant="primary" className="mt-6" onClick={() => (location.href = "/")}>
          Back to sign-in
        </Button>
      </div>
    );
  }

  const filtered = items.filter((i) =>
    !search || i.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="container py-10">
      {/* Header strip */}
      <section className="flex flex-wrap items-end justify-between gap-6 pb-8 border-b border-border">
        <div>
          <p className="font-mono text-xs tracking-[0.4em] text-sith uppercase">▸ Guardian</p>
          <h1 className={`font-display text-5xl font-black tracking-wide ${me ? CLASS_COLOR[me.primary_class] : "text-muted"}`}>
            {me?.bungie_name || "Loading…"}
          </h1>
          {me && (
            <p className="mt-1 font-ui uppercase tracking-[0.2em] text-sm text-muted">
              {me.primary_class} · Power {me.power}
            </p>
          )}
        </div>
        <div className="font-mono text-right">
          <p className="text-[10px] tracking-[0.3em] text-muted uppercase">Records</p>
          <p className="font-display text-3xl text-sith">{items.length.toLocaleString()}</p>
        </div>
      </section>

      {/* Search */}
      <div className="mt-8">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder='QUERY INVENTORY · "crimson" · "void grenade" · #favorite'
          className="w-full max-w-2xl bg-deepspace border border-border px-4 py-3 font-mono text-sm tracking-wider text-star placeholder:text-muted focus:outline-none focus:border-sith focus:ring-1 focus:ring-sith transition-colors"
        />
      </div>

      {/* Inventory grid */}
      <section className="mt-8">
        <header className="flex items-center justify-between pb-3 border-b border-border font-mono text-[10px] tracking-[0.25em] uppercase text-muted">
          <span>Displaying <strong className="text-sith">{filtered.length}</strong> records</span>
          <span>sort · power ↓</span>
        </header>

        <ul className="divide-y divide-border">
          {filtered.map((it) => (
            <li
              key={it.instance_id}
              className="group grid grid-cols-[4px_1fr_120px_60px_36px] items-center gap-4 px-2 py-4 hover:bg-nebula transition-colors relative overflow-hidden"
            >
              <span
                className={`h-12 ${
                  it.tier === "Exotic"
                    ? "bg-yellow-400 shadow-[0_0_12px_rgba(250,204,21,0.6)]"
                    : it.tier === "Legendary"
                    ? "bg-warlock"
                    : "bg-muted"
                }`}
              />
              <div className="min-w-0">
                <div className={`font-display text-base font-bold tracking-wide truncate ${
                  it.tier === "Exotic" ? "text-signature" : "text-star"
                }`}>
                  {it.name}
                </div>
                <div className="font-mono text-[10px] tracking-wider text-muted uppercase mt-1">
                  {it.type} · {it.element} · {it.slot}
                </div>
              </div>
              <div className="font-mono text-[10px] tracking-wider text-muted uppercase text-right">
                {it.location}
              </div>
              <div className="font-display text-lg text-saber text-right">
                {it.power}
              </div>
              <div className="flex justify-center">
                {it.tag ? (
                  <span className={`w-6 h-6 grid place-items-center font-mono text-xs font-bold ${TAG_BG[it.tag]}`}>
                    {TAG_LABEL[it.tag]}
                  </span>
                ) : (
                  <span className="w-6 h-6 border border-dashed border-border" />
                )}
              </div>
            </li>
          ))}
        </ul>

        {filtered.length === 0 && (
          <p className="mt-12 text-center font-mono text-muted text-sm tracking-wider uppercase">
            No items match.
          </p>
        )}
      </section>
    </div>
  );
}
