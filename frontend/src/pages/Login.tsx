import { Brain } from "lucide-react";
import { useState, type FormEvent } from "react";
import { ErrorBox } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { errorMessage } from "../services/api";

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(name, email, password);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 to-white p-4">
      <form onSubmit={submit} className="card w-full max-w-md space-y-4">
        <div className="text-center">
          <Brain className="mx-auto mb-2 text-brand-600" size={36} />
          <h1 className="text-2xl font-bold">TextForge AI</h1>
          <p className="text-sm text-slate-500">LSTM-powered text generation</p>
        </div>
        <ErrorBox message={error} />
        {mode === "register" && (
          <div>
            <label className="label" htmlFor="name">Name</label>
            <input id="name" className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
        )}
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input
            id="password" type="password" className="input" value={password}
            onChange={(e) => setPassword(e.target.value)} minLength={8} required
          />
          {mode === "register" && <p className="mt-1 text-xs text-slate-400">At least 8 characters</p>}
        </div>
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
        </button>
        <p className="text-center text-sm text-slate-500">
          {mode === "login" ? "No account?" : "Already registered?"}{" "}
          <button type="button" className="font-medium text-brand-600 hover:underline"
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}>
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </p>
      </form>
    </div>
  );
}
