# Judge Presentation Content

## What Did You Build?

Concise answer: We built a deterministic hybrid AI ranking system for candidate discovery that combines JD understanding, semantic retrieval, evidence-based ranking, anomaly confidence, and grounded explanations.

Judge-friendly wording: The system uses semantic retrieval for recall and evidence ranking for precision. It finds candidates whose experience is semantically aligned with search, ranking, recommendation, and retrieval work, but only promotes them when career history proves production ownership.

Diagram suggestion: Eight-layer architecture diagram from `docs/final_architecture.md`.

Visual suggestion: Split-screen showing JD requirements on the left and candidate evidence/semantic alignment on the right.

## Why Is It AI-Powered?

Concise answer: The solution includes a JD understanding layer and semantic retrieval layer that embed the JD and candidate profile/career/skills into a shared semantic space.

Judge-friendly wording: It is not a keyword-only filter. The semantic layer captures ranking/retrieval synonyms such as recommendation, personalization, matching, semantic search, vector search, information retrieval, and relevance optimization.

Diagram suggestion: Vector similarity flow from JDProfile to candidate semantic profile.

Visual suggestion: Concept map linking "ranking" to recommendation, matching, relevance, retrieval, and vector search.

## How Do You Preserve Explainability?

Concise answer: Every rank includes career evidence, score components, anomaly metadata, and semantic concepts.

Judge-friendly wording: We can explain why a candidate ranked highly with specific titles, companies, projects, metrics, ownership, and semantic alignment. No hidden LLM inference is used during ranking.

Diagram suggestion: Candidate row -> evidence features -> semantic score -> final score -> reason.

Visual suggestion: Annotated top-candidate explanation with highlighted evidence phrases.

## How Do You Avoid Keyword Stuffing?

Concise answer: Evidence from actual career history dominates skill-list claims, and semantic score is only 25% of the final score.

Judge-friendly wording: A candidate with many ranking/retrieval keywords in skills but weak production history still loses to candidates who shipped ranking, retrieval, evaluation, and production systems.

Diagram suggestion: Bar chart showing 75% evidence and 25% semantic.

Visual suggestion: Comparison between semantic-only and hybrid top ranks from `reports/hybrid_scoring_validation.md`.

## How Do You Handle Bad Data?

Concise answer: We use confidence-based anomaly handling: high confidence excludes, medium confidence penalizes, low confidence warns.

Judge-friendly wording: Impossible timelines are removed, suspicious metadata is penalized, and noisy-but-plausible records are retained with warnings.

Diagram suggestion: Three-lane anomaly decision flow.

Visual suggestion: Traffic-light table for high/medium/low confidence.

## How Fast And Reproducible Is It?

Concise answer: Full hybrid ranking runs in about 17 seconds, uses about 29 MB peak memory, is CPU-only, offline, and byte-deterministic.

Judge-friendly wording: The system is production-practical: no network calls, no GPU, no hosted model, and stable output across runs.

Diagram suggestion: Benchmark table.

Visual suggestion: PASS badges for runtime, memory, validator, determinism, offline.

## What Makes It Better Than A Rule Ranker?

Concise answer: Rules provide precision; semantic retrieval provides recall and paraphrase robustness.

Judge-friendly wording: Winning candidate discovery needs both. Evidence ranking prevents false positives, while semantic retrieval catches candidates who describe the same work with different language.

Diagram suggestion: Venn diagram: evidence precision + semantic recall = hybrid shortlist.

Visual suggestion: Three-column ranking comparison: evidence-only, semantic-only, hybrid.
