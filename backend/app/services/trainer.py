"""Background training job: preprocess -> build -> train -> save -> activate."""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import Dataset, ModelVersion, TrainingRun
from app.services import generator
from app.services.text_preprocessing import (
    Vocabulary, clean_text, download_dataset, make_sequences,
)

_train_lock = threading.Lock()


def is_training() -> bool:
    return _train_lock.locked()


def start_training_thread(run_id: int) -> None:
    threading.Thread(target=run_training, args=(run_id,), daemon=True).start()


def run_training(run_id: int) -> None:
    if not _train_lock.acquire(blocking=False):
        _fail(run_id, "Another training run is already in progress")
        return
    db = SessionLocal()
    try:
        run = db.get(TrainingRun, run_id)
        cfg = run.config
        run.status = "running"
        db.commit()

        from sklearn.model_selection import train_test_split
        from tensorflow import keras

        # 1. dataset ------------------------------------------------------
        path = download_dataset(settings.dataset_url, settings.dataset_path)
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if cfg.get("max_chars"):
            raw = raw[: cfg["max_chars"]]
        tokens = clean_text(raw).split(" ")
        vocab = Vocabulary.build(tokens, cfg["max_vocab"])
        ids = vocab.encode(tokens)
        X, y = make_sequences(ids, cfg["seq_length"])
        X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.1, random_state=42, shuffle=True)

        dataset = Dataset(
            name="Shakespeare (TensorFlow tutorial subset)", source_url=settings.dataset_url,
            file_path=str(path), num_chars=len(raw), num_tokens=len(tokens),
            preprocessing={"lowercase": True, "punctuation_removed": True, "tokenizer": "word", "max_vocab": cfg["max_vocab"]},
        )
        db.add(dataset)
        db.commit()

        # 2. model --------------------------------------------------------
        from app.services.lstm_model import build_lstm_model

        model = build_lstm_model(
            len(vocab), cfg["seq_length"], cfg["embedding_dim"], cfg["lstm_units"], cfg["lstm_layers"], cfg["dropout"]
        )
        out_dir = settings.artifacts_dir / f"run_{run_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        model_path = out_dir / "model.keras"
        vocab_path = out_dir / "vocab.json"
        vocab.save(vocab_path)

        # 3. training with early stopping + checkpoint ---------------------
        class DBProgress(keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                logs = logs or {}
                with SessionLocal() as s:
                    r = s.get(TrainingRun, run_id)
                    r.epochs_done = epoch + 1
                    r.history = [*r.history, {
                        "epoch": epoch + 1,
                        "loss": float(logs.get("loss", 0)), "val_loss": float(logs.get("val_loss", 0)),
                        "accuracy": float(logs.get("accuracy", 0)), "val_accuracy": float(logs.get("val_accuracy", 0)),
                    }]
                    r.best_val_loss = min([h["val_loss"] for h in r.history])
                    s.commit()

        callbacks = [
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
            keras.callbacks.ModelCheckpoint(str(model_path), monitor="val_loss", save_best_only=True),
            DBProgress(),
        ]
        model.fit(
            X_tr, y_tr, validation_data=(X_val, y_val),
            epochs=cfg["epochs"], batch_size=cfg["batch_size"], callbacks=callbacks, verbose=2,
        )

        # 4. register + activate ------------------------------------------
        db.query(ModelVersion).update({ModelVersion.is_active: False})
        mv = ModelVersion(
            name=f"lstm-run-{run_id}", dataset_id=dataset.id, vocab_size=len(vocab),
            architecture={k: cfg[k] for k in ("seq_length", "embedding_dim", "lstm_units", "lstm_layers", "dropout")},
            model_path=str(model_path), tokenizer_path=str(vocab_path), is_active=True,
        )
        db.add(mv)
        db.commit()
        run = db.get(TrainingRun, run_id)
        run.model_version_id = mv.id
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        generator.load_active_model(db)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
        db.rollback()
        _fail(run_id, f"{type(exc).__name__}: {exc}")
    finally:
        db.close()
        if _train_lock.locked():
            _train_lock.release()


def _fail(run_id: int, message: str) -> None:
    with SessionLocal() as s:
        r = s.get(TrainingRun, run_id)
        if r:
            r.status, r.error = "failed", message
            r.finished_at = datetime.now(timezone.utc)
            s.commit()
