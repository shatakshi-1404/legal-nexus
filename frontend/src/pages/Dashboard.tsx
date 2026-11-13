import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { Doc } from "../types";

export default function Dashboard() {
  const [docs, setDocs] = useState<Doc[]>([]);
  useEffect(() => { api.documents().then(setDocs).catch(() => {}); }, []);
  const stat = (label: string, n: number) => (
    <div className="rounded-lg border border-line bg-white p-4"><div className="text-2xl font-semibold">{n}</div><div className="text-sm text-ink-soft">{label}</div></div>);
  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold">Dashboard</h2>
      <div className="grid grid-cols-3 gap-4">
        {stat("Documents", docs.length)}
        {stat("Analyses completed", docs.filter((d) => d.latest_analysis_status === "completed").length)}
        {stat("Processing", docs.filter((d) => ["uploaded", "processing"].includes(d.status) || d.latest_analysis_status === "running").length)}
      </div>
      <section>
        <h3 className="mb-2 font-medium">Recent</h3>
        {docs.length === 0 ? <p className="text-sm text-ink-soft">Nothing yet. <Link className="text-accent" to="/documents">Upload your first document.</Link></p> :
          <ul className="divide-y divide-line rounded-lg border border-line bg-white text-sm">{docs.slice(0, 6).map((d) => (
            <li key={d.id} className="flex justify-between p-3"><span>{d.filename}</span><span className="text-ink-soft">{d.latest_analysis_status ?? d.status}</span></li>))}</ul>}
      </section>
    </div>
  );
}
