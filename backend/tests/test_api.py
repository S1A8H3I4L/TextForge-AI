"""API tests. TensorFlow is not required: generation uses a tiny fake model."""
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.generator import registry  # noqa: E402
from app.services.text_preprocessing import Vocabulary, clean_text, make_sequences, tokenize  # noqa: E402


class FakeModel:
    def __init__(self, vocab_size):
        self.n = vocab_size

    def __call__(self, x, training=False):
        p = np.ones((1, self.n)) / self.n
        return p


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth(client, email="a@example.com"):
    r = client.post("/api/auth/register", json={"name": "A", "email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_preprocessing():
    assert clean_text("To BE, or not to be!") == "to be or not to be"
    ids = list(range(10))
    X, y = make_sequences(ids, 3)
    assert X.shape == (7, 3) and list(X[0]) == [0, 1, 2] and y[0] == 3
    v = Vocabulary.build(tokenize("a b b c c c"), 10)
    assert v.decode(v.encode(["c", "b", "zzz"])) == "c b"  # unknown dropped on decode


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_auth_flow(client):
    h = auth(client, "flow@example.com")
    assert client.get("/api/auth/me", headers=h).json()["email"] == "flow@example.com"
    assert client.post("/api/auth/register", json={"name": "x", "email": "flow@example.com", "password": "password123"}).status_code == 409
    assert client.post("/api/auth/login", json={"email": "flow@example.com", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "flow@example.com", "password": "password123"}).status_code == 200
    assert client.get("/api/generations").status_code == 401


def test_generate_without_model(client):
    registry.model = None
    h = auth(client, "nomodel@example.com")
    assert client.post("/api/generate", json={"seed_text": "hello"}, headers=h).status_code == 503


def test_generate_history_and_isolation(client):
    vocab = Vocabulary.build(tokenize("to be or not to be that is the question"), 50)
    registry.model, registry.vocab, registry.seq_length = FakeModel(len(vocab)), vocab, 4
    h1, h2 = auth(client, "u1@example.com"), auth(client, "u2@example.com")

    r = client.post("/api/generate", json={"seed_text": "to be or", "max_tokens": 5, "top_k": 3}, headers=h1)
    assert r.status_code == 200, r.text
    assert len(r.json()["generated_text"].split()) == 5
    gid = r.json()["generation"]["id"]

    assert client.get("/api/generations", headers=h1).json()["total"] == 1
    assert client.get("/api/generations?q=zzzz", headers=h1).json()["total"] == 0
    # user 2 cannot see or delete user 1's generation
    assert client.get("/api/generations", headers=h2).json()["total"] == 0
    assert client.get(f"/api/generations/{gid}", headers=h2).status_code == 404
    assert client.delete(f"/api/generations/{gid}", headers=h2).status_code == 404
    assert client.delete(f"/api/generations/{gid}", headers=h1).status_code == 204

    assert client.post("/api/generate", json={"seed_text": "!!!"}, headers=h1).status_code == 422
    assert client.post("/api/generate", json={"seed_text": "x", "temperature": 0}, headers=h1).status_code == 422
    assert client.get("/api/stats", headers=h1).json()["total_generations"] == 0
    registry.model = None


def test_training_endpoints_require_auth(client):
    assert client.get("/api/training/runs").status_code == 401
    h = auth(client, "t@example.com")
    assert client.get("/api/training/runs", headers=h).json() == []
    assert client.get("/api/training/runs/999", headers=h).status_code == 404
    assert client.get("/api/model/info", headers=h).json()["loaded"] is False
