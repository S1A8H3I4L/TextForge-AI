"""Standalone assignment script: Generative AI with LSTM - Text Generation.

Run:  python scripts/lstm_text_generation.py            # train + generate sample outputs
      python scripts/lstm_text_generation.py --experiments   # bonus: compare architectures

Dataset: Shakespeare (public domain), downloaded automatically from
https://storage.googleapis.com/download.tensorflow.org/data/shakespeare.txt
Full works alternative: https://www.gutenberg.org/ebooks/100

Steps: 1) load + preprocess  2) build LSTM  3) train w/ validation, early stopping, checkpoint
       4) generate text from several seeds.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make `app` importable

import numpy as np  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from tensorflow import keras  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.services.generator import generate_text  # noqa: E402
from app.services.lstm_model import build_lstm_model  # noqa: E402
from app.services.text_preprocessing import (  # noqa: E402
    Vocabulary, clean_text, download_dataset, make_sequences,
)

SEEDS = ["to be or not to be", "first citizen", "o romeo romeo wherefore art thou"]


def prepare(seq_length: int, max_chars: int, max_vocab: int):
    path = download_dataset(settings.dataset_url, settings.dataset_path)        # 1. load
    raw = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    tokens = clean_text(raw).split(" ")                                          # lowercase, no punctuation, word tokens
    vocab = Vocabulary.build(tokens, max_vocab)
    X, y = make_sequences(vocab.encode(tokens), seq_length)                      # (sequence -> next token) pairs
    return vocab, train_test_split(X, y, test_size=0.1, random_state=42)


def run(name, seq_length=8, lstm_layers=2, lstm_units=256, epochs=20, max_chars=400_000, max_vocab=8000):
    vocab, (X_tr, X_val, y_tr, y_val) = prepare(seq_length, max_chars, max_vocab)
    model = build_lstm_model(len(vocab), seq_length, 128, lstm_units, lstm_layers, 0.2)   # 2. model
    out = settings.artifacts_dir / "standalone"
    out.mkdir(parents=True, exist_ok=True)
    hist = model.fit(                                                                      # 3. train
        X_tr, y_tr, validation_data=(X_val, y_val), epochs=epochs, batch_size=128, verbose=2,
        callbacks=[
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
            keras.callbacks.ModelCheckpoint(str(out / f"{name}.keras"), monitor="val_loss", save_best_only=True),
        ],
    )
    best = float(np.min(hist.history["val_loss"]))
    print(f"\n[{name}] best val_loss={best:.3f}  (perplexity≈{np.exp(best):.0f})")
    print(f"[{name}] sample outputs (temperature 0.7):")                                   # 4. generate
    for seed in SEEDS:
        text = generate_text(model, vocab, seq_length, seed, max_tokens=40, temperature=0.7, top_k=20)
        print(f"  seed: {seed!r}\n  -> {seed} {text}\n")
    return best


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", action="store_true", help="compare sequence lengths / depth (bonus)")
    ap.add_argument("--epochs", type=int, default=20)
    args = ap.parse_args()

    if args.experiments:
        results = {}
        for name, kw in {
            "baseline_seq8_1layer": dict(seq_length=8, lstm_layers=1),
            "seq8_2layers": dict(seq_length=8, lstm_layers=2),
            "seq16_2layers": dict(seq_length=16, lstm_layers=2),
        }.items():
            results[name] = run(name, epochs=args.epochs, **kw)
        print("\n=== Experiment summary (lower val_loss is better) ===")
        for k, v in sorted(results.items(), key=lambda kv: kv[1]):
            print(f"{k:28s} val_loss={v:.3f}")
    else:
        run("main", epochs=args.epochs)
