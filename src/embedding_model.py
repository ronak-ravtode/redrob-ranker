from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np


_MODEL_DIR: Path | None = None


def _resolve_model_dir() -> Path | None:
    env_path = os.environ.get("REDROB_EMBEDDING_MODEL_DIR")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    candidates = [
        Path(__file__).resolve().parents[1] / "models" / "all-MiniLM-L6-v2",
        Path("models") / "all-MiniLM-L6-v2",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _is_deterministic() -> bool:
    seed = os.environ.get("REDROB_EMBEDDING_SEED", "42")
    try:
        import random
        random.seed(int(seed))
        np.random.seed(int(seed))
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    model_dir = _resolve_model_dir()
    if model_dir is None:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        _is_deterministic()
        model = SentenceTransformer(str(model_dir), device="cpu")
        return model
    except Exception:
        return None


def encode_texts(texts: list[str], normalize: bool = True) -> np.ndarray | None:
    model = get_embedding_model()
    if model is None or not texts:
        return None
    try:
        embeddings = model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)
    except Exception:
        return None


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    if vec_a is None or vec_b is None:
        return 0.0
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    dot = float(np.dot(vec_a, vec_b))
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def embedding_model_info() -> dict[str, Any]:
    model = get_embedding_model()
    if model is None:
        return {"available": False, "model_name": "none"}
    model_dir = _resolve_model_dir()
    return {
        "available": True,
        "model_name": "all-MiniLM-L6-v2",
        "model_dir": str(model_dir),
        "dimension": 384,
        "device": "cpu",
    }
