from __future__ import annotations

from datetime import date
from typing import Any

from .config import REFERENCE_DATE
from .text_utils import candidate_id_suffix, normalize


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------

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


def _clean_text(value: object) -> str:
    text = str(value or "")
    for dash in ("\ufffd", "\u2013", "\u2014"):
        text = text.replace(dash, "-")
    text = "".join(ch if ord(ch) < 128 else "-" for ch in text)
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Evidence detection helpers (used by fact extraction AND archetype selection)
# ---------------------------------------------------------------------------

EVIDENCE_TERMS = (
    "ranking", "ranker", "re-ranker", "learning-to-rank", "recommendation",
    "matching", "retrieval", "search", "bm25", "dense", "embedding", "vector",
    "faiss", "hnsw", "rag", "ndcg", "mrr", "recall@", "a/b", "metric",
    "latency", "p95", "engagement", "index", "versioning", "rollback",
    "refresh", "drift", "queries", "corpus", "shortlist",
)


def _job_evidence_score(job: dict[str, Any]) -> int:
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    return sum(1 for term in EVIDENCE_TERMS if term in text)


def _evidence_jobs(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    indexed = [
        (_job_evidence_score(job), -i, job)
        for i, job in enumerate(candidate.get("career_history", []))
    ]
    return [job for score, _i, job in sorted(indexed, reverse=True) if score > 0]


def _job_label(job: dict[str, Any]) -> str:
    title = _clean_text(job.get("title")) or "role"
    company = _clean_text(job.get("company")) or "company"
    return f"{title} at {company}"


def _relevant_skills_list(candidate: dict[str, Any], max_skills: int = 3) -> str:
    skills = candidate.get("skills", [])
    relevant: list[str] = []
    for skill in skills:
        name = skill.get("name", "")
        proficiency = skill.get("proficiency", "")
        months = _safe_int(skill.get("duration_months", 0))
        if name and (proficiency in ("expert", "advanced") or months >= 12):
            relevant.append(f"{name} ({months}mo)" if months >= 12 else name)
    if not relevant:
        relevant = [s.get("name", "") for s in skills[:3] if s.get("name")]
    return ", ".join(relevant[:max_skills])


def _jd_groups(features: dict[str, Any], limit: int = 3) -> list[str]:
    career = features.get("career", {})
    labels = [
        (career.get("ranking", 0), "ranking/relevance"),
        (career.get("retrieval", 0), "retrieval/search"),
        (career.get("evaluation", 0), "evaluation"),
        (career.get("vector_infra", 0), "vector infrastructure"),
        (career.get("production", 0), "production delivery"),
        (career.get("python", 0), "Python"),
    ]
    found = [label for count, label in labels if count]
    if not found:
        semantic = features.get("semantic_top_concepts", [])
        found = [_clean_text(item) for item in semantic if item]
    return found[:limit]


def _has(features: dict[str, Any], group: str) -> bool:
    return features.get("career", {}).get(group, 0) > 0


# ---------------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------------

def _primary_strength(candidate: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    evidence_jobs = _evidence_jobs(candidate)
    if evidence_jobs:
        top_job = evidence_jobs[0]
        months = _safe_int(top_job.get("duration_months", 0))
        suffix = f" for {months}mo" if months else ""
        return {
            "text": f"{_job_label(top_job)}{suffix}",
            "sources": ["career_history.title", "career_history.company", "career_history.duration_months"],
        }
    profile = candidate.get("profile", {})
    title = _clean_text(profile.get("current_title")) or "unknown title"
    company = _clean_text(profile.get("current_company")) or "unknown company"
    return {
        "text": f"current role is {title} at {company}",
        "sources": ["profile.current_title", "profile.current_company"],
    }


def _jd_connection(features: dict[str, Any]) -> dict[str, Any]:
    groups = _jd_groups(features)
    if groups:
        return {"text": ", ".join(groups), "sources": ["career_history.description", "skills.name"]}
    return {"text": "only indirect JD evidence", "sources": ["career_history.description", "profile.summary"]}


def _concern(candidate: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    location = _clean_text(profile.get("location")) or "unknown location"

    notice = _safe_int(signals.get("notice_period_days", 180), 180)
    if notice > 90:
        return {"text": f"{notice}-day notice period", "sources": ["redrob_signals.notice_period_days"]}

    try:
        last_active = date.fromisoformat(str(signals.get("last_active_date", "2020-01-01")))
        inactive_days = max(0, (REFERENCE_DATE - last_active).days)
        if inactive_days > 120:
            return {"text": f"last active {signals.get('last_active_date')}", "sources": ["redrob_signals.last_active_date"]}
    except ValueError:
        return {"text": "invalid or missing last active date", "sources": ["redrob_signals.last_active_date"]}

    if features.get("location_fit", 0.0) < 0.4:
        return {"text": f"location is {location}", "sources": ["profile.location"]}
    if features.get("consulting_only"):
        return {"text": "career is consulting-only", "sources": ["career_history.company"]}
    if features.get("research_only"):
        return {"text": "research profile has little production evidence", "sources": ["career_history.description"]}
    if features.get("framework_only"):
        return {"text": "framework/tutorial evidence outweighs shipped work", "sources": ["profile.summary", "career_history.description"]}
    if not features.get("career", {}).get("production"):
        return {"text": "production ownership is not explicit", "sources": ["career_history.description"]}
    if not features.get("career", {}).get("evaluation"):
        return {"text": "ranking evaluation evidence is thin", "sources": ["career_history.description"]}
    if not features.get("career", {}).get("vector_infra"):
        return {"text": "vector-infrastructure evidence is limited", "sources": ["career_history.description"]}
    if features.get("coding_activity_score", 0.0) < 0.35:
        github = signals.get("github_activity_score")
        github_text = (
            f"GitHub activity score {_safe_int(github, 0)}" if github not in (None, "")
            else "missing GitHub activity score"
        )
        return {"text": github_text, "sources": ["redrob_signals.github_activity_score"]}
    missing = _safe_int(features.get("missing_availability_signals", 0))
    if missing:
        return {"text": f"{missing} availability signals are missing", "sources": ["redrob_signals"]}

    last_active_text = _clean_text(signals.get("last_active_date")) or "recent activity date missing"
    return {
        "text": f"confirm hands-on scope despite last active {last_active_text} and {notice}-day notice",
        "sources": ["redrob_signals.last_active_date", "redrob_signals.notice_period_days", "career_history.description"],
    }


def _behavior_note(signals: dict[str, Any]) -> str:
    parts: list[str] = []
    if signals.get("last_active_date"):
        parts.append(f"active {signals['last_active_date']}")
    if signals.get("recruiter_response_rate") not in (None, ""):
        parts.append(f"{_safe_float(signals['recruiter_response_rate']) * 100:.0f}% recruiter response")
    if signals.get("interview_completion_rate") not in (None, ""):
        parts.append(f"{_safe_float(signals['interview_completion_rate']) * 100:.0f}% interview completion")
    if signals.get("saved_by_recruiters_30d") not in (None, ""):
        parts.append(f"saved {signals['saved_by_recruiters_30d']} times in 30d")
    return ", ".join(parts[:3])


# ---------------------------------------------------------------------------
# Archetype classification
# ---------------------------------------------------------------------------

def _archetype(features: dict[str, Any], score: float) -> str:
    if features.get("consulting_only") or features.get("research_only") or features.get("framework_only") or features.get("keyword_stuffer"):
        return "risky"
    if score < 0.82:
        return "borderline"
    c = features.get("career", {})
    if c.get("retrieval", 0) + c.get("vector_infra", 0) >= 5:
        return "search"
    if features.get("behavior_fit", 0.0) >= 0.78 and features.get("career_core", 0) < 6:
        return "behavioral"
    if features.get("product_company_history", 0.0) and c.get("production", 0) and c.get("ownership", 0):
        return "product_ml"
    if c.get("production", 0) >= 3:
        return "production"
    if features.get("behavior_fit", 0.0) >= 0.72:
        return "active_dev"
    return "general"


# ---------------------------------------------------------------------------
# Rank bands
# ---------------------------------------------------------------------------

_RANK_TOP = "top"       # 1-10
_RANK_MID = "mid"       # 11-50
_RANK_LOW = "low"       # 51-100


def _rank_band(rank: int) -> str:
    if rank <= 10:
        return _RANK_TOP
    if rank <= 50:
        return _RANK_MID
    return _RANK_LOW


# ---------------------------------------------------------------------------
# Pattern families  (10 families x 4 variants x 3 rank bands = 120 templates)
#
# All templates start with {subject} (candidate info) directly.
# No archetypes prefixes like "Search-fit leader:" or "Low-band note:".
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "product_ml": {
        _RANK_TOP: [
            "{subject} stands out for production ML ownership: {strength}. JD connection is {jd}. Concern: {concern}.",
            "{subject} is a strong shortlist candidate with {strength}. Fits the role through {jd}. Concern: {concern}.",
            "{subject} with shortlist strength from {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} is a top product-ML profile. Strength: {strength}. Role match: {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} is a solid product-ML fit: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} with strong evidence: {strength}. Evidence aligns with {jd}. Concern: {concern}.",
            "{subject} with production ownership via {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} has product-ML evidence: {strength}. Fits {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} clears the bar narrowly as product-ML: {strength}. JD match is {jd}. Concern: {concern}.",
            "{subject} is borderline product-ML. Best proof is {strength}. JD connection is {jd}. Concern: {concern}.",
            "{subject} has some production-ML signal from {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} with limited product-ML signal: {strength}. JD fit to {jd}. Concern: {concern}.",
        ],
    },
    "search": {
        _RANK_TOP: [
            "{subject} is strongest on search/retrieval: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} with strong retrieval evidence: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} has deep search expertise: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} is a top search/retrieval profile. Best proof: {strength}. Role match: {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} maps to the retrieval-heavy parts of the JD through {jd}. Strength: {strength}. Concern: {concern}.",
            "{subject} with retrieval/search depth: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} with retrieval/search depth: {strength}. Fits {jd}. Concern: {concern}.",
            "{subject} has strong search signal: {strength}. Evidence aligns with {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has retrieval evidence but limited breadth: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} with some search signal from {strength}. JD connection is {jd}. Concern: {concern}.",
            "{subject} with some search signal from {strength}. Limited fit to {jd}. Concern: {concern}.",
            "{subject} has limited search profile: {strength}. JD match: {jd}. Concern: {concern}.",
        ],
    },
    "behavioral": {
        _RANK_TOP: [
            "{subject} has strong Redrob signals: {behavior}. Strength: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} shows high engagement. Platform signals: {behavior}. Evidence: {strength}. Concern: {concern}.",
            "{subject} with useful Redrob signals ({behavior}). Strength: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} is a behavioral-fit leader. Active via {behavior}. Best proof: {strength}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} shows strong behavioral fit: {behavior}. Strength: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} has useful availability profile: {behavior}. Evidence: {strength}. Concern: {concern}.",
            "{subject} is more of a behavioral-fit bet than a lock. Strength: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} has good platform engagement: {behavior}. Fits {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} shows availability but lighter technical proof: {behavior}. Strength: {strength}. Concern: {concern}.",
            "{subject} with platform signals ({behavior}). Evidence: {strength}. Concern: {concern}.",
            "{subject} with engagement signals ({behavior}) but limited JD alignment to {jd}. Concern: {concern}.",
            "{subject} has behavioral signals ({behavior}) but thin evidence: {strength}. Concern: {concern}.",
        ],
    },
    "risky": {
        _RANK_TOP: [
            "{subject} has some signal from {strength}, but this is not a clean shortlist profile. Concern: {concern}.",
            "{subject} shows {strength} as the main positive. JD fit: {jd}. Concern: {concern}.",
            "{subject} remains risky despite {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} with limited clean signal: {strength}. JD link: {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} is a cautious include: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} with {strength} but notable risk. JD connection: {jd}. Concern: {concern}.",
            "{subject} with risk-adjusted score: {strength}. Fits {jd}. Concern: {concern}.",
            "{subject} is an include with caveats: {strength}. JD match: {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} is low confidence: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} barely clears the bar. Best proof: {strength}. Concern: {concern}.",
            "{subject} is a weak include: {strength}. Concern: {concern}.",
            "{subject} is borderline and risky: {strength}. Concern: {concern}.",
        ],
    },
    "borderline": {
        _RANK_TOP: [
            "{subject} clears the bar narrowly. Strength: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} has limited signal from {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} is marginal but relevant: {strength}. Concern: {concern}.",
            "{subject} has {strength}. JD match is limited to {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} is borderline: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} has marginal fit: {strength}. Concern: {concern}.",
            "{subject} with limited signal from {strength}. Concern: {concern}.",
            "{subject} has thin profile with {strength}. JD match: {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has very thin profile: {strength}. Concern: {concern}.",
            "{subject} clears the bar only narrowly: {strength}. Concern: {concern}.",
            "{subject} is low confidence include: {strength}. Concern: {concern}.",
            "{subject} is borderline low-band: {strength}. Concern: {concern}.",
        ],
    },
    "production": {
        _RANK_TOP: [
            "{subject} brings deep production delivery: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} with strong production delivery: {strength}. Fits {jd}. Concern: {concern}.",
            "{subject} has strong production track record: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} is a top production-delivery candidate. Strength: {strength}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} has production delivery evidence: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} shows solid production signal: {strength}. Fits {jd}. Concern: {concern}.",
            "{subject} with shipped systems: {strength}. JD connection: {jd}. Concern: {concern}.",
            "{subject} has production delivery evidence: {strength}. Evidence aligns with {jd}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has some production evidence: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} with limited production breadth: {strength}. Concern: {concern}.",
            "{subject} has limited production breadth: {strength}. Concern: {concern}.",
            "{subject} has limited production fit: {strength}. Evidence: {jd}. Concern: {concern}.",
        ],
    },
    "active_dev": {
        _RANK_TOP: [
            "{subject} is an active developer with engagement signals: {behavior}. Strength: {strength}. Concern: {concern}.",
            "{subject} shows strong developer activity: {behavior}. Best proof: {strength}. Concern: {concern}.",
            "{subject} has high engagement ({behavior}) plus {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} is an engaged developer. Activity: {behavior}. Evidence: {strength}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} shows active development: {behavior}. Strength: {strength}. Concern: {concern}.",
            "{subject} with developer engagement: {behavior}. Best proof: {strength}. Concern: {concern}.",
            "{subject} with developer engagement: {behavior}. Best proof: {strength}. Concern: {concern}.",
            "{subject} has good developer activity: {behavior}. Evidence: {strength}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has developer activity but limited JD alignment: {behavior}. Concern: {concern}.",
            "{subject} with platform signals: {behavior}. Concern: {concern}.",
            "{subject} with some engagement ({behavior}) but thin evidence: {strength}. Concern: {concern}.",
            "{subject} has developer activity ({behavior}) but limited evidence: {strength}. Concern: {concern}.",
        ],
    },
    "github_strong": {
        _RANK_TOP: [
            "{subject} has strong GitHub presence: {github}. Strength: {strength}. Concern: {concern}.",
            "{subject} is a top GitHub profile. Activity: {github}. Best proof: {strength}. Concern: {concern}.",
            "{subject} is an active open-source contributor ({github}). Evidence: {strength}. Concern: {concern}.",
            "{subject} shows strong developer signal via {github}. Strength: {strength}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} with notable GitHub activity: {github}. Strength: {strength}. Concern: {concern}.",
            "{subject} has good GitHub presence: {github}. Fits {jd}. Concern: {concern}.",
            "{subject} shows open-source work ({github}). Evidence: {strength}. Concern: {concern}.",
            "{subject} has developer signal: {github}. Best proof: {strength}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has some GitHub presence: {github}. Limited evidence: {strength}. Concern: {concern}.",
            "{subject} with GitHub activity ({github}). Concern: {concern}.",
            "{subject} with developer activity ({github}) but thin JD fit. Concern: {concern}.",
            "{subject} has borderline GitHub profile: {github}. Concern: {concern}.",
        ],
    },
    "skill_focused": {
        _RANK_TOP: [
            "{subject} with strong skill evidence: {skills}. JD connection: {jd}. Concern: {concern}.",
            "{subject} is a skill-focused profile. Key skills: {skills}. Fits {jd}. Concern: {concern}.",
            "{subject} has skill depth including {skills}. Evidence aligns with {jd}. Concern: {concern}.",
            "{subject} is a top skill profile with {skills}. JD link: {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} has relevant skills: {skills}. JD link: {jd}. Concern: {concern}.",
            "{subject} with {skills} as key evidence. JD connection: {jd}. Concern: {concern}.",
            "{subject} with {skills} as key evidence. JD connection: {jd}. Concern: {concern}.",
            "{subject} is skill-focused with {skills}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} has skills but limited career proof: {skills}. Concern: {concern}.",
            "{subject} with {skills} but limited evidence. Concern: {concern}.",
            "{subject} with {skills} but thin formal evidence. Concern: {concern}.",
            "{subject} has borderline skill profile: {skills}. Concern: {concern}.",
        ],
    },
    "general": {
        _RANK_TOP: [
            "{subject}. Strength: {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} brings {strength}. JD connection is {jd}. Concern: {concern}.",
            "{subject} has strongest proof in {strength}. Role fit comes from {jd}. Concern: {concern}.",
            "{subject} is a plausible fit via {strength}. JD link: {jd}. Concern: {concern}.",
        ],
        _RANK_MID: [
            "{subject} with evidence from {strength}. JD link: {jd}. Concern: {concern}.",
            "{subject} has strong evidence: {strength}. Fits {jd}. Concern: {concern}.",
            "{subject} with evidence aligning with {jd}. Strength: {strength}. Concern: {concern}.",
            "{subject} is a plausible fit with {strength}. Concern: {concern}.",
        ],
        _RANK_LOW: [
            "{subject} with limited signal from {strength}. Concern: {concern}.",
            "{subject} has some evidence: {strength}. Concern: {concern}.",
            "{subject} clears the bar only narrowly: {strength}. Concern: {concern}.",
            "{subject} has thin profile: {strength}. Concern: {concern}.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Template selection
# ---------------------------------------------------------------------------

def _select_template(
    features: dict[str, Any],
    score: float,
    candidate_id: str,
    rank: int,
) -> tuple[str, str]:
    archetype = _archetype(features, score)
    band = _rank_band(rank)
    variant = candidate_id_suffix(candidate_id) % 4
    templates = _TEMPLATES.get(archetype, _TEMPLATES["general"])
    return templates[band][variant], archetype


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_reason_details(
    candidate: dict[str, Any],
    features: dict[str, Any],
    score: float,
    rank: int = 1,
) -> dict[str, Any]:
    """Build structured reasoning for a single candidate.

    Args:
        candidate: raw candidate record from JSONL
        features: extracted feature dict from extract_features()
        score: final hybrid score
        rank: position in the ranked list (1-indexed, default 1)

    Returns:
        dict with keys: reason, strengths, concerns, sources
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = features.get("career", {})

    years = _safe_float(profile.get("years_of_experience", 0.0))
    title = _clean_text(profile.get("current_title")) or "Unknown title"
    company = _clean_text(profile.get("current_company")) or "Unknown company"
    location = _clean_text(profile.get("location")) or "Unknown"

    subject = f"{years:.1f}yr {title} at {company}"

    # --- extract all facts ---
    primary = _primary_strength(candidate, features)
    jd = _jd_connection(features)
    concern = _concern(candidate, features)
    behavior = _behavior_note(signals)
    skills = _relevant_skills_list(candidate)

    # --- GitHub text for github_strong pattern ---
    github = signals.get("github_activity_score")
    if github not in (None, ""):
        github_text = f"GitHub activity {_safe_int(github, 0)}"
    else:
        github_text = "limited GitHub signal"

    # --- secondary strength (used as supplementary fact) ---
    secondary = None
    if skills:
        secondary = {
            "text": f"skills include {skills}",
            "sources": ["skills.name", "skills.proficiency", "skills.duration_months"],
        }
    elif career.get("production", 0) >= 3:
        secondary = {
            "text": f"production evidence count {career['production']}",
            "sources": ["career_history.description"],
        }

    # --- select template ---
    template, archetype = _select_template(features, score, candidate.get("candidate_id", ""), rank)

    # --- build strengths list ---
    strengths: list[dict[str, Any]] = [primary]
    if secondary:
        strengths.append(secondary)

    concerns: list[dict[str, Any]] = [concern]

    # --- fill template ---
    reason = template.format(
        subject=subject,
        title=title,
        company=company,
        location=location,
        strength=primary["text"],
        jd=jd["text"],
        concern=concern["text"],
        behavior=behavior or "limited platform signal",
        skills=skills or "no strong skills flagged",
        github=github_text,
    )

    sources: list[dict[str, Any]] = [*strengths, jd, *concerns]

    return {
        "reason": reason,
        "strengths": strengths,
        "concerns": concerns,
        "sources": sources,
    }


def build_reason(
    candidate: dict[str, Any],
    features: dict[str, Any],
    score: float,
    rank: int = 1,
) -> str:
    """Return the human-readable reasoning string for a candidate."""
    return build_reason_details(candidate, features, score, rank)["reason"]
