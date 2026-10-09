import { Check, Copy, Download, Loader2, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";
import { ErrorBox, PageHeader } from "../components/ui";
import { api, errorMessage } from "../services/api";
import type { GenerateResponse } from "../types";

export default function Playground() {
  const [seed, setSeed] = useState("to be or not to be");
  const [maxTokens, setMaxTokens] = useState(50);
  const [temperature, setTemperature] = useState(0.8);
  const [topK, setTopK] = useState<number | "">("");
  const [save, setSave] = useState(true);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      setResult(await api.generate({
        seed_text: seed, max_tokens: maxTokens, temperature,
        top_k: topK === "" ? null : topK, save,
      }));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!result) return;
    await navigator.clipboard.writeText(result.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function download() {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([result.full_text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <PageHeader title="AI Playground" subtitle="Enter a seed and let the LSTM continue the text" />
      <div className="grid gap-6 lg:grid-cols-5">
        <form onSubmit={submit} className="card space-y-4 lg:col-span-2">
          <div>
            <label className="label" htmlFor="seed">Seed text</label>
            <textarea id="seed" className="input min-h-[96px]" value={seed} maxLength={1000}
              onChange={(e) => setSeed(e.target.value)} required />
          </div>
          <div>
            <label className="label" htmlFor="tokens">Output length: {maxTokens} words</label>
            <input id="tokens" type="range" min={5} max={300} value={maxTokens} className="w-full accent-brand-600"
              onChange={(e) => setMaxTokens(Number(e.target.value))} />
          </div>
          <div>
            <label className="label" htmlFor="temp">Temperature: {temperature.toFixed(2)}</label>
            <input id="temp" type="range" min={0.1} max={2} step={0.05} value={temperature} className="w-full accent-brand-600"
              onChange={(e) => setTemperature(Number(e.target.value))} />
            <p className="text-xs text-slate-400">Lower = safer and more repetitive, higher = more varied.</p>
          </div>
          <div>
            <label className="label" htmlFor="topk">Top-k (optional)</label>
            <input id="topk" type="number" min={1} max={200} className="input" placeholder="all words" value={topK}
              onChange={(e) => setTopK(e.target.value === "" ? "" : Number(e.target.value))} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} /> Save to history
          </label>
          <button className="btn-primary w-full" disabled={busy || !seed.trim()}>
            {busy ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
            {busy ? "Generating…" : "Generate"}
          </button>
        </form>

        <section className="card lg:col-span-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="font-semibold">Output</h2>
            {result && (
              <div className="flex gap-2">
                <button className="btn-ghost" onClick={copy}>{copied ? <Check size={16} /> : <Copy size={16} />} <span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span></button>
                <button className="btn-ghost" onClick={download}><Download size={16} /> <span className="hidden sm:inline">.txt</span></button>
              </div>
            )}
          </div>
          <ErrorBox message={error} />
          {result ? (
            <p className="whitespace-pre-wrap break-words leading-relaxed">
              <span className="font-semibold text-brand-700">{result.seed_text}</span> {result.generated_text}
            </p>
          ) : (
            <p className="text-sm text-slate-400">Generated text will appear here.</p>
          )}
        </section>
      </div>
    </>
  );
}
