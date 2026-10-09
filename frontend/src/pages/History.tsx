import { Search, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { ErrorBox, PageHeader } from "../components/ui";
import { api, errorMessage } from "../services/api";
import type { Generation } from "../types";

const PAGE = 10;

export default function History() {
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [items, setItems] = useState<Generation[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Generation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api.generations(query, PAGE, page * PAGE)
      .then((r) => { setItems(r.items); setTotal(r.total); })
      .catch((e) => setError(errorMessage(e)));
  }, [query, page]);

  useEffect(load, [load]);

  async function remove(id: number) {
    if (!confirm("Delete this generation?")) return;
    try {
      await api.deleteGeneration(id);
      if (selected?.id === id) setSelected(null);
      if (items.length === 1 && page > 0) setPage(page - 1);
      else load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE));
  return (
    <>
      <PageHeader title="Generation history" subtitle={`${total} saved generation${total === 1 ? "" : "s"}`} />
      <form className="mb-4 flex gap-2" onSubmit={(e) => { e.preventDefault(); setPage(0); setQuery(q); }}>
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className="input pl-9" placeholder="Search seeds and outputs…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <button className="btn-primary">Search</button>
      </form>
      <ErrorBox message={error} />

      <div className="grid gap-4 lg:grid-cols-2">
        <ul className="space-y-3">
          {items.map((g) => (
            <li key={g.id}
              className={`card cursor-pointer !p-4 transition hover:border-brand-500 ${selected?.id === g.id ? "border-brand-500" : ""}`}
              onClick={() => setSelected(g)}>
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium">{g.seed_text}</p>
                <button aria-label="Delete" className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  onClick={(e) => { e.stopPropagation(); remove(g.id); }}><Trash2 size={16} /></button>
              </div>
              <p className="mt-1 line-clamp-2 text-sm text-slate-500">{g.generated_text}</p>
              <p className="mt-2 text-xs text-slate-400">{new Date(g.created_at).toLocaleString()}</p>
            </li>
          ))}
          {items.length === 0 && <p className="text-sm text-slate-500">No generations found.</p>}
        </ul>

        <aside className="card h-fit lg:sticky lg:top-6">
          {selected ? (
            <>
              <h2 className="mb-2 font-semibold">Details</h2>
              <p className="whitespace-pre-wrap break-words leading-relaxed">
                <span className="font-semibold text-brand-700">{selected.seed_text}</span> {selected.generated_text}
              </p>
              <dl className="mt-4 grid grid-cols-3 gap-2 text-sm">
                <div><dt className="text-slate-400">Length</dt><dd>{selected.max_tokens}</dd></div>
                <div><dt className="text-slate-400">Temp</dt><dd>{selected.temperature}</dd></div>
                <div><dt className="text-slate-400">Top-k</dt><dd>{selected.top_k ?? "all"}</dd></div>
              </dl>
            </>
          ) : (
            <p className="text-sm text-slate-400">Select an entry to see the full text and settings.</p>
          )}
        </aside>
      </div>

      <div className="mt-6 flex items-center justify-center gap-3 text-sm">
        <button className="btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
        <span>Page {page + 1} / {pages}</span>
        <button className="btn-ghost" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </>
  );
}
