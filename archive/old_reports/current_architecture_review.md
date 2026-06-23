# Current Architecture Review

## Current Strengths

- Deterministic streaming ranker with stable tie-breaking by candidate ID.
- CPU-only and offline; no API calls, hosted inference, or network dependency.
- Strong evidence hierarchy: career-history evidence dominates profile summaries and skill-list claims.
- Practical ontology covers ranking, retrieval, vector infrastructure, evaluation, production, ownership, Python, and negative archetypes.
- High-confidence anomaly exclusion removes impossible profiles before ranking.
- Runtime and memory are already strong for a hackathon submission: prior release measurements were about 15.78s and 26.33 MB.
- Explanations are grounded in career titles, companies, and role descriptions rather than opaque model outputs.

## Current Weaknesses

- The system is mostly symbolic: it catches curated paraphrases but does not naturally generalize to unseen wording.
- Exact phrase coverage can miss profiles that describe search/recommendation work with adjacent language.
- The JD is implicit in `src/config.py`; there is no first-class structured JD object consumed by the pipeline.
- Anomaly handling is binary: every detected anomaly is treated as hard exclusion, with no confidence/action separation.
- Reasoning can become repetitive because many generated profiles share similar project templates.

## Likely Judge Concerns

- Whether the submission is an AI ranking system or only a well-engineered rule ranker.
- Whether keyword stuffing can still surface candidates with weak production ownership.
- Whether ranking quality transfers to paraphrases not present in the ontology.
- Whether explanations are faithful to score inputs and candidate evidence.
- Whether the system remains reproducible under offline sandbox conditions.

## Likely Winning-Team Approaches

- Hybrid retrieval/ranking systems: semantic retrieval for recall, evidence-based ranking for precision.
- JD understanding step that converts role text into structured requirements.
- Grounded explanations that cite profile evidence and scoring rationale.
- Integrity validation that distinguishes suspicious records from impossible records.
- Lightweight CPU-compatible models or deterministic embeddings, with clear reproducibility controls.

## Highest-ROI Improvements

- Add a semantic retrieval layer that improves paraphrase recall while keeping the evidence score dominant.
- Make the JD a structured `JDProfile` object so scoring, retrieval, and docs share one requirement representation.
- Blend scores as `0.75 * evidence + 0.25 * semantic` to improve semantic coverage without rewarding weak career evidence too much.
- Add anomaly confidence/action metadata: high confidence excludes, medium confidence penalizes, low confidence warns.
- Improve reason generation with specific project sentences plus semantic alignment concepts.
