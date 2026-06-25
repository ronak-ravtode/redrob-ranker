from __future__ import annotations

from datetime import date
from typing import Any

from .config import REFERENCE_DATE


def _sat(value: float, cap: float) -> float:
    return min(value, cap) / cap if cap else 0.0


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _availability_gate(features: dict[str, Any]) -> float:
    """Soft availability penalty for candidates who are clearly not in the market.

    JD says: 'a perfect-on-paper candidate who hasn't logged in for 6 months
    with 5% response rate is not actually available.' We apply a bounded
    additional penalty when both recency and engagement are poor.
    Also flags spray-and-pray: high application volume with low response.
    """
    signals = features.get("_raw_signals", {})
    try:
        last_active = date.fromisoformat(signals.get("last_active_date", "2020-01-01"))
        inactive_days = max(0, (REFERENCE_DATE - last_active).days)
    except (ValueError, TypeError):
        inactive_days = 999

    response_rate = _safe_float(signals.get("recruiter_response_rate", 0.5))
    open_to_work = bool(signals.get("open_to_work_flag"))
    applications = _safe_int(signals.get("applications_submitted_30d", 0))
    interview = _safe_float(signals.get("interview_completion_rate", 0.0))
    notice = _safe_int(signals.get("notice_period_days", 180), 180)
    verified_count = sum(bool(signals.get(k)) for k in ("verified_email", "verified_phone", "linkedin_connected"))
    saved = _safe_int(signals.get("saved_by_recruiters_30d", 0))
    offer = _safe_float(signals.get("offer_acceptance_rate", -1), -1)

    # Spray-and-pray: many applications + low response + inactive = noise.
    if applications >= 15 and response_rate < 0.10 and inactive_days > 60:
        return 0.18
    if applications >= 10 and response_rate < 0.10 and inactive_days > 90:
        return 0.12

    if inactive_days > 180 and response_rate < 0.10 and not open_to_work:
        return 0.20
    if inactive_days > 120 and response_rate < 0.15:
        return 0.10
    if inactive_days > 180 and not open_to_work:
        return 0.06
    if inactive_days > 90 and not open_to_work and response_rate < 0.25:
        return 0.08
    if notice > 120 and response_rate < 0.20:
        return 0.07
    if verified_count == 0 and saved == 0 and interview < 0.20:
        return 0.06
    if offer == 0 and response_rate < 0.30:
        return 0.05
    return 0.0


def score_features(features: dict[str, Any]) -> tuple[float, dict[str, float]]:
    c = features["career"]
    cur = features["current"]
    p = features["profile_evidence"]
    s = features["skill_evidence"]

    # Evidence from actual work is decisive. Summary and skills only support it.
    ranking_retrieval = (
        0.42 * _sat(c["ranking"] + c["retrieval"], 8)
        + 0.16 * _sat(c["vector_infra"], 4)
        + 0.12 * _sat(cur["ranking"] + cur["retrieval"], 4)
        + 0.08 * _sat(c["ranking"] + c["retrieval"] + c["production"], 10)
    )
    evaluation = 0.22 * _sat(c["evaluation"], 5)
    production_ownership = (
        0.12 * _sat(c["production"], 5)
        + 0.10 * _sat(c["ownership"], 6)
        + 0.04 * _sat(c["scale_systems"], 4)
    )
    evidence_score = ranking_retrieval + evaluation + production_ownership

    supporting = (
        0.045 * _sat(c["python"], 4)
        + 0.012 * _sat(c["fine_tuning"], 3)
        + 0.018 * _sat(p["ranking"] + p["retrieval"] + p["evaluation"], 5)
        + 0.010 * _sat(s["ranking"] + s["retrieval"] + s["vector_infra"], 5)
        + 0.024 * features["skill_corroboration"]
        + 0.020 * features.get("measured_impact_score", 0.0)
        + 0.020 * features.get("coding_activity_score", 0.0)
    )

    role_depth = min(1.0, 0.45 * features["relevant_career_roles"] + features["relevant_career_months"] / 72.0)
    title = 1.0 if features["title_relevant"] else 0.0
    fit = (
        0.042 * features["experience_fit"]
        + 0.028 * title
        + 0.030 * role_depth
        + 0.045 * features["location_fit"]
        + 0.016 * features["notice_fit"]
        + 0.020 * features["title_trajectory"]
        + 0.018 * features["job_stability"]
        + 0.028 * features["product_company_history"]
        + 0.012 * features.get("salary_fit", 0.5)
        + 0.010 * features.get("education_fit", 0.5)
        + 0.008 * features.get("education_field_fit", 0.5)
        + 0.008 * features.get("skill_duration_score", 0.0)
        + 0.018 * features.get("current_relevance_score", 0.0)
        + 0.006 * features.get("company_size_score", 0.5)
        + 0.005 * features.get("industry_fit", 0.5)
    )

    # Behavioral signals matter because availability and responsiveness are part
    # of Redrob's product promise, not just nice-to-have tie breakers.
    behavior = 0.160 * features["behavior_fit"]
    avail_penalty = _availability_gate(features)

    strong_jd_combo = (
        c["ranking"] + c["retrieval"] >= 6
        and c["evaluation"] >= 2
        and c["production"] >= 2
        and c["ownership"] >= 2
    )
    shortlist_bonus = 0.0
    if strong_jd_combo:
        shortlist_bonus += 0.08
    if strong_jd_combo and c["vector_infra"] >= 2:
        shortlist_bonus += 0.05
    if strong_jd_combo and features.get("product_company_history", 0.0) > 0 and features.get("behavior_fit", 0.0) >= 0.72:
        shortlist_bonus += 0.04
    if features.get("current_relevance_score", 0.0) >= 0.8 and features.get("measured_impact_score", 0.0) >= 0.5:
        shortlist_bonus += 0.03

    penalty = 0.0
    if features["keyword_stuffer"]:
        penalty += 0.34
    if features["consulting_only"]:
        penalty += 0.30
    if features["cv_only"]:
        penalty += 0.22
    if features["research_only"]:
        penalty += 0.30
    if features.get("framework_only"):
        penalty += 0.24
    if "recent_llm_only" in features["negative_flags"] and features["career_core"] < 2:
        penalty += 0.24
    if features["career_core"] == 0:
        penalty += 0.20
    if features["title_relevant"] and features["career_core"] <= 1:
        penalty += 0.12
    if c["production"] == 0 and features["career_core"] < 4:
        penalty += 0.10
    if features.get("coding_activity_score", 0.0) < 0.15:
        penalty += 0.16
    elif features.get("coding_activity_score", 0.0) < 0.30:
        penalty += 0.07
    penalty += min(0.14, 0.025 * _safe_int(features.get("missing_availability_signals", 0)))
    penalty += float(features.get("anomaly_penalty", 0.0))
    penalty += avail_penalty

    raw = evidence_score + supporting + fit + behavior + shortlist_bonus - penalty
    # Raw scores are intentionally not clipped at 1.0; clipping flattened many
    # strong candidates into identical scores and destroyed ranking information.
    evidence_only_score = max(0.0, raw)
    semantic_score = max(0.0, min(1.0, float(features.get("semantic_fit_score", 0.0))))
    score = 0.84 * evidence_only_score + 0.16 * semantic_score
    parts = {
        "evidence": evidence_score,
        "supporting": supporting,
        "fit": fit,
        "behavior": behavior,
        "shortlist_bonus": shortlist_bonus,
        "availability_penalty": avail_penalty,
        "penalty": penalty,
        "evidence_only": evidence_only_score,
        "semantic": semantic_score,
    }
    return score, parts
