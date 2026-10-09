export interface User { id: number; name: string; email: string }
export interface TokenResponse { access_token: string; token_type: string; user: User }

export interface Generation {
  id: number;
  seed_text: string;
  generated_text: string;
  temperature: number;
  max_tokens: number;
  top_k: number | null;
  created_at: string;
}
export interface GenerationPage { items: Generation[]; total: number }
export interface GenerateRequest { seed_text: string; max_tokens: number; temperature: number; top_k: number | null; save: boolean }
export interface GenerateResponse { seed_text: string; generated_text: string; full_text: string; generation: Generation | null }

export interface EpochMetrics { epoch: number; loss: number; val_loss: number; accuracy: number; val_accuracy: number }
export interface TrainingRun {
  id: number;
  status: "queued" | "running" | "completed" | "failed";
  config: Record<string, number | null>;
  epochs_planned: number;
  epochs_done: number;
  history: EpochMetrics[];
  best_val_loss: number | null;
  error: string | null;
  model_version_id: number | null;
  started_at: string;
  finished_at: string | null;
}
export interface TrainConfig {
  epochs: number; seq_length: number; embedding_dim: number; lstm_units: number;
  lstm_layers: number; dropout: number; batch_size: number; max_vocab: number; max_chars: number | null;
}
export interface ModelInfo {
  loaded: boolean; name?: string; vocab_size?: number; message?: string;
  architecture?: Record<string, number>; dataset?: { name: string; source_url: string; num_tokens: number };
  created_at?: string;
}
export interface Stats { total_generations: number; model_loaded: boolean; latest_run: TrainingRun | null; recent: Generation[] }
