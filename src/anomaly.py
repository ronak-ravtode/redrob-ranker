from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import REFERENCE_DATE
from .text_utils import normalize

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "company_founding_years.json"


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
