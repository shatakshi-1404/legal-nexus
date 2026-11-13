import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import type { AgentRun, Analysis } from "../types";
import AgentMonitor from "../components/agents/AgentMonitor";
import FindingList from "../components/risks/FindingList";

export default function AnalysisPage() {
  const { id = "" } = useParams();
  const [a, setA] = useState<Analysis | null>(null); const [runs, setRuns] = useState<AgentRun[]>([]);
  const [tick, setTick] = useState(0);

  usePolling(async () => {
    const [an, ag] = await Promise.all([api.analysis(id), api.agents(id)]);
    setA(an); setRuns(ag);
    return ["completed", "failed", "awaiting_approval"].includes(an.status);
  }, 1500, [id, tick]);

  const r = a?.report;
  return (
    <div className="grid max-w-6xl gap-6 lg:grid-cols-[1fr_340px]">
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Analysis <span className="text-base font-normal text-ink-soft">({a?.status ?? "loading"})</span></h2>
        {a?.status === "awaiting_approval" && (
          <div className="rounded border border-line bg-white p-4 text-sm">
            The agents have finished. Approve to finalize the report.
            <button className="ml-3 rounded bg-navy px-3 py-1 text-white" onClick={async () => { await api.approve(id); setTick((t) => t + 1); }}>Approve and finalize</button>
          </div>)}
        {a?.status === "failed" && (
          <div role="alert" className="rounded border border-red-200 bg-white p-4 text-sm text-red-800">
            The analysis stopped: {a.error}
            <button className="ml-3 rounded border border-red-300 px-3 py-1" onClick={async () => { await api.resume(id); setTick((t) => t + 1); }}>Resume from last checkpoint</button>
          </div>)}
        {r && (<>
          <p className="text-sm">{r.summary}</p>
          <p className="text-sm text-ink-soft">High {r.severity_counts.high} · Medium {r.severity_counts.medium} · Low {r.severity_counts.low} · {r.stats.rejected} unsupported findings removed</p>
          <FindingList findings={r.findings} analysisId={id} />
          <p className="text-xs text-ink-soft">{r.disclaimer}</p>
        </>)}
      </section>
      <aside><h3 className="mb-2 font-medium">Agent activity</h3><AgentMonitor runs={runs} /></aside>
    </div>
  );
}
