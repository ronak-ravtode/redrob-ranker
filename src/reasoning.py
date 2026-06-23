from __future__ import annotations

import re
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
PRIMARY_TERMS = (
    "built", "led", "owned", "migrated", "ranking", "ranker", "re-ranker",
    "learning-to-rank", "recommendation", "matching", "retrieval", "search", "bm25",
    "dense", "embedding", "vector", "faiss", "hnsw", "rag", "serving", "pipeline",
)
METRIC_TERMS = (
    "ndcg", "mrr", "recall@", "a/b", "p95", "latency", "improved", "reduced",
    "engagement", "time-to-shortlist", "queries", "corpus", "items", "%", "+",
)


def _sentences(text: str) -> list[str]:
    clean = _clean_text(text)
    return [part.strip(" .") for part in re.split(r"(?<=[.!?])\s+", clean) if part.strip(" .")]


def _trim(text: str, limit: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:")


def _sentence_score(sentence: str, prefer_metrics: bool = False) -> int:
    lower = sentence.lower()
    if prefer_metrics:
        return sum(1 for term in EVIDENCE_TERMS if term in lower) + sum(2 for term in METRIC_TERMS if term in lower)
    return sum(2 for term in PRIMARY_TERMS if term in lower) + sum(1 for term in METRIC_TERMS if term in lower)


def _job_score(job: dict[str, Any]) -> int:
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    return sum(1 for term in EVIDENCE_TERMS if term in text)


def _evidence_jobs(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    indexed = [(_job_score(job), -index, job) for index, job in enumerate(candidate.get("career_history", []))]
    return [job for score, _index, job in sorted(indexed, reverse=True) if score > 0]


def _best_sentence(job: dict[str, Any], used: set[str], prefer_metrics: bool = False) -> str:
    ranked = sorted(_sentences(job.get("description", "")), key=lambda item: _sentence_score(item, prefer_metrics), reverse=True)
    for sentence in ranked:
        if sentence not in used and _sentence_score(sentence, prefer_metrics) > 0:
            used.add(sentence)
            return _trim(sentence)
    return ""


def _job_label(job: dict[str, Any]) -> str:
    title = _clean_text(job.get("title")) or "role"
    company = _clean_text(job.get("company")) or "the company"
    return f"{title} at {company}"


def _role_depth_text(features: dict[str, Any]) -> str:
    roles = _safe_int(features.get("relevant_career_roles", 0))
    months = _safe_int(features.get("relevant_career_months", 0))
    if roles >= 2 and months >= 36:
        return f"relevant work spans {roles} roles and about {months // 12} years"
    if roles >= 1:
        return f"has {roles} directly relevant role in the career history"
    return "has limited directly relevant role depth"


def _semantic_alignment_text(features: dict[str, Any]) -> str:
    score = _safe_float(features.get("semantic_fit_score", 0.0))
    concepts = [_clean_text(item) for item in features.get("semantic_top_concepts", []) if item]
    if score < 0.18 or not concepts:
        return ""
    if len(concepts) == 1:
        concept_text = concepts[0]
    elif len(concepts) == 2:
        concept_text = f"{concepts[0]} and {concepts[1]}"
    else:
        concept_text = f"{concepts[0]}, {concepts[1]}, and {concepts[2]}"
    return f"semantic retrieval aligns the profile with {concept_text}"


def build_reason_details(candidate: dict[str, Any], features: dict[str, Any], score: float) -> dict[str, Any]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    years = _safe_float(profile.get("years_of_experience", 0.0))
    title = _clean_text(profile.get("current_title")) or "Unknown title"
    company = _clean_text(profile.get("current_company")) or "Unknown company"

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
    used_sentences: set[str] = set()
    evidence_jobs = _evidence_jobs(candidate)
    for job in evidence_jobs[:2]:
        sentence = _best_sentence(job, used_sentences)
        if sentence:
            strengths.append(_piece(f"{_job_label(job)}: {sentence}", ["career_history.title", "career_history.company", "career_history.description"]))

    if _has(features, "evaluation") and not any(any(term in item["text"].lower() for term in METRIC_TERMS) for item in strengths):
        metric_sentence = _best_sentence(evidence_jobs[0], used_sentences, prefer_metrics=True) if evidence_jobs else ""
        if metric_sentence:
            strengths.append(_piece(f"evaluation evidence: {metric_sentence}", ["career_history.description"]))
        else:
            strengths.append(_piece("evaluation signal includes offline/online ranking metrics or A/B-test evidence", ["career_history.description"]))
    if _has(features, "production") and _has(features, "ownership"):
        strengths.append(_piece(_role_depth_text(features), ["career_history.title", "career_history.duration_months"]))
    if _has(features, "fine_tuning") and len(strengths) < 3:
        strengths.append(_piece("LLM or embedding-model tuning appears in career or skill evidence", ["career_history.description", "skills.name"]))
    semantic_alignment = _semantic_alignment_text(features)
    if semantic_alignment and len(strengths) < 3:
        strengths.append(_piece(semantic_alignment, ["semantic_fit_score", "semantic_top_concepts"]))

    if not strengths:
        strengths.append(_piece("profile is adjacent to ML engineering, but career descriptions provide limited concrete ranking evidence", ["profile.current_title", "career_history.description"]))
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

    primary = strengths[0]["text"]
    secondary = strengths[1]["text"] if len(strengths) > 1 else ""
    if style == 0:
        reason = f"{intro}. Strongest evidence: {primary}."
        if secondary:
            reason += f" Also, {secondary}."
    elif style == 1:
        reason = f"{intro}. The rank is driven by {primary}."
        if secondary:
            reason += f" Supporting signal: {secondary}."
    elif style == 2:
        reason = f"{intro}. Relevant fit comes from {primary}."
        if secondary:
            reason += f" Additional evidence: {secondary}."
    else:
        reason = f"{intro}. Key career evidence is {primary}."
        if secondary:
            reason += f" The profile also shows {secondary}."
    if concerns:
        reason += f" Main concern: {concerns[0]['text']}."
    elif score >= 0.72:
        fit_lines = [
            "This fits the hands-on search/ranking and evaluation mandate.",
            "The production and evaluation evidence is strong for this AI-engineering shortlist.",
            "Rank is based on shipped retrieval/ranking work rather than skill-list claims.",
            "Overall fit is strong for product ML ownership and ranking evaluation.",
        ]
        reason += f" {fit_lines[style]}"
    else:
        reason += " Fit is credible but less complete than higher-ranked candidates."
    if semantic_alignment and "semantic" not in reason.lower():
        reason += f" {semantic_alignment.capitalize()}."
    return {
        "reason": reason,
        "strengths": strengths,
        "concerns": concerns,
        "sources": [*strengths, *concerns],
    }


def build_reason(candidate: dict[str, Any], features: dict[str, Any], score: float) -> str:
    return build_reason_details(candidate, features, score)["reason"]
