const BASE = "/api/v1";
export const getToken = () => localStorage.getItem("ln_token");
export const setToken = (t: string | null) => (t ? localStorage.setItem("ln_token", t) : localStorage.removeItem("ln_token"));

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const t = getToken();
  if (t) headers.set("Authorization", `Bearer ${t}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(BASE + path, { ...init, headers });
  if (res.status === 401) { setToken(null); window.location.href = "/login"; }
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `Request failed (${res.status})`);
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, full_name: string) => request<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }),
  documents: () => request<import("../types").Doc[]>("/documents"),
  upload: (file: File) => { const f = new FormData(); f.append("file", file); return request<import("../types").Doc>("/documents/upload", { method: "POST", body: f }); },
  deleteDoc: (id: string) => request<void>(`/documents/${id}`, { method: "DELETE" }),
  startAnalysis: (docId: string) => request<{ analysis_id: string }>(`/analysis/${docId}/start`, { method: "POST" }),
  analysis: (id: string) => request<import("../types").Analysis>(`/analysis/${id}`),
  agents: (id: string) => request<import("../types").AgentRun[]>(`/analysis/${id}/agents`),
  approve: (id: string) => request<unknown>(`/analysis/${id}/approve`, { method: "POST" }),
  resume: (id: string) => request<unknown>(`/analysis/${id}/resume`, { method: "POST" }),
  chat: (question: string, document_id?: string, conversation_id?: string) =>
    request<import("../types").ChatReply>("/chat", { method: "POST", body: JSON.stringify({ question, document_id, conversation_id, include_legal: true }) }),
  feedback: (analysis_id: string, target_id: string, rating: number) =>
    request<unknown>("/feedback", { method: "POST", body: JSON.stringify({ analysis_id, target_id, rating }) }),
};
