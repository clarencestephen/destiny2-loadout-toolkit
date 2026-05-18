import { useEffect, useRef, useState } from "react";
import { api, type ChatMessage } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const placeholders = [
  "How do I get the Crimson catalyst?",
  "What's the current PvP meta?",
  "Compare Finality's Auger and One Thousand Voices",
  "What should I chase next for raids?",
  "Walk me through Desert Perpetual encounters",
];

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const placeholder = useRef(
    placeholders[Math.floor(Math.random() * placeholders.length)],
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const question = input.trim();
    if (!question || busy) return;
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question }]);
    setBusy(true);
    try {
      const resp = await api.chat(question);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: resp.answer, category: resp.category },
      ]);
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="container py-10 flex flex-col gap-6 max-w-4xl">
      <header className="flex flex-col gap-2">
        <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-muted">
          ▲ Imperial Interrogation Chamber
        </span>
        <h1 className="font-display text-3xl tracking-[0.18em] font-black text-signature">
          DARTH BOT
        </h1>
        <p className="font-ui text-sm text-muted-foreground max-w-2xl">
          Same brain as Darth Bot on Discord. Grounded on your inventory (if linked),
          the live Bungie manifest, and the current meta state. Anti-hallucination
          checks flag any item names not in the manifest.
        </p>
      </header>

      <Card className="flex-1 flex flex-col min-h-[480px] max-h-[70vh]">
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 space-y-4 font-ui text-sm"
        >
          {messages.length === 0 && (
            <div className="text-muted text-center pt-12 space-y-3">
              <div className="font-mono text-[10px] tracking-[0.3em] uppercase">
                no transmissions yet
              </div>
              <div>Try something like:</div>
              <div className="text-star italic">"{placeholder.current}"</div>
            </div>
          )}

          {messages.map((m, i) => (
            <MessageBubble key={i} msg={m} />
          ))}

          {busy && (
            <div className="text-muted font-mono text-[10px] tracking-[0.3em] uppercase">
              ▸ Darth Bot is thinking...
            </div>
          )}
          {error && (
            <div className="text-red-400 text-xs">⚠ {error}</div>
          )}
        </div>

        <form onSubmit={submit} className="border-t border-border p-4 flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything Destiny..."
            disabled={busy}
            className="flex-1 bg-void/40 border border-border rounded-md px-3 py-2 font-ui text-sm focus:outline-none focus:ring-1 focus:ring-sith"
          />
          <Button type="submit" disabled={busy || !input.trim()}>
            Send
          </Button>
        </form>
      </Card>

      <p className="text-[10px] font-mono tracking-[0.25em] uppercase text-muted text-center">
        Not affiliated with Bungie. Answers may still drift — verify on light.gg/db before deleting items.
      </p>
    </section>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-3 ${
          isUser
            ? "bg-sith/15 border border-sith/30"
            : "bg-deepspace/60 border border-border"
        }`}
      >
        {!isUser && msg.category && (
          <div className="font-mono text-[9px] tracking-[0.3em] uppercase text-muted mb-2">
            [{msg.category}]
          </div>
        )}
        <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
      </div>
    </div>
  );
}
