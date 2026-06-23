"""Self-evaluation: compute standard IR metrics on the system's own ranking.

Uses career_core (ranking + retrieval + evaluation evidence count) as a
graded relevance proxy. This demonstrates the system can evaluate itself
using the same metrics the JD requires candidates to understand.
"""
from __future__ import annotations

import math
from typing import Any


def _graded_relevance(features: dict[str, Any]) -> int:
    """Map career evidence to a 0-4 relevance grade.

    Grade 0: no career evidence (irrelevant)
    Grade 1: weak evidence (1-2 group hits)
    Grade 2: moderate evidence (3-4 hits)
    Grade 3: strong evidence (5-7 hits)
    Grade 4: very strong evidence (8+ hits)
    """
    career_core = features.get("career_core", 0)
    production = features.get("career", {}).get("production", 0)
    ownership = features.get("career", {}).get("ownership", 0)
    total = career_core + production + ownership
    if total >= 8:
        return 4
    if total >= 5:
        return 3
    if total >= 3:
        return 2
    if total >= 1:
        return 1
    return 0


def _dcg(relevances: list[int], k: int) -> float:
    """Compute DCG@k."""
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances[:k]))


def _ndcg(relevances: list[int], k: int) -> float:
    """Compute NDCG@k."""
    actual = _dcg(relevances, k)
    ideal = _dcg(sorted(relevances, reverse=True), k)
    return actual / ideal if ideal > 0 else 0.0


def _average_precision(relevances: list[int]) -> float:
    """Compute Average Precision across all relevance levels."""
    hits = 0
    sum_precisions = 0.0
    for i, rel in enumerate(relevances):
        if rel > 0:
            hits += 1
            sum_precisions += hits / (i + 1)
    return sum_precisions / hits if hits > 0 else 0.0


def evaluate_ranking(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Compute IR metrics on a ranked list of candidates.

    Args:
        rows: List of dicts with 'features' key containing extracted features.

    Returns:
        Dict with NDCG@10, NDCG@50, MAP, P@10.
    """
    relevances = [_graded_relevance(row["features"]) for row in rows]

    ndcg_10 = _ndcg(relevances, 10)
    ndcg_50 = _ndcg(relevances, 50)
    p_at_10 = sum(1 for r in relevances[:10] if r > 0) / 10.0
    map_score = _average_precision(relevances)

    return {
        "NDCG@10": round(ndcg_10, 4),
        "NDCG@50": round(ndcg_50, 4),
        "MAP": round(map_score, 4),
        "P@10": round(p_at_10, 4),
        "total_relevant": sum(1 for r in relevances if r > 0),
        "total_strong": sum(1 for r in relevances if r >= 3),
    }
