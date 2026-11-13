import { FormEvent, useEffect, useState } from "react";
import { api } from "../services/api";
import type { ChatReply, Doc } from "../types";

interface Turn { q: string; a?: ChatReply; error?: string }

export default function Chat() {
  const [docs, setDocs] = useState<Doc[]>([]); const [docId, setDocId] = useState("");
  const [q, setQ] = useState(""); const [turns, setTurns] = useState<Turn[]>([]); const [conv, setConv] = useState<string>();
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.documents().then((d) => setDocs(d.filter((x) => x.status === "ready"))).catch(() => {}); }, []);

  async function ask(e: FormEvent) {
    e.preventDefault(); if (!q.trim()) return;
    const question = q; setQ(""); setBusy(true); setTurns((t) => [...t, { q: question }]);
    try {
      const a = await api.chat(question, docId || undefined, conv); setConv(a.conversation_id);
      setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, a } : x)));
    } catch (err) { setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, error: (err as Error).message } : x))); }
    setBusy(false);
  }
  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-2xl font-semibold">Ask a question</h2>
      <select className="rounded border border-line bg-white px-3 py-2 text-sm" value={docId} onChange={(e) => { setDocId(e.target.value); setConv(undefined); }}>
        <option value="">Legal sources only</option>{docs.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
      </select>
      {turns.length === 0 && <p className="text-sm text-ink-soft">Try: “Can my landlord keep the full deposit if I leave early?”</p>}
      {turns.map((t, i) => (
        <div key={i} className="space-y-2">
          <p className="font-medium">{t.q}</p>
          {t.error && <p role="alert" className="text-sm text-red-700">{t.error}</p>}
          {t.a && (<div className="rounded-lg border border-line bg-white p-4 text-sm">
            <p className="whitespace-pre-wrap">{t.a.answer}</p>
            {!t.a.citations_verified && <p className="mt-2 text-xs text-amber-700">Some citations could not be verified. Check the sources before relying on this answer.</p>}
            {t.a.sources.map((s) => <blockquote key={s.label} className="mt-2 border-l-2 border-accent pl-2 text-xs text-ink-soft"><b>{s.label}</b> {s.meta.source_title ?? `Clause ${s.meta.clause_ref}, page ${s.meta.page}`}: {s.text.slice(0, 250)}</blockquote>)}
          </div>)}
        </div>))}
      <form onSubmit={ask} className="flex gap-2">
        <input className="flex-1 rounded border border-line bg-white px-3 py-2 text-sm" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about a document or Indian law" />
        <button disabled={busy} className="rounded bg-navy px-4 py-2 text-sm text-white disabled:opacity-50">{busy ? "Thinking…" : "Ask"}</button>
      </form>
    </div>
  );
}
