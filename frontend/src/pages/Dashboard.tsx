import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ErrorBox, PageHeader, Stat, StatusBadge } from "../components/ui";
import { api, errorMessage } from "../services/api";
import type { Stats } from "../types";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(errorMessage(e)));
  }, []);

  const run = stats?.latest_run;
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Overview of your model and recent activity" />
      <ErrorBox message={error} />
      {stats && !stats.model_loaded && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          No trained model yet. <Link className="font-medium underline" to="/training">Start a training run</Link> to enable text generation.
        </div>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stat label="Your generations" value={stats?.total_generations ?? "–"} />
        <Stat label="Model status" value={stats ? (stats.model_loaded ? "Ready" : "Not trained") : "–"} />
        <Stat
          label="Latest training run"
          value={run ? <StatusBadge status={run.status} /> : "None"}
          hint={run ? `Epoch ${run.epochs_done}/${run.epochs_planned}${run.best_val_loss != null ? ` · best val loss ${run.best_val_loss.toFixed(3)}` : ""}` : undefined}
        />
      </div>

      <section className="card mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Recent generations</h2>
          <Link to="/history" className="text-sm font-medium text-brand-600 hover:underline">View all</Link>
        </div>
        {stats?.recent.length ? (
          <ul className="divide-y">
            {stats.recent.map((g) => (
              <li key={g.id} className="py-3">
                <p className="text-sm font-medium">{g.seed_text}</p>
                <p className="line-clamp-2 text-sm text-slate-500">{g.generated_text}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Nothing yet — try the <Link className="text-brand-600 underline" to="/playground">Playground</Link>.</p>
        )}
      </section>
    </>
  );
}
