"""Dataset loading, cleaning, tokenisation and sequence preparation.

Pipeline (matches the assignment):
    1. load a large public-domain text file (Shakespeare)
    2. lowercase + remove punctuation
    3. tokenise into words
    4. build (input sequence -> next token) training pairs
"""
from __future__ import annotations

import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

PAD, UNK = "<pad>", "<unk>"
_NON_WORD = re.compile(r"[^a-z0-9\s']")  # punctuation removed, apostrophes kept (e.g. "o'er")
_WS = re.compile(r"\s+")


def download_dataset(url: str, dest: Path) -> Path:
    """Download the dataset once and cache it on disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size == 0:
        req = urllib.request.Request(url, headers={"User-Agent": "textforge-ai/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted configured URL)
            dest.write_bytes(resp.read())
    return dest


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    return clean_text(text).split(" ") if text.strip() else []


class Vocabulary:
    """Word <-> id mapping. id 0 = padding, id 1 = unknown."""

    def __init__(self, itos: list[str]):
        self.itos = itos
        self.stoi = {w: i for i, w in enumerate(itos)}

    @classmethod
    def build(cls, tokens: list[str], max_vocab: int = 8000) -> "Vocabulary":
        counts = Counter(tokens)
        words = [w for w, _ in counts.most_common(max_vocab - 2)]
        return cls([PAD, UNK] + words)

    def __len__(self) -> int:
        return len(self.itos)

    def encode(self, tokens: list[str]) -> list[int]:
        unk = self.stoi[UNK]
        return [self.stoi.get(t, unk) for t in tokens]

    def decode(self, ids: list[int]) -> str:
        return " ".join(self.itos[i] for i in ids if i > 1 and i < len(self.itos))

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps({"itos": self.itos}))

    @classmethod
    def load(cls, path: Path) -> "Vocabulary":
        return cls(json.loads(Path(path).read_text())["itos"])


def make_sequences(ids: list[int], seq_length: int) -> tuple[np.ndarray, np.ndarray]:
    """Sliding window: X[i] = ids[i : i+seq_length], y[i] = ids[i+seq_length]."""
    arr = np.asarray(ids, dtype=np.int32)
    n = len(arr) - seq_length
    if n <= 0:
        raise ValueError("Dataset too small for the chosen sequence length")
    idx = np.arange(seq_length)[None, :] + np.arange(n)[:, None]
    return arr[idx], arr[seq_length:]
