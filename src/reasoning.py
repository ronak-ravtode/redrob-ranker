from __future__ import annotations

from datetime import date
from typing import Any

from .config import REFERENCE_DATE
from .text_utils import candidate_id_suffix


def _has(features: dict[str, Any], group: str) -> bool:
    return features["career"].get(group, 0) > 0


def _piece(text: str, sources: list[str]) -> dict[str, Any]:
    return {"text": text, "sources": sources}


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


def build_reason_details(candidate: dict[str, Any], features: dict[str, Any], score: float) -> dict[str, Any]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    years = _safe_float(profile.get("years_of_experience", 0.0))
    title = profile.get("current_title", "Unknown title")
    company = profile.get("current_company", "Unknown company")

    style = candidate_id_suffix(candidate.get("candidate_id")) % 4
    if style == 0:
        intro = f"{years:.1f} years; {title} at {company}"
    elif style == 1:
        intro = f"{title} at {company}, with {years:.1f} years of experience"
    elif style == 2:
        intro = f"{company} role {title}; {years:.1f} years total"
    else:
        intro = f"{years:.1f} years in the profile and currently {title} at {company}"

    strengths: list[dict[str, Any]] = []
    if _has(features, "ranking") and _has(features, "retrieval"):
        strengths.append(_piece("career evidence across ranking and retrieval", ["career_history.title", "career_history.description"]))
    elif _has(features, "ranking"):
        strengths.append(_piece("hands-on ranking or recommendation work", ["career_history.title", "career_history.description"]))
    elif _has(features, "retrieval"):
        strengths.append(_piece("hands-on search or retrieval work", ["career_history.title", "career_history.description"]))
    if _has(features, "vector_infra"):
        strengths.append(_piece("production vector/search infrastructure", ["career_history.description"]))
    if _has(features, "evaluation"):
        strengths.append(_piece("offline/online evaluation or A/B testing", ["career_history.description"]))
    if _has(features, "production") and _has(features, "ownership"):
        strengths.append(_piece("production ownership and measurable delivery", ["career_history.description"]))
    if _has(features, "fine_tuning"):
        strengths.append(_piece("LLM fine-tuning experience", ["career_history.description", "skills.name"]))

    if not strengths:
        strengths.append(_piece("adjacent ML engineering experience", ["profile.current_title", "career_history.description"]))
    strengths = strengths[:3]

    concerns: list[dict[str, Any]] = []
    notice = _safe_int(signals.get("notice_period_days", 180), 180)
    if notice > 90:
        concerns.append(_piece(f"{notice}-day notice period", ["redrob_signals.notice_period_days"]))
    elif notice > 30:
        concerns.append(_piece(f"{notice}-day notice period", ["redrob_signals.notice_period_days"]))

    try:
        last_active = date.fromisoformat(signals.get("last_active_date", "2020-01-01"))
        inactive_days = max(0, (REFERENCE_DATE - last_active).days)
        if inactive_days > 120:
            concerns.append(_piece("stale platform activity", ["redrob_signals.last_active_date"]))
    except ValueError:
        pass

    if features["location_fit"] < 0.4:
        concerns.append(_piece("location/relocation fit is weak", ["profile.country", "profile.location", "redrob_signals.willing_to_relocate"]))
    if features["consulting_only"]:
        concerns.append(_piece("career is consulting-only", ["career_history.company"]))
    if not _has(features, "evaluation"):
        concerns.append(_piece("limited explicit ranking-evaluation evidence", ["career_history.description"]))
    if not _has(features, "vector_infra"):
        concerns.append(_piece("limited explicit vector-infrastructure evidence", ["career_history.description"]))

    strength_text = ", ".join(piece["text"] for piece in strengths)
    reason = f"{intro}, with {strength_text}."
    if concerns:
        reason += f" Main concern: {concerns[0]['text']}."
    elif score >= 0.72:
        reason += " Strong fit for the JD's hands-on product-and-evaluation mandate."
    else:
        reason += " Fit is credible but less complete than higher-ranked candidates."
    return {
        "reason": reason,
        "strengths": strengths,
        "concerns": concerns,
        "sources": [*strengths, *concerns],
    }


def build_reason(candidate: dict[str, Any], features: dict[str, Any], score: float) -> str:
    return build_reason_details(candidate, features, score)["reason"]
