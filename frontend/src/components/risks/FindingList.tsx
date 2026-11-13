import { api } from "../../services/api";
import type { Finding } from "../../types";
import CitationCard from "../citations/CitationCard";

const sev: Record<string, string> = { high: "bg-red-100 text-red-800", medium: "bg-amber-100 text-amber-800", low: "bg-blue-100 text-blue-800" };

export default function FindingList({ findings, analysisId }: { findings: Finding[]; analysisId: string }) {
  if (!findings.length) return <p className="text-sm text-ink-soft">No findings were reported for this document.</p>;
  return (
    <ul className="space-y-3">
      {findings.map((f) => (
        <li key={f.finding_id} className="rounded-lg border border-line bg-white p-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">{f.finding_id} · {f.clause_ref}</span>
            {f.severity && <span className={`rounded px-2 py-0.5 text-xs ${sev[f.severity]}`}>{f.severity}</span>}
            {f.category && <span className="text-ink-soft">{f.category.replace(/_/g, " ")}</span>}
            {f.compliance_status && <span className="text-ink-soft">{f.compliance_status.replace(/_/g, " ")}</span>}
            <span className="ml-auto text-xs text-ink-soft">{f.status === "verified" ? "Evidence verified" : "Needs human review"}</span>
          </div>
          <p className="mt-2 text-sm">{f.rationale}</p>
          {f.explanation && <p className="mt-2 text-sm text-ink-soft">{f.explanation}</p>}
          {f.recommendation && <p className="mt-2 text-sm"><span className="font-medium">Suggested change:</span> {f.recommendation}</p>}
          {f.questions?.length > 0 && <ul className="mt-2 list-disc pl-5 text-sm text-ink-soft">{f.questions.map((q) => <li key={q}>{q}</li>)}</ul>}
          <CitationCard f={f} />
          <div className="mt-2 space-x-3 text-xs text-ink-soft">
            Was this useful?
            <button className="hover:text-accent" onClick={() => api.feedback(analysisId, f.finding_id, 1)}>Yes</button>
            <button className="hover:text-accent" onClick={() => api.feedback(analysisId, f.finding_id, -1)}>No</button>
          </div>
        </li>))}
    </ul>
  );
}
