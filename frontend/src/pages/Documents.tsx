import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import type { Doc } from "../types";
import UploadBox from "../components/documents/UploadBox";

export default function Documents() {
  const nav = useNavigate();
  const [docs, setDocs] = useState<Doc[]>([]); const [tick, setTick] = useState(0);
  usePolling(async () => { const d = await api.documents(); setDocs(d); return !d.some((x) => ["uploaded", "processing"].includes(x.status)); }, 2500, [tick]);

  async function analyze(id: string) { const r = await api.startAnalysis(id); nav(`/analysis/${r.analysis_id}`); }
  async function remove(id: string) { if (confirm("Delete this document and its analyses?")) { await api.deleteDoc(id); setTick((t) => t + 1); } }

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold">Documents</h2>
      <UploadBox onUploaded={() => setTick((t) => t + 1)} />
      {docs.length === 0 ? <p className="text-sm text-ink-soft">No documents yet. Upload one to start an analysis.</p> : (
        <table className="w-full rounded-lg border border-line bg-white text-sm">
          <thead className="text-left text-ink-soft"><tr><th className="p-3">File</th><th>Type</th><th>Processing</th><th>Analysis</th><th /></tr></thead>
          <tbody>{docs.map((d) => (
            <tr key={d.id} className="border-t border-line">
              <td className="p-3">{d.filename}</td><td>{d.doc_type ?? d.file_type}</td>
              <td>{d.status}{d.error ? ` – ${d.error}` : ""}</td>
              <td>{d.latest_analysis_id ? <Link className="text-accent" to={`/analysis/${d.latest_analysis_id}`}>{d.latest_analysis_status}</Link> : "–"}</td>
              <td className="space-x-3 pr-3 text-right">
                <button disabled={d.status !== "ready"} onClick={() => analyze(d.id)} className="text-accent disabled:text-ink-soft">Analyze</button>
                <button onClick={() => remove(d.id)} className="text-ink-soft hover:text-red-700">Delete</button>
              </td>
            </tr>))}</tbody>
        </table>)}
    </div>
  );
}
