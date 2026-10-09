import { AlertCircle } from "lucide-react";
import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function ErrorBox({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <AlertCircle size={16} className="mt-0.5 shrink-0" /> <span>{message}</span>
    </div>
  );
}

const colors: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-700",
  running: "bg-amber-100 text-amber-700",
  queued: "bg-slate-100 text-slate-700",
  failed: "bg-red-100 text-red-700",
};
export function StatusBadge({ status }: { status: string }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] ?? colors.queued}`}>{status}</span>;
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
