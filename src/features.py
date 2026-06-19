from __future__ import annotations

import math
import re
from datetime import date
from typing import Any

from .config import (
    CONSULTING_COMPANIES,
    NEGATIVE_PATTERNS,
    PATTERN_GROUPS,
    PREFERRED_CITIES,
    REFERENCE_DATE,
    RELEVANT_TITLE_TERMS,
)
from .text_utils import clipped, contains_any, normalize

def _term_pattern(term: str) -> str:
    # Avoid false positives such as MAP matching roadmap while still matching
    # phrases with punctuation like a/b testing and recall@.
    return rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"


GROUP_REGEX = {
    name: re.compile("|".join(_term_pattern(term) for term in sorted(terms, key=len, reverse=True)))
    for name, terms in PATTERN_GROUPS.items()
}
COARSE_CAREER_REGEX = re.compile(
    r"learning[- ]to[- ]rank|re-?rank|ranking|ranker|recommendation|semantic search|"
    r"hybrid search|dense retrieval|embedding-based search|matching layer|"
    r"search and discovery|surface relevant|most relevant matches|personalization|"
    r"candidate[- ]jd matching|information retrieval|candidate ranking|match people to roles|"
    r"relevance ranking|search relevance|find the right candidate"
)


def _date_or_default(value: str | None, default: date) -> date:
    try:
        return date.fromisoformat(value or "")
    except ValueError:
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _career_text(candidate: dict[str, Any]) -> tuple[str, str, str]:
    history = candidate.get("career_history", [])
    all_career = " ".join(
        f"{job.get('title', '')} {job.get('description', '')}"
        for job in history
    )
    current_career = " ".join(
        f"{job.get('title', '')} {job.get('description', '')}"
        for job in history
        if job.get("is_current")
    )
    profile = candidate.get("profile", {})
    profile_text = " ".join(
        [profile.get("headline", ""), profile.get("summary", ""), profile.get("current_title", "")]
    )
    return normalize(all_career), normalize(current_career), normalize(profile_text)


def _skills_text(candidate: dict[str, Any]) -> str:
    return normalize(" ".join(skill.get("name", "") for skill in candidate.get("skills", [])))


def _skill_groups(candidate: dict[str, Any]) -> dict[str, int]:
    return _group_evidence(_skills_text(candidate))


def _group_evidence(text: str) -> dict[str, int]:
    return {name: len(set(regex.findall(text))) for name, regex in GROUP_REGEX.items()}


def _job_months(job: dict[str, Any]) -> int:
    return max(0, _safe_int(job.get("duration_months", 0)))


def _title_level(title: str) -> int:
    title = normalize(title)
    if not title:
        return 0
    if any(term in title for term in ("vp", "vice president", "director", "head", "founder")):
        return 5
    if any(term in title for term in ("staff", "principal", "distinguished")):
        return 4
    if any(term in title for term in ("lead", "senior")):
        return 3
    if any(term in title for term in ("engineer", "scientist", "analyst", "manager")):
        return 2
    return 1


def _company_mix(candidate: dict[str, Any]) -> tuple[float, float, float]:
    total_months = 0
    consulting_months = 0
    for job in candidate.get("career_history", []):
        months = _job_months(job)
        if not months:
            continue
        total_months += months
        if normalize(job.get("company")) in CONSULTING_COMPANIES:
            consulting_months += months
    if not total_months:
        return 0.0, 0.0, 0.0
    product_months = max(0, total_months - consulting_months)
    return total_months, consulting_months, product_months


def _job_stability(candidate: dict[str, Any]) -> float:
    durations = [
        _job_months(job)
        for job in candidate.get("career_history", [])
        if _job_months(job)
    ]
    if not durations:
        return 0.0
    short_stints = sum(1 for months in durations if months < 12)
    churn = short_stints / len(durations)
    multi_role = min(1.0, len(durations) / 6.0)
    return clipped(1.0 - 0.65 * churn + 0.15 * multi_role)


def _title_trajectory(candidate: dict[str, Any]) -> float:
    history = candidate.get("career_history", [])
    if len(history) < 2:
        return 0.5
    ordered = sorted(
        history,
        key=lambda job: _date_or_default(job.get("start_date"), date(1900, 1, 1)),
    )
    first_level = _title_level(ordered[0].get("title", ""))
    last_level = _title_level(ordered[-1].get("title", ""))
    if not first_level and not last_level:
        return 0.5
    delta = last_level - first_level
    return clipped(0.5 + delta / 8.0)


