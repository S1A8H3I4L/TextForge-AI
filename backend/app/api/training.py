from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import TrainingRun, User
from app.schemas.schemas import ModelInfoOut, TrainingRunOut, TrainStartIn
from app.services import trainer
from app.services.generator import registry

router = APIRouter(tags=["training"])


@router.get("/model/info", response_model=ModelInfoOut)
def model_info(_: User = Depends(get_current_user)):
    if not registry.loaded:
        return ModelInfoOut(loaded=False, message="No trained model yet. Start a training run.")
    v = registry.version or {}
    return ModelInfoOut(
        loaded=True, name=v.get("name"), vocab_size=v.get("vocab_size"), architecture=v.get("architecture"),
        dataset=v.get("dataset"), created_at=v.get("created_at"),
    )


@router.post("/training/start", response_model=TrainingRunOut, status_code=status.HTTP_202_ACCEPTED)
def start_training(body: TrainStartIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if trainer.is_training():
        raise HTTPException(status.HTTP_409_CONFLICT, "A training run is already in progress")
    run = TrainingRun(
        status="queued", config=body.model_dump(), epochs_planned=body.epochs, history=[], started_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    trainer.start_training_thread(run.id)
    return run


@router.get("/training/runs", response_model=list[TrainingRunOut])
def list_runs(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(TrainingRun).order_by(TrainingRun.id.desc()).limit(50).all()


@router.get("/training/runs/{run_id}", response_model=TrainingRunOut)
def get_run(run_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Training run not found")
    return run
