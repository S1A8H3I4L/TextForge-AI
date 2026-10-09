
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Generation, TrainingRun, User
from app.schemas.schemas import (
    GenerateIn,
    GenerateOut,
    GenerationOut,
    GenerationPage,
    StatsOut,
    TrainingRunOut,
)
from app.services.generator import registry, tokenize

router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerateOut)
def generate(
    body: GenerateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Reject seed text that contains no valid tokens.
    if not any(char.isalnum() for char in body.seed_text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Seed text must contain valid words.",
        )

    # A trained model must be available for text generation.
    if not registry.loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No trained model available. "
                "Train one on the Training page."
            ),
        )

    try:
        text = registry.generate(
            seed_text=body.seed_text,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
            top_k=body.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    saved = None

    if body.save:
        saved = Generation(
            user_id=user.id,
            model_version_id=(registry.version or {}).get("id"),
            seed_text=body.seed_text,
            generated_text=text,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            top_k=body.top_k,
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)

    return GenerateOut(
        seed_text=body.seed_text,
        generated_text=text,
        full_text=f"{body.seed_text} {text}",
        generation=GenerationOut.model_validate(saved) if saved else None,
    )


@router.get("/generations", response_model=GenerationPage)
def list_generations(
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Generation).filter(Generation.user_id == user.id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            Generation.seed_text.ilike(like)
            | Generation.generated_text.ilike(like)
        )

    total = query.count()

    items = (
        query.order_by(
            Generation.created_at.desc(),
            Generation.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return GenerationPage(items=items, total=total)


def _own(db: Session, gen_id: int, user: User) -> Generation:
    generation = db.get(Generation, gen_id)

    if generation is None or generation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found",
        )

    return generation


@router.get("/generations/{gen_id}", response_model=GenerationOut)
def get_generation(
    gen_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _own(db, gen_id, user)


@router.delete(
    "/generations/{gen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_generation(
    gen_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    generation = _own(db, gen_id, user)
    db.delete(generation)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats", response_model=StatsOut)
def stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        db.query(func.count(Generation.id))
        .filter(Generation.user_id == user.id)
        .scalar()
        or 0
    )

    recent = (
        db.query(Generation)
        .filter(Generation.user_id == user.id)
        .order_by(
            Generation.created_at.desc(),
            Generation.id.desc(),
        )
        .limit(5)
        .all()
    )

    latest = (
        db.query(TrainingRun)
        .order_by(TrainingRun.id.desc())
        .first()
    )

    return StatsOut(
        total_generations=total,
        model_loaded=registry.loaded,
        latest_run=TrainingRunOut.model_validate(latest) if latest else None,
        recent=recent,
    )
