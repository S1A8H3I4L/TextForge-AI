import { Brain, History, LayoutDashboard, LineChart, LogOut, Menu, Sparkles, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/playground", label: "Playground", icon: Sparkles, end: false },
  { to: "/history", label: "History", icon: History, end: false },
  { to: "/training", label: "Training", icon: LineChart, end: false },
];

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  const nav = (
    <nav className="flex flex-col gap-1">
      {links.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
              isActive ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
            }`
          }
        >
          <Icon size={18} /> {label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen lg:flex">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b bg-white px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2 font-semibold"><Brain className="text-brand-600" /> TextForge AI</div>
        <button aria-label="Toggle menu" onClick={() => setOpen((o) => !o)} className="rounded-lg p-2 hover:bg-slate-100">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Sidebar (drawer on mobile, fixed on desktop) */}
      <aside
        className={`fixed inset-y-0 left-0 z-20 w-64 transform border-r bg-white p-4 pt-20 transition-transform lg:static lg:translate-x-0 lg:pt-4 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-6 hidden items-center gap-2 text-lg font-semibold lg:flex"><Brain className="text-brand-600" /> TextForge AI</div>
        {nav}
        <div className="absolute inset-x-4 bottom-4 border-t pt-4">
          <p className="truncate text-sm font-medium">{user?.name}</p>
          <p className="mb-3 truncate text-xs text-slate-500">{user?.email}</p>
          <button onClick={logout} className="btn-ghost w-full"><LogOut size={16} /> Log out</button>
        </div>
      </aside>
      {open && <div className="fixed inset-0 z-10 bg-black/30 lg:hidden" onClick={() => setOpen(false)} />}

      <main className="mx-auto w-full max-w-6xl flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
    </div>
  );
}
