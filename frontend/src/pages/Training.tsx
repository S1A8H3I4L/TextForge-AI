import { Loader2, Play } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorBox, PageHeader, Stat, StatusBadge } from "../components/ui";
import { api, errorMessage } from "../services/api";
import type { ModelInfo, TrainConfig, TrainingRun } from "../types";

const defaults: TrainConfig = {
  epochs: 20, seq_length: 8, embedding_dim: 128, lstm_units: 256, lstm_layers: 2,
  dropout: 0.2, batch_size: 128, max_vocab: 8000, max_chars: 400000,
};

const fields: { key: keyof TrainConfig; label: string; step?: number }[] = [
  { key: "epochs", label: "Max epochs" },
  { key: "seq_length", label: "Sequence length" },
  { key: "embedding_dim", label: "Embedding dim" },
  { key: "lstm_units", label: "LSTM units" },
  { key: "lstm_layers", label: "LSTM layers" },
  { key: "dropout", label: "Dropout", step: 0.05 },
  { key: "batch_size", label: "Batch size" },
  { key: "max_vocab", label: "Max vocabulary" },
];

export default function Training() {
  const [cfg, setCfg] = useState<TrainConfig>(defaults);
  const [runs, setRuns] = useState<TrainingRun[]>([]);
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    api.runs().then(setRuns).catch((e) => setError(errorMessage(e)));
    api.modelInfo().then(setInfo).catch(() => undefined);
  }, []);

  useEffect(refresh, [refresh]);

  const active = runs.some((r) => r.status === "running" || r.status === "queued");
  useEffect(() => {
    if (!active) return;
    const t = setInterval(refresh, 3000); // poll while a run is in progress
    return () => clearInterval(t);
  }, [active, refresh]);

  async function start(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const run = await api.startTraining(cfg);
      setSelectedId(run.id);
      refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const shown = runs.find((r) => r.id === selectedId) ?? runs[0];

  return (
    <>
      <PageHeader title="Training" subtitle="Train the LSTM and monitor loss per epoch" />
      <ErrorBox message={error} />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Model" value={info?.loaded ? "Loaded" : "None"} hint={info?.name} />
        <Stat label="Vocabulary" value={info?.vocab_size?.toLocaleString() ?? "–"} />
        <Stat label="Layers × units" value={info?.architecture ? `${info.architecture.lstm_layers} × ${info.architecture.lstm_units}` : "–"} />
        <Stat label="Seq. length" value={info?.architecture?.seq_length ?? "–"} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <form onSubmit={start} className="card space-y-3 lg:col-span-1">
          <h2 className="font-semibold">New training run</h2>
          <div className="grid grid-cols-2 gap-3">
            {fields.map((f) => (
              <div key={f.key}>
                <label className="label" htmlFor={f.key}>{f.label}</label>
                <input id={f.key} type="number" step={f.step ?? 1} className="input" value={cfg[f.key] ?? ""}
                  onChange={(e) => setCfg({ ...cfg, [f.key]: Number(e.target.value) })} required />
              </div>
            ))}
          </div>
          <button className="btn-primary w-full" disabled={busy || active}>
            {busy || active ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            {active ? "Training in progress…" : "Start training"}
          </button>
          <p className="text-xs text-slate-400">Early stopping (patience 3) and best-model checkpointing are enabled. CPU training can take several minutes.</p>
        </form>

        <section className="card lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">{shown ? `Run #${shown.id}` : "Loss curves"}</h2>
            {shown && <StatusBadge status={shown.status} />}
          </div>
          {shown?.error && <ErrorBox message={shown.error} />}
          {shown && shown.history.length > 0 ? (
            <div className="h-64 sm:h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={shown.history} margin={{ left: -10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="epoch" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="loss" name="Train loss" stroke="#4f46e5" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="val_loss" name="Val loss" stroke="#f59e0b" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-400">{shown ? "Waiting for the first epoch to finish…" : "No runs yet."}</p>
          )}
          {shown && (
            <p className="mt-3 text-sm text-slate-500">
              Epoch {shown.epochs_done}/{shown.epochs_planned}
              {shown.best_val_loss != null && ` · best val loss ${shown.best_val_loss.toFixed(3)}`}
            </p>
          )}
        </section>
      </div>

      <section className="card mt-6">
        <h2 className="mb-3 font-semibold">Run history</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] text-left text-sm">
            <thead className="text-slate-500">
              <tr><th className="py-2">Run</th><th>Status</th><th>Epochs</th><th>Best val loss</th><th>Started</th></tr>
            </thead>
            <tbody className="divide-y">
              {runs.map((r) => (
                <tr key={r.id} className="cursor-pointer hover:bg-slate-50" onClick={() => setSelectedId(r.id)}>
                  <td className="py-2 font-medium">#{r.id}</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td>{r.epochs_done}/{r.epochs_planned}</td>
                  <td>{r.best_val_loss?.toFixed(3) ?? "–"}</td>
                  <td>{new Date(r.started_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {runs.length === 0 && <p className="py-2 text-sm text-slate-400">No runs yet.</p>}
        </div>
      </section>
    </>
  );
}
