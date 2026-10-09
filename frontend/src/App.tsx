import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./hooks/useAuth";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Login from "./pages/Login";
import Playground from "./pages/Playground";
import Training from "./pages/Training";

function Protected() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-slate-500">Loading…</div>;
  return user ? <Layout><Outlet /></Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route element={<Protected />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/playground" element={<Playground />} />
        <Route path="/history" element={<History />} />
        <Route path="/training" element={<Training />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
