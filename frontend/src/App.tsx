import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { getToken, setToken } from "./services/api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import AnalysisPage from "./pages/AnalysisPage";
import Chat from "./pages/Chat";

function Shell() {
  const nav = useNavigate();
  if (!getToken()) return <Navigate to="/login" replace />;
  const link = ({ isActive }: { isActive: boolean }) =>
    `block rounded px-3 py-2 text-sm ${isActive ? "bg-white font-medium text-accent shadow-sm" : "text-ink-soft hover:text-navy"}`;
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-line p-4">
        <h1 className="mb-6 text-xl font-semibold">LegalNexus</h1>
        <nav className="space-y-1">
          <NavLink to="/" end className={link}>Dashboard</NavLink>
          <NavLink to="/documents" className={link}>Documents</NavLink>
          <NavLink to="/chat" className={link}>Ask a question</NavLink>
        </nav>
        <button className="mt-8 text-sm text-ink-soft hover:text-navy" onClick={() => { setToken(null); nav("/login"); }}>Sign out</button>
      </aside>
      <main className="flex-1 p-8"><Outlet /></main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="documents" element={<Documents />} />
        <Route path="analysis/:id" element={<AnalysisPage />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  );
}
