# Architecture

## Pipeline Overview

```
candidates.jsonl (100K profiles)
       │
       ▼
┌─────────────────────┐
│  JD Understanding    │  Structured Senior AI Engineer ontology
│  (config.py)         │  Required: ranking, retrieval, evaluation, production
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Coarse Filter       │  Fast regex skip for obviously unrelated profiles
│  (features.py)       │  Reduces 100K → ~5K candidates
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Anomaly Detection   │  Hard-exclude integrity frauds
│  (anomaly.py)        │  Penalize medium-confidence anomalies
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Feature Extraction  │  Career evidence, skills, behavior, location
│  (features.py)       │  23 Redrob signals integrated
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Semantic Scoring    │  MiniLM-L6-v2 or deterministic fallback
│  (semantic.py)       │  Profile ↔ JD embedding similarity
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Hybrid Scoring      │  0.75 × evidence + 0.25 × semantic
│  (scoring.py)        │  Evidence-dominant, skill lists supporting only
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Reasoning Gen       │  Candidate-specific, evidence-grounded explanations
│  (reasoning.py)      │  No hallucination, rank-consistent
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  CSV Output          │  100 rows, ranks 1-100, scores non-increasing
│  (rank.py)           │  Filename: Code_With_Errors.csv
└─────────────────────┘
```

## Scoring Weights

| Component | Weight | Source |
|-----------|--------|--------|
| Career evidence (ranking, retrieval, evaluation) | ~62% | career_history descriptions |
| Supporting signals (skills, profile, corroboration) | ~9% | skills array + profile |
| Fit signals (experience, location, title, etc.) | ~18% | profile + redrob_signals |
| Behavioral signals | 8.5% | 23 Redrob platform signals |
| Semantic similarity | 25% of final | MiniLM-L6-v2 embeddings |
| Penalties | up to -0.94 | keyword stuffing, consulting-only, etc. |

Final score: `0.75 × evidence_only + 0.25 × semantic`

## Key Design Decisions

1. **Evidence-first**: Career-history descriptions are the dominant signal. Skill lists and summaries are supporting only.

2. **Coarse filter**: Fast regex pre-filter skips candidates without relevant titles OR career evidence. Keeps runtime under 70s on 100K pool.

3. **Anomaly handling**: Hard-exclude high-confidence frauds (impossible durations, future dates). Penalize medium-confidence anomalies (keyword stuffing, consulting-only).

4. **Availability gate**: Inactive candidates with low response rates get bounded penalties. Spray-and-pray detection via application volume.

5. **Deterministic**: No randomness, no network calls, no GPU. Same input always produces same output.
