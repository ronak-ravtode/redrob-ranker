from __future__ import annotations

import re
from datetime import date
from typing import Any

from .config import REFERENCE_DATE
from .text_utils import candidate_id_suffix, normalize


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


EVIDENCE_TERMS = (
    "ranking", "ranker", "re-ranker", "learning-to-rank", "recommendation", "matching",
    "retrieval", "search", "bm25", "dense", "embedding", "vector", "faiss", "hnsw", "rag",
    "ndcg", "mrr", "recall@", "a/b", "metric", "latency", "p95", "engagement",
    "index", "versioning", "rollback", "refresh", "drift", "queries", "corpus", "shortlist",
)


def _job_evidence_score(job: dict[str, Any]) -> int:
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    return sum(1 for term in EVIDENCE_TERMS if term in text)


def _evidence_jobs(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    indexed = [(_job_evidence_score(job), -i, job) for i, job in enumerate(candidate.get("career_history", []))]
    return [job for score, _i, job in sorted(indexed, reverse=True) if score > 0]


def _job_label(job: dict[str, Any]) -> str:
    title = _clean_text(job.get("title")) or "role"
    company = _clean_text(job.get("company")) or "company"
    return f"{title} at {company}"


def _relevant_skills_list(candidate: dict[str, Any], max_skills: int = 5) -> str:
    skills = candidate.get("skills", [])
    relevant = []
    for skill in skills:
        name = skill.get("name", "")
        proficiency = skill.get("proficiency", "")
        months = _safe_int(skill.get("duration_months", 0))
        if name and (proficiency in ("expert", "advanced") or months >= 12):
            if months >= 12:
                relevant.append(f"{name} ({months}mo)")
            else:
                relevant.append(name)
    if not relevant:
        relevant = [skill.get("name", "") for skill in skills[:3] if skill.get("name")]
    return ", ".join(relevant[:max_skills])


def _job_roles_summary(candidate: dict[str, Any]) -> str:
    history = candidate.get("career_history", [])
    if not history:
        return "no career history"
    roles = []
    for job in history[:4]:
        title = _clean_text(job.get("title")) or "unknown"
        company = _clean_text(job.get("company")) or "unknown"
        months = _safe_int(job.get("duration_months", 0))
        if months >= 12:
            roles.append(f"{title} at {company} ({months // 12}yr{months % 12}mo)")
        else:
            roles.append(f"{title} at {company} ({months}mo)")
    return "; ".join(roles)


def _evidence_depth_summary(features: dict[str, Any]) -> str:
    relevant_roles = _safe_int(features.get("relevant_career_roles", 0))
    relevant_months = _safe_int(features.get("relevant_career_months", 0))
    career_core = _safe_int(features.get("career_core", 0))
    if relevant_roles >= 3:
        return f"deep evidence across {relevant_roles} relevant roles ({relevant_months // 12}yr+ in ranking/retrieval)"
    if relevant_roles >= 2:
        return f"solid evidence from {relevant_roles} relevant roles ({relevant_months // 12}yr in ranking/retrieval)"
    if relevant_roles == 1:
        return f"one relevant role with {relevant_months}mo of direct ranking/retrieval work"
    if career_core >= 3:
        return f"limited formal roles but strong keyword evidence across career ({career_core} career-core matches)"
    if career_core >= 1:
        return f"some ranking/retrieval mentions but thin formal ownership"
    return "limited concrete ranking/retrieval evidence"


def build_reason_details(candidate: dict[str, Any], features: dict[str, Any], score: float) -> dict[str, Any]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    years = _safe_float(profile.get("years_of_experience", 0.0))
    title = _clean_text(profile.get("current_title")) or "Unknown title"
    company = _clean_text(profile.get("current_company")) or "Unknown company"
    location = _clean_text(profile.get("location")) or "Unknown"
    headline = _clean_text(profile.get("headline")) or ""

    strengths: list[dict[str, Any]] = []
    evidence_jobs = _evidence_jobs(candidate)

    if evidence_jobs:
        top_job = evidence_jobs[0]
        strengths.append({
            "text": f"top evidence from {_job_label(top_job)}",
            "sources": ["career_history.title", "career_history.company"],
        })

    depth = _evidence_depth_summary(features)
    strengths.append({
        "text": depth,
        "sources": ["career_history.title", "career_history.description"],
    })

    skills = _relevant_skills_list(candidate)
    if skills:
        strengths.append({
            "text": f"relevant skills: {skills}",
            "sources": ["skills.name", "skills.proficiency", "skills.duration_months"],
        })

    strengths = strengths[:3]

    concerns: list[dict[str, Any]] = []
    notice = _safe_int(signals.get("notice_period_days", 180), 180)
    if notice > 90:
        concerns.append({"text": f"{notice}-day notice period", "sources": ["redrob_signals.notice_period_days"]})

    try:
        last_active = date.fromisoformat(signals.get("last_active_date", "2020-01-01"))
        inactive_days = max(0, (REFERENCE_DATE - last_active).days)
        if inactive_days > 120:
            concerns.append({"text": "stale platform activity", "sources": ["redrob_signals.last_active_date"]})
    except ValueError:
        pass

    if features["location_fit"] < 0.4:
        concerns.append({"text": f"located in {location}, weak relocation fit", "sources": ["profile.location"]})
    if features["consulting_only"]:
        concerns.append({"text": "career is consulting-only", "sources": ["career_history.company"]})
    if not features.get("career", {}).get("evaluation"):
        concerns.append({"text": "limited ranking-evaluation evidence", "sources": ["career_history.description"]})
    if not features.get("career", {}).get("vector_infra"):
        concerns.append({"text": "limited vector-infrastructure evidence", "sources": ["career_history.description"]})

    primary = strengths[0]["text"]
    secondary = strengths[1]["text"] if len(strengths) > 1 else ""
    tertiary = strengths[2]["text"] if len(strengths) > 2 else ""

    parts = [f"{years:.1f}yr {title} at {company}"]
    parts.append(f"Strength: {primary}")
    if secondary:
        parts.append(secondary)
    if tertiary:
        parts.append(tertiary)
    if concerns:
        parts.append(f"Concern: {concerns[0]['text']}")

    reason = ". ".join(parts) + "."

    return {
        "reason": reason,
        "strengths": strengths,
        "concerns": concerns,
        "sources": [*strengths, *concerns],
    }


def _has(features: dict[str, Any], group: str) -> bool:
    return features.get("career", {}).get(group, 0) > 0


def build_reason(candidate: dict[str, Any], features: dict[str, Any], score: float) -> str:
    return build_reason_details(candidate, features, score)["reason"]
