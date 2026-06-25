from __future__ import annotations

import math
import re
from datetime import date
from typing import Any

from .config import (
    CONSULTING_COMPANIES,
    NEGATIVE_PATTERNS,
    PREFERRED_CITIES,
    REFERENCE_DATE,
)
from .jd_understanding import get_default_jd_profile
from .text_utils import clipped, contains_any, normalize


JD_PROFILE = get_default_jd_profile()
PATTERN_GROUPS = JD_PROFILE.pattern_groups
RELEVANT_TITLE_TERMS = JD_PROFILE.relevant_title_terms

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
        [str(profile.get("headline") or ""), str(profile.get("summary") or ""), str(profile.get("current_title") or "")]
    )
    return normalize(all_career), normalize(current_career), normalize(profile_text)


def _skills_text(candidate: dict[str, Any]) -> str:
    return normalize(" ".join(skill.get("name", "") for skill in candidate.get("skills", [])))


def _skill_groups(candidate: dict[str, Any]) -> dict[str, int]:
    return _group_evidence(_skills_text(candidate))


def _skill_duration_score(candidate: dict[str, Any]) -> float:
    """Weight skills by how long the candidate has used them.

    Skills with 24+ months are fully weighted; shorter durations are scaled down.
    This penalizes candidates who recently added trendy skills without depth.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0
    total_weight = 0.0
    weighted_sum = 0.0
    for skill in skills:
        months = _safe_int(skill.get("duration_months", 0))
        weight = min(1.0, months / 24.0)  # full weight at 24+ months
        total_weight += weight
        weighted_sum += weight
    return clipped(weighted_sum / len(skills)) if skills else 0.0


COMPANY_SIZE_SCORE = {
    "1-10": 0.30, "11-50": 0.45, "51-200": 0.60,
    "201-500": 0.70, "501-1000": 0.80, "1001-5000": 0.85,
    "5001-10000": 0.90, "10001+": 0.95,
}

TECH_INDUSTRIES = {
    "technology", "computer software", "information technology", "it services",
    "artificial intelligence", "machine learning", "data science", "analytics",
    "internet", "saas", "cloud computing", " cybersecurity", "fintech",
    "health tech", "edtech", "e-commerce", "telecommunications",
}

TECH_EDUCATION_FIELDS = (
    "computer science",
    "information technology",
    "software engineering",
    "data science",
    "machine learning",
    "artificial intelligence",
    "mathematics",
    "statistics",
)

IMPACT_REGEX = re.compile(
    r"(?<![a-z0-9])(?:\d+(?:\.\d+)?\s?(?:%|ms|s|x|k|m|gb|tb)|p95|p99|latency|throughput|conversion|ctr|recall|ndcg|mrr|map)(?![a-z0-9])"
)


def _company_size_score(candidate: dict[str, Any]) -> float:
    """Map current company size to a 0-1 scale. Larger companies signal more structure."""
    size = normalize(candidate.get("profile", {}).get("current_company_size", ""))
    return COMPANY_SIZE_SCORE.get(size, 0.50)


def _industry_fit(candidate: dict[str, Any]) -> float:
    """Minor signal: tech-adjacent industries are preferred for an AI engineering role."""
    industry = normalize(candidate.get("profile", {}).get("current_industry", ""))
    if not industry:
        return 0.50
    if any(term in industry for term in TECH_INDUSTRIES):
        return 0.85
    return 0.50


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


def _skill_corroboration(career: dict[str, int], skills: dict[str, int], candidate: dict[str, Any] | None = None) -> float:
    corroborated = 0
    for group in ("ranking", "retrieval", "vector_infra", "evaluation", "python"):
        if career.get(group, 0) and skills.get(group, 0):
            corroborated += 1
    base = corroborated / 5.0

    if not candidate:
        return base

    signals = candidate.get("redrob_signals", {})

    # Boost if Redrob skill assessments confirm career-evidence skills.
    assessments = signals.get("skill_assessment_scores", {})
    assessment_boost = 0.0
    if isinstance(assessments, dict) and assessments:
        high_scores = sum(1 for v in assessments.values() if _safe_int(v, 0) >= 70)
        assessment_boost = min(0.10, high_scores * 0.02)

    # Boost from peer endorsements: log-normalized, caps at ~15 endorsements.
    endorsements = _safe_int(signals.get("endorsements_received", 0))
    endorsement_boost = min(0.05, math.log1p(max(0, endorsements)) / math.log(16) * 0.05)

    return clipped(base + assessment_boost + endorsement_boost)


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
    work_mode = normalize(signals.get("preferred_work_mode", ""))

    if country == "india":
        if any(city in location for city in PREFERRED_CITIES):
            base = 1.0
        else:
            base = 0.82 if willing else 0.58
    else:
        base = 0.30 if willing else 0.05

    # JD is hybrid; boost flexible/hybrid/onsite candidates, penalize remote-only.
    if work_mode in ("hybrid", "flexible", "onsite"):
        work_bonus = 0.05
    elif work_mode == "remote":
        work_bonus = -0.05
    else:
        work_bonus = 0.0

    return clipped(base + work_bonus)


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

    # Organic demand, platform visibility, profile engagement.
    profile_views = clipped(math.log1p(max(0, _safe_int(signals.get("profile_views_received_30d", 0)))) / math.log(20))
    searchAppear = clipped(math.log1p(max(0, _safe_int(signals.get("search_appearance_30d", 0)))) / math.log(20))
    completeness = clipped(_safe_float(signals.get("profile_completeness_score", 0)) / 100.0)

    # Account age: veteran users (>12mo) show commitment; very new (<1mo) = tire-kickers.
    signup = _date_or_default(signals.get("signup_date"), date(2020, 1, 1))
    account_days = max(0, (REFERENCE_DATE - signup).days)
    account_age = clipped(min(1.0, account_days / 365.0))

    # Network size: log-normalized platform connections.
    connections = _safe_int(signals.get("connection_count", 0))
    connection_norm = clipped(math.log1p(max(0, connections)) / math.log(50))

    # Offer acceptance rate: -1 = no offers, 0-1 = acceptance rate.
    # High rate = selective candidate likely to accept; -1 = unknown.
    offer_raw = _safe_float(signals.get("offer_acceptance_rate", -1), -1)
    if offer_raw < 0:
        offer_signal = 0.5  # neutral for no data
    else:
        offer_signal = clipped(offer_raw)

    return clipped(
        0.22 * recency
        + 0.12 * open_to_work
        + 0.14 * response_rate
        + 0.05 * response_speed
        + 0.12 * interview
        + 0.07 * saved
        + 0.08 * github_norm
        + 0.05 * verified
        + 0.04 * profile_views
        + 0.03 * searchAppear
        + 0.02 * completeness
        + 0.02 * account_age
        + 0.02 * connection_norm
        + 0.04 * offer_signal
    )


AVAILABILITY_FIELDS = (
    "last_active_date",
    "open_to_work_flag",
    "recruiter_response_rate",
    "interview_completion_rate",
    "notice_period_days",
    "verified_email",
    "verified_phone",
    "linkedin_connected",
    "offer_acceptance_rate",
)


def _missing_availability_signals(candidate: dict[str, Any]) -> int:
    signals = candidate.get("redrob_signals", {})
    return sum(1 for field in AVAILABILITY_FIELDS if signals.get(field) in (None, ""))


def _coding_activity_score(candidate: dict[str, Any]) -> float:
    signals = candidate.get("redrob_signals", {})
    github = _safe_float(signals.get("github_activity_score", -1), -1)
    if github < 0:
        github_norm = 0.0
    else:
        github_norm = clipped(github / 100.0)

    last_active = _date_or_default(signals.get("last_active_date"), date(2020, 1, 1))
    days = max(0, (REFERENCE_DATE - last_active).days)
    if days <= 30:
        recency = 1.0
    elif days <= 60:
        recency = 0.75
    elif days <= 120:
        recency = 0.40
    else:
        recency = 0.05
    return clipped(0.70 * github_norm + 0.30 * recency)


def _education_fit(candidate: dict[str, Any]) -> float:
    """Education quality signal from institution tiering.

    Tier 1 institutions are a minor positive signal; tier 3/4 is neutral.
    Used as a tiebreaker, not a gate — the JD does not require specific degrees.
    """
    education = candidate.get("education", [])
    if not education:
        return 0.5  # neutral when no education data
    tiers = [edu.get("tier", "unknown") for edu in education]
    # Weighted average: most recent degree matters more.
    tier_scores = {"tier_1": 1.0, "tier_2": 0.75, "tier_3": 0.50, "tier_4": 0.40, "unknown": 0.50}
    scores = [tier_scores.get(t, 0.50) for t in tiers]
    return scores[-1] if scores else 0.50


def _education_field_fit(candidate: dict[str, Any]) -> float:
    education = candidate.get("education", [])
    if not education:
        return 0.5
    fields = " ".join(normalize(edu.get("field_of_study")) for edu in education)
    if not fields:
        return 0.5
    if any(field in fields for field in TECH_EDUCATION_FIELDS):
        return 1.0
    if any(term in fields for term in ("engineering", "physics", "economics")):
        return 0.7
    return 0.45


def _current_relevance_score(title_relevant: bool, current: dict[str, int]) -> float:
    current_core = current["ranking"] + current["retrieval"] + current["evaluation"]
    if current_core >= 3 and title_relevant:
        return 1.0
    if current_core >= 2:
        return 0.8
    if current_core >= 1 and title_relevant:
        return 0.65
    if title_relevant:
        return 0.45
    return 0.0


def _measured_impact_score(candidate: dict[str, Any]) -> float:
    relevant_jobs = 0
    measured_jobs = 0
    for job in candidate.get("career_history", []):
        text = normalize(f"{job.get('title', '')} {job.get('description', '')}")
        ev = _group_evidence(text)
        if ev["ranking"] + ev["retrieval"] + ev["evaluation"] < 1:
            continue
        relevant_jobs += 1
        if IMPACT_REGEX.search(text):
            measured_jobs += 1
    if not relevant_jobs:
        return 0.0
    return clipped(measured_jobs / relevant_jobs)


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


def _salary_fit(candidate: dict[str, Any]) -> float:
    """Check if candidate salary expectations are reasonable for the role.

    Series A startup in India. Reasonable range ~15-40 LPA for senior ML.
    Below range = likely underqualified or low expectations (neutral).
    Above range = may be out of budget (slight penalty).
    No data = neutral (0.5).
    """
    signals = candidate.get("redrob_signals", {})
    salary = signals.get("expected_salary_range_inr_lpa")
    if not salary or not isinstance(salary, dict):
        return 0.5
    sal_min = _safe_float(salary.get("min"), 0)
    sal_max = _safe_float(salary.get("max"), 0)
    if sal_min <= 0 and sal_max <= 0:
        return 0.5
    mid = (sal_min + sal_max) / 2 if sal_min > 0 and sal_max > 0 else sal_min or sal_max
    if mid <= 0:
        return 0.5
    if 12 <= mid <= 45:
        return 1.0
    if 10 <= mid < 12 or 45 < mid <= 55:
        return 0.75
    if 8 <= mid < 10 or 55 < mid <= 70:
        return 0.50
    if mid < 8:
        return 0.35
    return 0.25


def _consulting_only(candidate: dict[str, Any]) -> bool:
    companies = [normalize(job.get("company")) for job in candidate.get("career_history", [])]
    return bool(companies) and all(company in CONSULTING_COMPANIES for company in companies)



def is_coarse_candidate(candidate: dict[str, Any]) -> bool:
    profile = candidate.get("profile", {})
    title = normalize(profile.get("current_title"))
    if contains_any(title, RELEVANT_TITLE_TERMS):
        return True
    all_text = " ".join(
        normalize(f"{job.get('title', '')} {job.get('description', '')}")
        for job in candidate.get("career_history", [])
    )
    return bool(COARSE_CAREER_REGEX.search(all_text))

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
    coding_activity_score = _coding_activity_score(candidate)
    missing_availability_signals = _missing_availability_signals(candidate)

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
            "salary_fit": _salary_fit(candidate),
            "education_fit": _education_fit(candidate),
            "education_field_fit": _education_field_fit(candidate),
            "skill_duration_score": _skill_duration_score(candidate),
            "coding_activity_score": coding_activity_score,
            "missing_availability_signals": missing_availability_signals,
            "framework_only": False,
            "company_size_score": _company_size_score(candidate),
            "industry_fit": _industry_fit(candidate),
            "current_relevance_score": 0.0,
            "measured_impact_score": 0.0,
            "anomaly_flags": anomaly_flags,
            "anomaly_confidence": 0.0,
            "anomaly_action": "none",
            "anomaly_penalty": 0.0,
            "semantic_fit_score": 0.0,
            "semantic_model": "not_scored",
            "semantic_top_concepts": [],
            "coarse_relevant": False,
            "_raw_signals": dict(candidate.get("redrob_signals", {})),
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
    skill_corroboration = _skill_corroboration(career, skill_ev, candidate)
    current_relevance_score = _current_relevance_score(title_relevant, current)
    measured_impact_score = _measured_impact_score(candidate)

    negative_flags: list[str] = []
    combined_non_skill = f"{career_text} {profile_text}"
    for name, patterns in NEGATIVE_PATTERNS.items():
        if contains_any(combined_non_skill, patterns):
            negative_flags.append(name)

    cv_only = "cv_speech_only" in negative_flags and career_core == 0
    research_only = (
        ("research" in current_title or "research_only" in negative_flags)
        and career["production"] == 0
        and career["ownership"] < 2
    )
    framework_only = (
        "framework_tutorial_only" in negative_flags
        and career["production"] == 0
        and career_core < 3
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
        "salary_fit": _salary_fit(candidate),
        "education_fit": _education_fit(candidate),
        "education_field_fit": _education_field_fit(candidate),
        "skill_duration_score": _skill_duration_score(candidate),
        "coding_activity_score": coding_activity_score,
        "missing_availability_signals": missing_availability_signals,
        "framework_only": framework_only,
        "company_size_score": _company_size_score(candidate),
        "industry_fit": _industry_fit(candidate),
        "current_relevance_score": current_relevance_score,
        "measured_impact_score": measured_impact_score,
        "anomaly_flags": anomaly_flags,
        "anomaly_confidence": 0.0,
        "anomaly_action": "none",
        "anomaly_penalty": 0.0,
        "semantic_fit_score": 0.0,
        "semantic_model": "not_scored",
        "semantic_top_concepts": [],
        "coarse_relevant": True,
        "_raw_signals": dict(candidate.get("redrob_signals", {})),
    }
