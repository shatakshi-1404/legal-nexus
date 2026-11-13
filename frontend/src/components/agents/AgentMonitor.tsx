import type { AgentRun } from "../../types";

const tone: Record<string, string> = { completed: "text-green-700", running: "text-accent", failed: "text-red-700" };

export default function AgentMonitor({ runs }: { runs: AgentRun[] }) {
  if (!runs.length) return <p className="text-sm text-ink-soft">Waiting for the first agent to start…</p>;
  return (
    <ol className="space-y-2">
      {runs.map((r) => (
        <li key={r.id} className="rounded border border-line bg-white p-3 text-sm">
          <div className="flex justify-between">
            <span className="font-medium">{r.agent}</span>
            <span className={tone[r.status]}>{r.status}{r.duration_ms != null ? ` · ${(r.duration_ms / 1000).toFixed(1)}s` : ""}</span>
          </div>
          {r.tools.length > 0 && <div className="mt-1 text-xs text-ink-soft">Tools: {r.tools.join(", ")}</div>}
          {r.error && <div role="alert" className="mt-1 text-xs text-red-700">{r.error}</div>}
          <details className="mt-1 text-xs text-ink-soft">
            <summary className="cursor-pointer">Input and output (redacted)</summary>
            <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify({ input: r.input, output: r.output }, null, 2)}</pre>
          </details>
        </li>))}
    </ol>
  );
}
