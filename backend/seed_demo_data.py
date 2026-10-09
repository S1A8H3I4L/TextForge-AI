"""Insert demo (dummy) data so the Dashboard, History and Training pages can be tried without TensorFlow.

Run from the backend folder with the virtual environment active:
    python scripts/seed_demo_data.py                      # seeds the first registered user
    python scripts/seed_demo_data.py --email you@mail.com # seeds a specific user
    python scripts/seed_demo_data.py --clear              # removes the demo rows again

How demo rows are recognised (so --clear never touches real data):
    - demo generations have model_version_id = NULL (real ones always store the model id)
    - the demo training run has config {"demo": true}

This does NOT create a trained model, so the Playground still needs a real training run.
"""
import argparse
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make `app` importable

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.models import models  # noqa: E402,F401  (registers tables)
from app.models.models import Generation, TrainingRun, User  # noqa: E402

# (seed, generated text, temperature, max_tokens, top_k) - invented placeholder text, not real model output
DEMO_GENERATIONS = [
    ("to be or not to be", "that is the question of all the winds that bear a king upon his sorrow and the night", 0.8, 20, None),
    ("first citizen", "speak the people hear me not for i am but a voice that cometh from the crowd", 0.7, 20, 20),
    ("o romeo romeo wherefore art thou", "my lord the moon is high and all the stars forget their ancient song", 0.9, 20, None),
    ("all the world's a stage", "and men and women merely players upon the hour that never stays", 0.6, 20, 10),
    ("what light through yonder window", "breaks upon the garden where the quiet roses sleep beneath the dew", 0.8, 20, None),
    ("now is the winter of our discontent", "made glorious summer by this sun of york and all the clouds that lowered", 1.0, 20, 40),
    ("double double toil and trouble", "fire burn and cauldron bubble in the dark where witches sing", 1.2, 20, None),
    ("friends romans countrymen", "lend me your ears for i have come to speak and not to praise the day", 0.5, 20, 5),
]


def seed(db, user: User) -> None:
    if db.query(Generation).filter(Generation.user_id == user.id, Generation.model_version_id.is_(None)).first():
        print("Demo data already present for this user. Run with --clear first to re-seed.")
        return

    now = datetime.now(timezone.utc)
    for i, (seed_text, text, temp, n, top_k) in enumerate(DEMO_GENERATIONS):
        db.add(Generation(
            user_id=user.id, model_version_id=None, seed_text=seed_text, generated_text=text,
            temperature=temp, max_tokens=n, top_k=top_k, created_at=now - timedelta(hours=i + 1),
        ))

    # a fake, completed training run whose loss curves look like early stopping kicked in
    history = []
    for e in range(1, 13):
        history.append({
            "epoch": e,
            "loss": round(3.0 + 3.4 * math.exp(-0.35 * e), 4),
            "val_loss": round(3.2 + 3.3 * math.exp(-0.35 * e) + (0.05 * (e - 9) if e > 9 else 0), 4),
            "accuracy": round(0.05 + 0.17 * (1 - math.exp(-0.3 * e)), 4),
            "val_accuracy": round(0.05 + 0.14 * (1 - math.exp(-0.3 * e)), 4),
        })
    db.add(TrainingRun(
        status="completed",
        config={"demo": True, "epochs": 20, "seq_length": 8, "embedding_dim": 128, "lstm_units": 256,
                "lstm_layers": 2, "dropout": 0.2, "batch_size": 128, "max_vocab": 8000, "max_chars": 400000},
        epochs_planned=20, epochs_done=len(history), history=history,
        best_val_loss=min(h["val_loss"] for h in history), error=None, model_version_id=None,
        started_by=user.id, started_at=now - timedelta(hours=2), finished_at=now - timedelta(hours=1),
    ))
    db.commit()
    print(f"Seeded {len(DEMO_GENERATIONS)} generations and 1 training run for {user.email}.")


def clear(db) -> None:
    gens = db.query(Generation).filter(Generation.model_version_id.is_(None)).delete(synchronize_session=False)
    runs = [r for r in db.query(TrainingRun).all() if isinstance(r.config, dict) and r.config.get("demo")]
    for r in runs:
        db.delete(r)
    db.commit()
    print(f"Removed {gens} demo generations and {len(runs)} demo training runs.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", help="seed this user (default: first registered user)")
    ap.add_argument("--clear", action="store_true", help="remove demo data instead of adding it")
    args = ap.parse_args()

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if args.clear:
            clear(db)
        else:
            q = db.query(User)
            user = q.filter(User.email == args.email.lower()).first() if args.email else q.order_by(User.id).first()
            if user is None:
                sys.exit("No user found. Register an account in the app first, then run this again.")
            seed(db, user)