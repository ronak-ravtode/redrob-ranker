from __future__ import annotations

import hashlib
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .jd_understanding import JDProfile, get_default_jd_profile
from .text_utils import clipped, normalize


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#-]*")
_HASH_DIMS = 192


CONCEPT_SYNONYMS: dict[str, tuple[str, ...]] = {
    "ranking_relevance": (
        "ranking", "ranker", "re-ranker", "reranking", "learning to rank",
        "learning-to-rank", "relevance", "relevance ranking", "scoring function",
        "match quality", "shortlist quality", "search relevance",
    ),
    "recommendation_personalization": (
        "recommendation", "recommendation system", "recommendation-style",
        "personalization", "discovery feed", "feed ranking", "engagement signals",
        "content-based ranking", "collaborative filtering",
    ),
    "matching_systems": (
        "matching", "candidate matching", "candidate-jd matching", "candidate jd matching",
        "match people to roles", "most relevant matches", "connect them to the most relevant",
        "find the right candidate", "talent matching",
    ),
    "semantic_retrieval": (
        "retrieval", "semantic search", "dense retrieval", "hybrid search",
        "embedding-based search", "sparse and dense", "bm25", "query understanding",
        "search and discovery", "information retrieval", "surface relevant",
    ),
    "vector_search_infra": (
        "vector search", "vector database", "vector index", "embedding store",
        "faiss", "hnsw", "pinecone", "qdrant", "milvus", "weaviate",
        "opensearch", "elasticsearch", "nearest-neighbor", "ann index",
    ),
    "evaluation_experimentation": (
        "ndcg", "mrr", "map", "recall@", "a/b test", "a/b testing",
        "ab test", "offline metrics", "online metrics", "human relevance",
        "human judgments", "evaluation framework", "interleaving", "feedback loop",
    ),
    "production_scale": (
        "production", "shipped", "deployed", "serving", "served", "rollout",
        "real users", "production traffic", "latency", "p95", "monitoring",
        "rollback", "index refresh", "index versioning", "operated", "at scale",
    ),
    "ownership_delivery": (
        "owned", "led", "designed", "built", "drove", "architected",
        "end-to-end", "end to end", "from scratch", "principal owner", "hands-on owner",
    ),
    "ml_engineering_stack": (
        "python", "pytorch", "scikit-learn", "sklearn", "xgboost", "lightgbm",
        "sentence-transformers", "hugging face", "mlflow", "feature store", "fastapi",
    ),
}


CONCEPT_LABELS = {
    "ranking_relevance": "ranking and relevance optimization",
    "recommendation_personalization": "recommendation and personalization",
    "matching_systems": "candidate-role matching",
    "semantic_retrieval": "semantic retrieval and information retrieval",
    "vector_search_infra": "vector search infrastructure",
    "evaluation_experimentation": "ranking evaluation and experimentation",
    "production_scale": "production scale and operations",
    "ownership_delivery": "end-to-end ownership",
    "ml_engineering_stack": "ML engineering stack",
}


def _stable_index(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % _HASH_DIMS


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize(text))


def _add(vec: dict[str, float], key: str, value: float) -> None:
    if value:
        vec[key] = vec.get(key, 0.0) + value


def _fallback_embedding(text: str, weight: float = 1.0) -> dict[str, float]:
    normalized = normalize(text)
    vec: dict[str, float] = {}

    for concept, phrases in CONCEPT_SYNONYMS.items():
        hits = 0
        for phrase in phrases:
            if phrase in normalized:
                hits += 1
        if hits:
            _add(vec, f"concept:{concept}", weight * (1.0 + math.log1p(hits)))

    tokens = _tokenize(normalized)
    for token in tokens:
        if len(token) < 3:
            continue
        _add(vec, f"hash:{_stable_index(token)}", weight * 0.18)

    for left, right in zip(tokens, tokens[1:]):
        if len(left) >= 3 and len(right) >= 3:
            _add(vec, f"hash:{_stable_index(left + '_' + right)}", weight * 0.10)
    return vec


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return clipped(dot / (left_norm * right_norm))


def _candidate_sections(candidate: dict[str, Any]) -> list[tuple[str, float]]:
    profile = candidate.get("profile", {})
    sections: list[tuple[str, float]] = [
        (" ".join(str(profile.get(key, "")) for key in ("headline", "summary", "current_title")), 0.55),
        (" ".join(str(skill.get("name", "")) for skill in candidate.get("skills", [])), 0.30),
    ]
    career = []
    for job in candidate.get("career_history", []):
        career.append(f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')}")
    sections.append((" ".join(career), 1.00))
    return sections


def _candidate_embedding(candidate: dict[str, Any]) -> dict[str, float]:
    vec: dict[str, float] = {}
    for text, weight in _candidate_sections(candidate):
        for key, value in _fallback_embedding(text, weight).items():
            _add(vec, key, value)
    return vec


@lru_cache(maxsize=4)
def _jd_embedding(text: str) -> dict[str, float]:
    return _fallback_embedding(text, 1.0)


@lru_cache(maxsize=1)
def _local_transformer_model() -> object | None:
    model_path = os.environ.get("REDROB_SEMANTIC_MODEL_PATH") or str(Path("models") / "all-MiniLM-L6-v2")
    path = Path(model_path)
    if not path.exists():
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None
    try:
        return SentenceTransformer(str(path), device="cpu")
    except Exception:
        return None


def _transformer_score(candidate_text: str, jd_text: str) -> float | None:
    model = _local_transformer_model()
    if model is None:
        return None
    try:
        embeddings = model.encode([jd_text, candidate_text], normalize_embeddings=True, show_progress_bar=False)
        score = float(sum(float(a) * float(b) for a, b in zip(embeddings[0], embeddings[1])))
    except Exception:
        return None
    return clipped((score + 1.0) / 2.0)


def _top_concepts(candidate_vec: dict[str, float], jd_vec: dict[str, float], limit: int = 3) -> list[str]:
    overlaps: list[tuple[float, str]] = []
    for concept, label in CONCEPT_LABELS.items():
        key = f"concept:{concept}"
        overlap = min(candidate_vec.get(key, 0.0), jd_vec.get(key, 0.0))
        if overlap > 0:
            overlaps.append((overlap, label))
    overlaps.sort(key=lambda item: (-item[0], item[1]))
    return [label for _score, label in overlaps[:limit]]


def semantic_features(candidate: dict[str, Any], jd_profile: JDProfile | None = None) -> dict[str, Any]:
    jd = jd_profile or get_default_jd_profile()
    candidate_vec = _candidate_embedding(candidate)
    jd_vec = _jd_embedding(jd.text)
    fallback_score = cosine_similarity(candidate_vec, jd_vec)

    candidate_text = " ".join(text for text, _weight in _candidate_sections(candidate))
    transformer_score = _transformer_score(candidate_text, jd.text)
    if transformer_score is None:
        score = fallback_score
        model_name = "deterministic-domain-embedding"
    else:
        score = clipped(0.70 * transformer_score + 0.30 * fallback_score)
        model_name = "local-sentence-transformer"

    return {
        "semantic_fit_score": clipped(score),
        "semantic_model": model_name,
        "semantic_top_concepts": _top_concepts(candidate_vec, jd_vec),
    }
