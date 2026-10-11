"use client";

import { FormEvent, useState } from "react";
import { resumeChat, ReviewAction, startChat, WorkflowResult } from "@/lib/api";

const prompts = [
  "How long does standard shipping take?",
  "Where is ORD-1007?",
  "Do you have Trail Runner shoes in size 10?",
  "My order arrived damaged. Refund it.",
];

function conversationId() {
  if (typeof window === "undefined") return "browser-session";
  const existing = sessionStorage.getItem("northstar-conversation-id");
  if (existing) return existing;
  const created = crypto.randomUUID();
  sessionStorage.setItem("northstar-conversation-id", created);
  return created;
}

export function ChatShell() {
  const [threadId] = useState(conversationId);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [edited, setEdited] = useState("");

  async function send(text = message) {
    if (!text.trim() || loading) return;
    setLoading(true); setError(null); setMessage("");
    setMessages((items) => [...items, { role: "user", content: text }]);
    try {
      const next = await startChat(text, threadId);
      setResult(next);
      setMessages((items) => [...items, { role: "assistant", content: next.response }]);
      setEdited(next.human_review_payload?.proposed_response ?? "");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unexpected error."); }
    finally { setLoading(false); }
  }

  async function review(action: ReviewAction) {
    if (loading) return;
    setLoading(true); setError(null);
    try {
      const next = await resumeChat(threadId, action, action === "EDIT" ? edited : undefined);
      setResult(next);
      setMessages((items) => [...items, { role: "assistant", content: next.response }]);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unexpected error."); }
    finally { setLoading(false); }
  }

  return <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-8">
    <header className="mx-auto mb-8 max-w-6xl"><p className="text-xs font-semibold uppercase tracking-[.24em] text-sky-300">Northstar Outfitters</p><h1 className="mt-2 text-3xl font-semibold">Commerce Support Assistant</h1><p className="mt-2 text-slate-400">Ask about store policies, orders, or products. Trace data shows evidence, never private reasoning.</p></header>
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.3fr_.7fr]">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl">
        <div className="min-h-80 space-y-4" aria-live="polite">{messages.length === 0 && <p className="pt-20 text-center text-slate-500">Start with a demo prompt or ask a question.</p>}{messages.map((item, index) => <div key={index} className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${item.role === "user" ? "ml-auto bg-sky-500 text-slate-950" : "bg-slate-800 text-slate-100"}`}>{item.content}</div>)}</div>
        <div className="mt-5 flex flex-wrap gap-2">{prompts.map((prompt) => <button key={prompt} onClick={() => send(prompt)} className="rounded-full border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-sky-400 hover:text-sky-200">{prompt}</button>)}</div>
        <form onSubmit={(event: FormEvent) => { event.preventDefault(); send(); }} className="mt-5 flex gap-2"><input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask Northstar support…" className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-sky-400" /><button disabled={loading} className="rounded-xl bg-sky-400 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{loading ? "Working…" : "Send"}</button></form>
        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      </section>
      <aside className="space-y-5">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="font-semibold">Agent Trace</h2>{!result ? <p className="mt-3 text-sm text-slate-500">Structured execution metadata will appear here.</p> : <div className="mt-4 space-y-4 text-sm"><div className="grid grid-cols-2 gap-2 text-slate-400"><span>Intent <b className="text-slate-100">{result.intent}</b></span><span>Status <b className="text-slate-100">{result.workflow_status}</b></span><span>Evidence <b className="text-slate-100">{result.evidence_status}</b></span><span>Escalation <b className="text-slate-100">{String(result.escalation_required)}</b></span></div><div><p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Graph path</p><div className="flex flex-wrap gap-1">{result.graph_path.map((step) => <span key={step} className="rounded bg-slate-800 px-2 py-1 text-xs">{step}</span>)}</div></div>{result.sources.length > 0 && <div><p className="text-xs uppercase tracking-wide text-slate-500">Sources</p>{result.sources.map((source) => <p key={`${source.source_name}-${source.chunk_index}`} className="mt-1 text-slate-300">{source.source_name} · distance {source.distance.toFixed(2)}</p>)}</div>}{result.tool_results.length > 0 && <div><p className="text-xs uppercase tracking-wide text-slate-500">Tool results</p><pre className="mt-1 max-h-32 overflow-auto rounded bg-slate-950 p-2 text-[11px] text-slate-300">{JSON.stringify(result.tool_results, null, 2)}</pre></div>}{result.risk_flags.length > 0 && <p className="text-amber-300">Flags: {result.risk_flags.join(", ")}</p>}</div>}</section>
        {result?.workflow_status === "INTERRUPTED" && result.human_review_payload && <section className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5"><h2 className="font-semibold text-amber-200">Human review required</h2><p className="mt-2 text-sm text-slate-300">{result.human_review_payload.escalation_reason}</p><textarea value={edited} onChange={(event) => setEdited(event.target.value)} className="mt-3 min-h-24 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm" aria-label="Edited response" /><div className="mt-3 flex gap-2"><button onClick={() => review("APPROVE")} className="rounded-lg bg-emerald-400 px-3 py-2 text-sm font-semibold text-slate-950">Approve</button><button onClick={() => review("EDIT")} className="rounded-lg bg-sky-400 px-3 py-2 text-sm font-semibold text-slate-950">Use edit</button><button onClick={() => review("REJECT")} className="rounded-lg border border-rose-300 px-3 py-2 text-sm text-rose-200">Reject</button></div></section>}
      </aside>
    </div>
  </main>;
}
