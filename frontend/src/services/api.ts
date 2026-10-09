import axios, { AxiosError } from "axios";
import type {
  GenerateRequest, GenerateResponse, Generation, GenerationPage, ModelInfo, Stats,
  TokenResponse, TrainConfig, TrainingRun, User,
} from "../types";

const TOKEN_KEY = "textforge_token";
export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// VITE_API_URL is set in production (e.g. the Render URL); in dev the Vite proxy handles /api.
const http = axios.create({ baseURL: `${import.meta.env.VITE_API_URL ?? ""}/api` });

http.interceptors.request.use((cfg) => {
  const t = tokenStore.get();
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

/** Turn any API failure into a readable message. */
export function errorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
    if (!err.response) return "Cannot reach the server. Is the backend running?";
  }
  return "Something went wrong";
}

export const api = {
  register: (name: string, email: string, password: string) =>
    http.post<TokenResponse>("/auth/register", { name, email, password }).then((r) => r.data),
  login: (email: string, password: string) =>
    http.post<TokenResponse>("/auth/login", { email, password }).then((r) => r.data),
  me: () => http.get<User>("/auth/me").then((r) => r.data),
  stats: () => http.get<Stats>("/stats").then((r) => r.data),
  generate: (body: GenerateRequest) => http.post<GenerateResponse>("/generate", body).then((r) => r.data),
  generations: (q: string, limit: number, offset: number) =>
    http.get<GenerationPage>("/generations", { params: { q: q || undefined, limit, offset } }).then((r) => r.data),
  deleteGeneration: (id: number) => http.delete(`/generations/${id}`),
  modelInfo: () => http.get<ModelInfo>("/model/info").then((r) => r.data),
  startTraining: (cfg: TrainConfig) => http.post<TrainingRun>("/training/start", cfg).then((r) => r.data),
  runs: () => http.get<TrainingRun[]>("/training/runs").then((r) => r.data),
};

export type { Generation };
