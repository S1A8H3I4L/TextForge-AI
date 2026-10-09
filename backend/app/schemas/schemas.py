"""Pydantic request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class GenerateIn(BaseModel):
    seed_text: str = Field(min_length=1, max_length=1000)
    max_tokens: int = Field(default=50, ge=1, le=300)
    temperature: float = Field(default=0.8, gt=0.0, le=2.0)
    top_k: int | None = Field(default=None, ge=1, le=200)
    save: bool = True


class GenerationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    seed_text: str
    generated_text: str
    temperature: float
    max_tokens: int
    top_k: int | None
    created_at: datetime


class GenerationPage(BaseModel):
    items: list[GenerationOut]
    total: int


class GenerateOut(BaseModel):
    seed_text: str
    generated_text: str
    full_text: str
    generation: GenerationOut | None = None


class TrainStartIn(BaseModel):
    epochs: int = Field(default=20, ge=1, le=200)
    seq_length: int = Field(default=8, ge=2, le=50)
    embedding_dim: int = Field(default=128, ge=8, le=512)
    lstm_units: int = Field(default=256, ge=16, le=1024)
    lstm_layers: int = Field(default=2, ge=1, le=4)
    dropout: float = Field(default=0.2, ge=0.0, le=0.7)
    batch_size: int = Field(default=128, ge=8, le=1024)
    max_vocab: int = Field(default=8000, ge=500, le=50000)
    max_chars: int | None = Field(default=400000, ge=10000)


class TrainingRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    config: dict
    epochs_planned: int
    epochs_done: int
    history: list
    best_val_loss: float | None
    error: str | None
    model_version_id: int | None
    started_at: datetime
    finished_at: datetime | None


class ModelInfoOut(BaseModel):
    loaded: bool
    name: str | None = None
    vocab_size: int | None = None
    architecture: dict | None = None
    dataset: dict | None = None
    created_at: datetime | None = None
    message: str | None = None


class StatsOut(BaseModel):
    total_generations: int
    model_loaded: bool
    latest_run: TrainingRunOut | None
    recent: list[GenerationOut]
