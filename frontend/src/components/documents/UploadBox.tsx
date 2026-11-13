import { useRef, useState } from "react";
import { api } from "../../services/api";

export default function UploadBox({ onUploaded }: { onUploaded: () => void }) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  async function pick(f?: File) {
    if (!f) return;
    setBusy(true); setError("");
    try { await api.upload(f); onUploaded(); } catch (e) { setError((e as Error).message); }
    setBusy(false); if (ref.current) ref.current.value = "";
  }
  return (
    <div className="rounded-lg border border-dashed border-line bg-white p-6 text-center">
      <p className="text-sm text-ink-soft">Upload a rental, employment, NDA, service or vendor agreement, or a privacy policy (PDF or DOCX, up to 20 MB).</p>
      <button disabled={busy} onClick={() => ref.current?.click()} className="mt-3 rounded bg-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
        {busy ? "Uploading…" : "Choose a file"}
      </button>
      <input ref={ref} type="file" accept=".pdf,.docx" hidden onChange={(e) => pick(e.target.files?.[0])} />
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
