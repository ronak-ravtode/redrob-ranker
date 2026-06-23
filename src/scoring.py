from __future__ import annotations

from typing import Any


def _sat(value: float, cap: float) -> float:
    return min(value, cap) / cap if cap else 0.0


def score_features(features: dict[str, Any]) -> tuple[float, dict[str, float]]:
    c = features["career"]
    cur = features["current"]
    p = features["profile_evidence"]
    s = features["skill_evidence"]

    # Evidence from actual work is decisive. Summary and skills only support it.
    ranking_retrieval = (
        0.36 * _sat(c["ranking"] + c["retrieval"], 8)
        + 0.12 * _sat(c["vector_infra"], 4)
        + 0.08 * _sat(cur["ranking"] + cur["retrieval"], 4)
        + 0.06 * _sat(c["ranking"] + c["retrieval"] + c["production"], 10)
    )
    evaluation = 0.18 * _sat(c["evaluation"], 5)
    production_ownership = (
        0.08 * _sat(c["production"], 5)
        + 0.08 * _sat(c["ownership"], 6)
        + 0.03 * _sat(c["scale_systems"], 4)
    )
    evidence_score = ranking_retrieval + evaluation + production_ownership

    supporting = (
        0.030 * _sat(c["python"], 4)
        + 0.015 * _sat(c["fine_tuning"], 3)
        + 0.018 * _sat(p["ranking"] + p["retrieval"] + p["evaluation"], 5)
        + 0.012 * _sat(s["ranking"] + s["retrieval"] + s["vector_infra"], 5)
        + 0.018 * features["skill_corroboration"]
    )

    role_depth = min(1.0, 0.45 * features["relevant_career_roles"] + features["relevant_career_months"] / 72.0)
    title = 1.0 if features["title_relevant"] else 0.0
    fit = (
        0.042 * features["experience_fit"]
        + 0.028 * title
        + 0.030 * role_depth
        + 0.022 * features["location_fit"]
        + 0.016 * features["notice_fit"]
        + 0.020 * features["title_trajectory"]
        + 0.018 * features["job_stability"]
        + 0.020 * features["product_company_history"]
    )

    # Behavioral signals are a modifier, not a replacement for skill fit.
    behavior = 0.035 * features["behavior_fit"]

    penalty = 0.0
    if features["keyword_stuffer"]:
        penalty += 0.34
    if features["consulting_only"]:
        penalty += 0.16
    if features["cv_only"]:
        penalty += 0.22
    if features["research_only"]:
        penalty += 0.18
    if "recent_llm_only" in features["negative_flags"] and features["career_core"] < 2:
        penalty += 0.18
    if features["career_core"] == 0:
        penalty += 0.20
    penalty += float(features.get("anomaly_penalty", 0.0))

    raw = evidence_score + supporting + fit + behavior - penalty
    # Raw scores are intentionally not clipped at 1.0; clipping flattened many
    # strong candidates into identical scores and destroyed ranking information.
    evidence_only_score = max(0.0, raw)
    semantic_score = max(0.0, min(1.0, float(features.get("semantic_fit_score", 0.0))))
    score = 0.75 * evidence_only_score + 0.25 * semantic_score
    parts = {
        "evidence": evidence_score,
        "supporting": supporting,
        "fit": fit,
        "behavior": behavior,
        "penalty": penalty,
        "evidence_only": evidence_only_score,
        "semantic": semantic_score,
    }
    return score, parts
