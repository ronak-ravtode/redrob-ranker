from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import REFERENCE_DATE
from .text_utils import normalize

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "company_founding_years.json"

HIGH_CONFIDENCE_FLAGS = {
    "job_negative_duration",
    "future_employment_date",
    "job_duration_mismatch",
    "company_before_founding_year",
    "experience_sum_mismatch",
    "contradictory_current_job_state",
    "multiple_expert_skills_with_zero_duration",
}

MEDIUM_CONFIDENCE_FLAGS = {
    "skill_duration_exceeds_profile_experience",
    "many_expert_skills_with_low_tenure",
    "current_job_missing_from_history",
}

LOW_CONFIDENCE_FLAGS = {
    "missing_experience_or_history",
    "thin_skill_duration_metadata",
}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _month_difference(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


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


@lru_cache(maxsize=1)
def _company_founding_years() -> dict[str, int]:
    try:
        with _DATA_PATH.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except OSError:
        return {}
    except json.JSONDecodeError:
        return {}

    result: dict[str, int] = {}
    for company, year in raw.items():
        try:
            result[normalize(company)] = int(year)
        except (TypeError, ValueError):
            continue
    return result


def detect_anomalies(candidate: dict[str, Any]) -> list[str]:
    """Detect high-confidence impossible-profile patterns.

    Do not flag common synthetic noise such as salary min > max or last-active
    before signup: those occur too frequently to identify the ~80 honeypots.
    """
    flags: list[str] = []
    history = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    founding_years = _company_founding_years()

    for job in history:
        start = _parse_date(job.get("start_date"))
        end = _parse_date(job.get("end_date")) or REFERENCE_DATE
        if start is None:
            continue
        if end < start:
            flags.append("job_negative_duration")
            break
        if start > REFERENCE_DATE:
            flags.append("future_employment_date")
            break
        if end > REFERENCE_DATE:
            flags.append("future_employment_date")
            break
        calculated = max(0, _month_difference(start, end))
        declared = _safe_int(job.get("duration_months", 0))
        if abs(calculated - declared) > 3:
            flags.append("job_duration_mismatch")
            break
        company = normalize(job.get("company"))
        founding_year = founding_years.get(company)
        if founding_year and start.year < founding_year:
            flags.append("company_before_founding_year")
            break

    declared_years = _safe_float(profile.get("years_of_experience", 0.0))
    summed_years = sum(_safe_float(job.get("duration_months", 0)) for job in history) / 12.0
    if abs(summed_years - declared_years) > 2.0:
        flags.append("experience_sum_mismatch")

    current_title = normalize(profile.get("current_title"))
    current_company = normalize(profile.get("current_company"))
    explicit_current = [job for job in history if bool(job.get("is_current"))]
    if len(explicit_current) > 1:
        flags.append("contradictory_current_job_state")
    elif explicit_current:
        job = explicit_current[0]
        job_company = normalize(job.get("company"))
        job_title = normalize(job.get("title"))
        if job.get("end_date") not in (None, ""):
            flags.append("contradictory_current_job_state")
        elif current_company and job_company and current_company != job_company:
            flags.append("contradictory_current_job_state")
        elif current_title and job_title and current_title not in job_title and job_title not in current_title:
            flags.append("contradictory_current_job_state")

    impossible_expert_skills = sum(
        1
        for skill in candidate.get("skills", [])
        if skill.get("proficiency") == "expert"
        and _safe_int(skill.get("duration_months", 0)) == 0
    )
    if impossible_expert_skills >= 3:
        flags.append("multiple_expert_skills_with_zero_duration")

    return sorted(set(flags))


def detect_anomaly_confidence(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    """Return integrity findings with confidence and ranking action.

    The legacy hard-rule detector remains authoritative for honeypot-grade
    exclusions. Additional medium/low signals are intentionally conservative so
    legitimate profiles are not discarded for noisy metadata.
    """
    findings: dict[str, dict[str, Any]] = {}

    def add(flag: str, confidence: float, action: str, evidence: str) -> None:
        existing = findings.get(flag)
        if existing and existing["confidence"] >= confidence:
            return
        findings[flag] = {
            "flag": flag,
            "confidence": confidence,
            "action": action,
            "evidence": evidence,
        }

    for flag in detect_anomalies(candidate):
        add(flag, 0.95, "exclude", "high-confidence impossible timeline or profile contradiction")

    history = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    declared_years = _safe_float(profile.get("years_of_experience", 0.0))
    declared_months = max(0.0, declared_years * 12.0)

    if declared_years <= 0 or not history:
        add("missing_experience_or_history", 0.30, "warn", "profile is missing usable experience or career history")

    max_skill_months = max((_safe_int(skill.get("duration_months", 0)) for skill in candidate.get("skills", [])), default=0)
    if declared_months and max_skill_months > declared_months + 24:
        add("skill_duration_exceeds_profile_experience", 0.65, "penalize", "skill tenure substantially exceeds total profile experience")

    expert_low_tenure = sum(
        1
        for skill in candidate.get("skills", [])
        if skill.get("proficiency") == "expert" and 0 < _safe_int(skill.get("duration_months", 0)) <= 6
    )
    if expert_low_tenure >= 4:
        add("many_expert_skills_with_low_tenure", 0.60, "penalize", "many expert skills have only a few months of duration")

    missing_duration = sum(1 for skill in candidate.get("skills", []) if skill.get("duration_months") in (None, ""))
    if missing_duration >= 5:
        add("thin_skill_duration_metadata", 0.25, "warn", "many skill records lack duration metadata")

    current_company = normalize(profile.get("current_company"))
    explicit_current = [job for job in history if bool(job.get("is_current"))]
    if current_company and history and not explicit_current:
        if all(normalize(job.get("company")) != current_company for job in history):
            add("current_job_missing_from_history", 0.55, "penalize", "profile current company is absent from career history")

    return sorted(findings.values(), key=lambda item: (-item["confidence"], item["flag"]))


def anomaly_action_summary(findings: list[dict[str, Any]]) -> tuple[list[str], float, str, float]:
    hard_flags = [item["flag"] for item in findings if item["action"] == "exclude"]
    max_confidence = max((float(item["confidence"]) for item in findings), default=0.0)
    if hard_flags:
        return hard_flags, max_confidence, "exclude", 0.0
    medium = [item for item in findings if item["action"] == "penalize"]
    if medium:
        penalty = min(0.16, 0.06 * len(medium))
        return [], max_confidence, "penalize", penalty
    if findings:
        return [], max_confidence, "warn", 0.0
    return [], 0.0, "none", 0.0