def _skill_corroboration(career: dict[str, int], skills: dict[str, int]) -> float:
    corroborated = 0
    for group in ("ranking", "retrieval", "vector_infra", "evaluation", "python"):
        if career.get(group, 0) and skills.get(group, 0):
            corroborated += 1
    return corroborated / 5.0


def _experience_fit(years: float) -> float:
    if 6.0 <= years <= 8.5:
        return 1.0
    if 5.0 <= years < 6.0 or 8.5 < years <= 9.5:
        return 0.88
    if 4.0 <= years < 5.0 or 9.5 < years <= 11.0:
        return 0.62
    if 3.0 <= years < 4.0 or 11.0 < years <= 13.0:
        return 0.35
    return 0.12


def _location_fit(candidate: dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    country = normalize(profile.get("country"))
    location = normalize(profile.get("location"))
    willing = bool(signals.get("willing_to_relocate"))

    if country == "india":
        if any(city in location for city in PREFERRED_CITIES):
            return 1.0
        return 0.82 if willing else 0.58
    return 0.30 if willing else 0.05


def _behavior_fit(candidate: dict[str, Any]) -> float:
    signals = candidate.get("redrob_signals", {})
    last_active = _date_or_default(signals.get("last_active_date"), date(2020, 1, 1))
    days = max(0, (REFERENCE_DATE - last_active).days)
    if days <= 30:
        recency = 1.0
    elif days <= 60:
        recency = 0.82
    elif days <= 90:
        recency = 0.62
    elif days <= 180:
        recency = 0.30
    else:
        recency = 0.05

    response_rate = clipped(_safe_float(signals.get("recruiter_response_rate", 0.0)))
    response_hours = max(0.0, _safe_float(signals.get("avg_response_time_hours", 240.0), 240.0))
    response_speed = clipped(1.0 - response_hours / 240.0)
    interview = clipped(_safe_float(signals.get("interview_completion_rate", 0.0)))
    open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.0
    saved = clipped(math.log1p(max(0, _safe_int(signals.get("saved_by_recruiters_30d", 0)))) / math.log(16))
    github = _safe_float(signals.get("github_activity_score", -1), -1)
    github_norm = 0.0 if github < 0 else clipped(github / 100.0)
    verified = sum(bool(signals.get(k)) for k in ("verified_email", "verified_phone", "linkedin_connected")) / 3.0

    return clipped(
        0.26 * recency
        + 0.18 * open_to_work
        + 0.18 * response_rate
        + 0.08 * response_speed
        + 0.13 * interview
        + 0.07 * saved
        + 0.06 * github_norm
        + 0.04 * verified
    )


def _notice_fit(candidate: dict[str, Any]) -> float:
    days = _safe_int(candidate.get("redrob_signals", {}).get("notice_period_days", 180), 180)
    if days <= 30:
        return 1.0
    if days <= 60:
        return 0.75
    if days <= 90:
        return 0.50
    if days <= 120:
        return 0.25
    return 0.05


def _consulting_only(candidate: dict[str, Any]) -> bool:
    companies = [normalize(job.get("company")) for job in candidate.get("career_history", [])]
    return bool(companies) and all(company in CONSULTING_COMPANIES for company in companies)



def is_coarse_candidate(candidate: dict[str, Any]) -> bool:
    profile = candidate.get("profile", {})
    title = normalize(profile.get("current_title"))
    if contains_any(title, RELEVANT_TITLE_TERMS):
        return True
    for job in candidate.get("career_history", []):
        text = normalize(f"{job.get('title', '')} {job.get('description', '')}")
        if COARSE_CAREER_REGEX.search(text):
            return True
    return False

def extract_features(candidate: dict[str, Any], anomaly_flags: list[str]) -> dict[str, Any]:
    profile = candidate.get("profile", {})
    career_text, current_career_text, profile_text = _career_text(candidate)
    career = _group_evidence(career_text)
    current = _group_evidence(current_career_text)
    profile_ev = _group_evidence(profile_text)
    skill_ev = _skill_groups(candidate)

    current_title = normalize(profile.get("current_title"))
    title_relevant = contains_any(current_title, RELEVANT_TITLE_TERMS)
    total_months, consulting_months, product_months = _company_mix(candidate)
    company_history = 1.0 if product_months > 0 else 0.0

    # Fast path: most of the 100K pool is obviously unrelated. Avoid dozens of
    # regex scans for profiles with neither a relevant title nor career evidence.
    if not title_relevant and not COARSE_CAREER_REGEX.search(career_text):
        zero = {name: 0 for name in PATTERN_GROUPS}
        return {
            "candidate_id": candidate.get("candidate_id"),
            "years": _safe_float(profile.get("years_of_experience", 0.0)),
            "title_relevant": False,
            "career": dict(zero),
            "current": dict(zero),
            "profile_evidence": dict(zero),
            "skill_evidence": dict(zero),
            "career_core": 0,
            "relevant_career_roles": 0,
            "relevant_career_months": 0,
            "total_career_months": int(total_months),
            "consulting_months": int(consulting_months),
            "product_months": int(product_months),
            "product_company_history": company_history,
            "title_trajectory": 0.5,
            "job_stability": _job_stability(candidate),
            "skill_corroboration": 0.0,
            "keyword_stuffer": False,
            "negative_flags": [],
            "cv_only": False,
            "research_only": False,
            "consulting_only": _consulting_only(candidate),
            "experience_fit": _experience_fit(_safe_float(profile.get("years_of_experience", 0.0))),
            "location_fit": _location_fit(candidate),
            "behavior_fit": _behavior_fit(candidate),
            "notice_fit": _notice_fit(candidate),
            "anomaly_flags": anomaly_flags,
            "coarse_relevant": False,
        }

    relevant_career_roles = 0
    relevant_career_months = 0
    for job in candidate.get("career_history", []):
        job_text = normalize(f"{job.get('title', '')} {job.get('description', '')}")
        ev = _group_evidence(job_text)
        if ev["ranking"] + ev["retrieval"] + ev["evaluation"] >= 2:
            relevant_career_roles += 1
            relevant_career_months += _job_months(job)

    ai_skill_mentions = (
        skill_ev["ranking"] + skill_ev["retrieval"] + skill_ev["vector_infra"]
        + skill_ev["evaluation"] + skill_ev["fine_tuning"]
    )
    career_core = career["ranking"] + career["retrieval"] + career["evaluation"]
    keyword_stuffer = ai_skill_mentions >= 3 and career_core == 0
    skill_corroboration = _skill_corroboration(career, skill_ev)

    negative_flags: list[str] = []
    combined_non_skill = f"{career_text} {profile_text}"
    for name, patterns in NEGATIVE_PATTERNS.items():
        if contains_any(combined_non_skill, patterns):
            negative_flags.append(name)

    cv_only = "cv_speech_only" in negative_flags and career_core == 0
    research_only = (
        "research" in current_title
        and career["production"] == 0
        and career["ownership"] < 2
    )

    return {
        "candidate_id": candidate.get("candidate_id"),
        "years": _safe_float(profile.get("years_of_experience", 0.0)),
        "title_relevant": title_relevant,
        "career": career,
        "current": current,
        "profile_evidence": profile_ev,
        "skill_evidence": skill_ev,
        "career_core": career_core,
        "relevant_career_roles": relevant_career_roles,
        "relevant_career_months": relevant_career_months,
        "total_career_months": int(total_months),
        "consulting_months": int(consulting_months),
        "product_months": int(product_months),
        "product_company_history": company_history,
        "title_trajectory": _title_trajectory(candidate),
        "job_stability": _job_stability(candidate),
        "skill_corroboration": skill_corroboration,
        "keyword_stuffer": keyword_stuffer,
        "negative_flags": negative_flags,
        "cv_only": cv_only,
        "research_only": research_only,
        "consulting_only": _consulting_only(candidate),
        "experience_fit": _experience_fit(_safe_float(profile.get("years_of_experience", 0.0))),
        "location_fit": _location_fit(candidate),
        "behavior_fit": _behavior_fit(candidate),
        "notice_fit": _notice_fit(candidate),
        "anomaly_flags": anomaly_flags,
        "coarse_relevant": True,
    }
