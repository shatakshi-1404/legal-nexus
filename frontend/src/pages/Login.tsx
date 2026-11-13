import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../services/api";

export default function Login() {
  const nav = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault(); setError("");
    try {
      const r = mode === "login" ? await api.login(email, password) : await api.register(email, password, name);
      setToken(r.access_token); nav("/");
    } catch (err) { setError((err as Error).message); }
  }
  const input = "w-full rounded border border-line bg-white px-3 py-2 text-sm";
  return (
    <div className="mx-auto mt-24 max-w-sm">
      <h1 className="text-3xl font-semibold">LegalNexus</h1>
      <p className="mb-6 mt-1 text-sm text-ink-soft">Understand documents. Discover risks. Verify evidence.</p>
      <form onSubmit={submit} className="space-y-3 rounded-lg border border-line bg-white p-5">
        {mode === "register" && <input className={input} placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />}
        <input className={input} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className={input} type="password" placeholder="Password (8+ characters)" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
        <button className="w-full rounded bg-navy py-2 text-sm font-medium text-white">{mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" className="w-full text-sm text-accent" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Create an account" : "I already have an account"}
        </button>
      </form>
    </div>
  );
}
