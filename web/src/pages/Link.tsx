import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Phase = "idle" | "needs-login" | "linking" | "done" | "error";

/**
 * /link?code=XYZ — Discord ↔ Bungie account link completion.
 *
 * Flow:
 *   1. Discord bot generates a one-time code via the backend.
 *   2. User clicks the DM link, lands here with ?code=XYZ in the URL.
 *   3. If not signed in to Bungie yet: bounce them through /api/auth/login.
 *   4. After login: POST /api/link/complete { code, bungie_id }.
 *   5. Show success → "your Discord can now use /loadout-check and /upgrade".
 */
export default function Link() {
  const [params] = useSearchParams();
  const code = params.get("code");
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!code) {
      setPhase("error");
      setMessage("No link code in URL. Re-run /link-bungie on Discord.");
      return;
    }
    (async () => {
      try {
        const me = await api.me().catch(() => null);
        if (!me) {
          setPhase("needs-login");
          return;
        }
        setPhase("linking");
        await api.linkComplete(code, me.membership_id, me.bungie_name);
        setPhase("done");
        setMessage(`Linked to ${me.bungie_name}.`);
      } catch (err: any) {
        setPhase("error");
        setMessage(err?.message ?? "Link failed");
      }
    })();
  }, [code]);

  async function startLogin() {
    try {
      const { url } = await api.authUrl();
      const ret = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `${url}&state_return=${ret}`;
    } catch (err: any) {
      setPhase("error");
      setMessage(err?.message ?? "Couldn't start Bungie login");
    }
  }

  return (
    <section className="container py-16 max-w-xl">
      <Card className="p-8 text-center space-y-6">
        <div className="font-mono text-[10px] tracking-[0.3em] uppercase text-muted">
          ▲ Discord ↔ Bungie account link
        </div>
        <h1 className="font-display text-2xl tracking-[0.18em] font-black text-signature">
          {phase === "done" ? "ACCESS GRANTED" : "AUTHORIZE"}
        </h1>

        {phase === "idle" && (
          <p className="text-muted-foreground">Checking session…</p>
        )}

        {phase === "needs-login" && (
          <div className="space-y-4">
            <p className="text-muted-foreground">
              Sign in with Bungie to finish linking. Stays signed in for 30 days.
            </p>
            <Button onClick={startLogin}>Sign in with Bungie</Button>
          </div>
        )}

        {phase === "linking" && (
          <p className="text-muted-foreground">Linking your accounts…</p>
        )}

        {phase === "done" && (
          <div className="space-y-3">
            <p className="text-green-400">✓ {message}</p>
            <p className="text-muted-foreground text-sm">
              Your Discord can now use <code className="text-sith">/loadout-check</code>,
              {" "}<code className="text-sith">/upgrade</code>, and personalized
              <code className="text-sith"> /ask</code> questions.
            </p>
            <p className="text-muted-foreground text-sm">
              You can close this tab.
            </p>
          </div>
        )}

        {phase === "error" && (
          <p className="text-red-400">⚠ {message}</p>
        )}
      </Card>
    </section>
  );
}
