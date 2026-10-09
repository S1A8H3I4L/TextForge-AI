"""FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, generation, training
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models import models  # noqa: F401  (register tables)
from app.models.models import TrainingRun
from app.services.generator import load_active_model, registry


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)  # simple bootstrap; add Alembic migrations before schema changes in production
    with SessionLocal() as db:
        # a crash mid-training leaves runs stuck as "running": mark them failed
        for run in db.query(TrainingRun).filter(TrainingRun.status.in_(["queued", "running"])):
            run.status, run.error = "failed", "Server restarted during training"
        db.commit()
        try:
            load_active_model(db)
        except Exception as exc:  # noqa: BLE001 - API must still boot without TF/model
            print(f"[startup] model not loaded: {exc}")
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(generation.router)
api.include_router(training.router)


@api.get("/health", tags=["health"])
def health():
    return {"status": "ok", "model_loaded": registry.loaded}


app.include_router(api)
