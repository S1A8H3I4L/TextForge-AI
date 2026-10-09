"""Text generation + in-memory model registry used by the API."""
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from app.services.text_preprocessing import Vocabulary, tokenize


def sample_next(probs: np.ndarray, temperature: float = 1.0, top_k: int | None = None) -> int:
    """Temperature + optional top-k sampling. Never returns pad/unk."""
    probs = np.asarray(probs, dtype=np.float64).copy()
    probs[:2] = 0.0  # block <pad>/<unk>
    probs = np.log(probs + 1e-9) / max(temperature, 1e-3)
    if top_k is not None and top_k < len(probs):
        cutoff = np.partition(probs, -top_k)[-top_k]
        probs[probs < cutoff] = -np.inf
    probs = np.exp(probs - np.max(probs))
    probs /= probs.sum()
    return int(np.random.choice(len(probs), p=probs))


def generate_text(model, vocab: Vocabulary, seq_length: int, seed_text: str,
                  max_tokens: int = 50, temperature: float = 0.8, top_k: int | None = None) -> str:
    """Iteratively predict the next token and append it to the context."""
    ids = vocab.encode(tokenize(seed_text))
    if not ids:
        raise ValueError("Seed text contains no usable words")
    out: list[int] = []
    for _ in range(max_tokens):
        window = ids[-seq_length:]
        window = [0] * (seq_length - len(window)) + window  # left-pad short seeds
        x = np.asarray([window], dtype=np.int32)
        probs = np.asarray(model(x, training=False))[0]
        nxt = sample_next(probs, temperature, top_k)
        ids.append(nxt)
        out.append(nxt)
    return vocab.decode(out)


class ModelRegistry:
    """Holds the active model so requests don't reload it from disk."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.model = None
        self.vocab: Vocabulary | None = None
        self.seq_length: int = 0
        self.version = None  # ModelVersion row snapshot (dict)

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self, model_path: str, tokenizer_path: str, seq_length: int, meta: dict) -> None:
        from tensorflow import keras

        with self._lock:
            self.model = keras.models.load_model(model_path)
            self.vocab = Vocabulary.load(Path(tokenizer_path))
            self.seq_length = seq_length
            self.version = meta

    def generate(self, **kwargs) -> str:
        if not self.loaded:
            raise RuntimeError("No trained model is loaded. Start a training run first.")
        return generate_text(self.model, self.vocab, self.seq_length, **kwargs)


registry = ModelRegistry()


def load_active_model(db) -> bool:
    """Load the model flagged active in the DB. Returns True on success."""
    from app.models.models import Dataset, ModelVersion

    mv = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).order_by(ModelVersion.id.desc()).first()
    if not mv or not Path(mv.model_path).exists():
        return False
    ds = db.get(Dataset, mv.dataset_id) if mv.dataset_id else None
    registry.load(
        mv.model_path, mv.tokenizer_path, mv.architecture.get("seq_length", 8),
        {
            "id": mv.id, "name": mv.name, "vocab_size": mv.vocab_size,
            "architecture": mv.architecture, "created_at": mv.created_at,
            "dataset": {"name": ds.name, "source_url": ds.source_url, "num_tokens": ds.num_tokens} if ds else None,
        },
    )
    return True
