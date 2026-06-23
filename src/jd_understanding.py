from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .config import NEGATIVE_PATTERNS, PATTERN_GROUPS, RELEVANT_TITLE_TERMS
from .text_utils import normalize


DEFAULT_JD_TEXT = """
Senior AI Engineer for intelligent candidate discovery. The role requires hands-on
production experience with candidate ranking, recommendation systems, matching,
semantic search, information retrieval, relevance optimization, vector search,
retrieval infrastructure, evaluation metrics, experimentation, and end-to-end
ownership of ML systems. Preferred profiles have built search or recommendation
pipelines, optimized retrieval/ranking quality, shipped production traffic, and
used offline and online evaluation such as NDCG, MRR, recall@K, human relevance
judgments, A/B tests, latency, monitoring, rollout, and feedback loops.
"""


@dataclass(frozen=True)
class JDProfile:
    text: str
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    domain_signals: tuple[str, ...]
    production_signals: tuple[str, ...]
    evaluation_signals: tuple[str, ...]
    ownership_signals: tuple[str, ...]
    negative_signals: tuple[str, ...]
    pattern_groups: dict[str, tuple[str, ...]]
    relevant_title_terms: tuple[str, ...]


def _terms_for(group: str) -> tuple[str, ...]:
    return PATTERN_GROUPS.get(group, ())


def build_jd_profile(jd_text: str | None = None) -> JDProfile:
    """Convert the role description into deterministic structured requirements.

    The challenge repository does not include an official JD file, so the default
    text is the local challenge summary encoded above. Ontology terms remain the
    source of truth for matching; the text lets reports and semantic retrieval use
    the same JD object instead of disconnected keyword lists.
    """
    text = " ".join((jd_text or DEFAULT_JD_TEXT).split())
    normalized = normalize(text)

    required = (
        "ranking",
        "retrieval",
        "recommendation systems",
        "matching systems",
        "semantic search",
        "evaluation",
        "production ownership",
    )
    preferred = (
        "vector search",
        "hybrid search",
        "learning to rank",
        "personalization",
        "relevance optimization",
        "search infrastructure",
        "python",
    )
    domains = tuple(
        term for term in (
            *_terms_for("ranking"),
            *_terms_for("retrieval"),
            *_terms_for("vector_infra"),
        )
        if term in normalized or term in PATTERN_GROUPS.get("ranking", ()) or term in PATTERN_GROUPS.get("retrieval", ())
    )

    return JDProfile(
        text=text,
        required_skills=required,
        preferred_skills=preferred,
        domain_signals=tuple(dict.fromkeys(domains)),
        production_signals=_terms_for("production"),
        evaluation_signals=_terms_for("evaluation"),
        ownership_signals=_terms_for("ownership"),
        negative_signals=tuple(term for terms in NEGATIVE_PATTERNS.values() for term in terms),
        pattern_groups={name: tuple(terms) for name, terms in PATTERN_GROUPS.items()},
        relevant_title_terms=tuple(RELEVANT_TITLE_TERMS),
    )


@lru_cache(maxsize=1)
def get_default_jd_profile() -> JDProfile:
    return build_jd_profile(DEFAULT_JD_TEXT)
