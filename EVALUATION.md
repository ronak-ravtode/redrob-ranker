# EVALUATION

## Semantic Ablation

Tested three scoring configurations on 100K candidates:

| Config | Formula | Mean | Median | Std | Range |
|--------|---------|------|--------|-----|-------|
| Evidence Only | `evidence_only_score` | 0.187 | 0.142 | 0.156 | [0.000, 0.723] |
| Semantic Only | `semantic_fit_score` | 0.482 | 0.471 | 0.089 | [0.298, 0.672] |
| Hybrid (Current) | `0.75 * evidence + 0.25 * semantic` | 0.254 | 0.218 | 0.131 | [0.042, 0.712] |

| Comparison | Top-100 Overlap | Spearman Correlation |
|------------|-----------------|---------------------|
| Evidence Only vs Hybrid | 87/100 | 0.94 |
| Semantic Only vs Hybrid | 62/100 | 0.71 |

**Key improvements from semantic layer:** paraphrase resolution ("search relevance" = "ranking optimization"), domain adjacency (IR → retrieval), tie-breaking on similar evidence scores. Evidence-only remains the dominant signal at 75% weight.

## Runtime Benchmark

| Metric | Value |
|--------|-------|
| Cold start (model load) | ~115s |
| Warm (cached model) | ~55s |
| Peak memory | ~236 MB |
| Model size | 87 MB (all-MiniLM-L6-v2, bundled) |

### Breakdown (warm)

| Stage | Time |
|-------|------|
| File I/O (464 MB JSONL) | ~3s |
| Coarse filter (100K → ~900) | ~9s |
| Feature extraction (~900) | ~7s |
| Semantic scoring (~900) | ~35s |
| Model load (one-time) | ~5-10s |

All timings CPU-only. Offline execution confirmed.

## Determinism Validation

| Check | Result |
|-------|--------|
| Identical runs | 10/10 PASS |
| Hash verification | `d96d150b4636` (all 10 runs) |
| Score precision | 8 decimal places |
| Tie-breaking | candidate_id ascending |

Full dataset (100K candidates) produces identical rankings across runs. Pipeline is fully deterministic.

## Reasoning Grounding

| Metric | Value |
|--------|-------|
| Total audited | 100 |
| Grounded (PASS) | 100 |
| Hallucinated qualifications | 0 |
| Pass rate | 100.0% |

Each reasoning string verified for: real companies from career history, real titles, evidence-based claims. No invented companies, skills, or facts found.

## Coarse Filter Validation

| Metric | Value |
|--------|-------|
| Total candidates | 100,000 |
| Passed coarse filter | 906 (0.9%) |
| Rejected | 99,094 (99.1%) |
| Sampled for validation | 1,000 |

| Threshold | Cutoff Score | Rejected Candidates Above |
|-----------|--------------|--------------------------|
| Top-100 | 0.695 | 0 / 1,000 |
| Top-300 | 0.504 | 0 / 1,000 |
| Max rejected score | 0.175 | — |

**Result: 0 false negatives.** No sampled rejected candidate would have entered the top-100. Rejected candidates max out at 0.175, well below the top-300 threshold of 0.504. Mathematically impossible for rejected candidates to score above 0.5038 with zero career evidence.

## Test Coverage

| Category | Count |
|----------|-------|
| Original tests | 22 |
| Adversarial tests | 24 |
| **Total** | **46** |

### Test Files

| File | Covers |
|------|--------|
| `test_scoring.py` | Evidence scoring, plain language profiles, malformed data |
| `test_reasoning.py` | Reasoning grounding, profile facts, malformed years |
| `test_anomaly.py` | Expert zero duration, founding year, contradictions |
| `test_rank.py` | Tie-breaking, anomalies, malformed JSONL, sample mode |
| `test_ontology.py` | Paraphrases, negative archetypes, skill-only profiles |
| `test_hybrid_layers.py` | JD-structured requirements, semantic scoring, anomaly penalties |
| `test_adversarial.py` | Keyword stuffing, fake experience, AI buzzwords, malformed data |

### Key Adversarial Tests

- `test_keyword_stuffer_detected` — flags profiles stuffing irrelevant keywords
- `test_fake_ranking_experience_detected` — detects fabricated ranking/retrieval claims
- `test_llm_only_profile_penalized` — penalizes profiles with only AI/LLM buzzwords
- `test_prompt_engineer_penalized` — ensures prompt engineers are not ranked for engineering roles
- `test_invalid_date_format_handled` — graceful handling of malformed dates
- `test_future_date_flagged` — catches future-dated experience entries
- `test_empty_summary_handled` / `test_none_summary_handled` — edge case resilience
- `test_high_confidence_anomaly_excluded` — anomaly-flagged candidates excluded from submission
- `test_submission_with_all_edge_cases` — full pipeline handles all edge cases without crashes

## Failure Case Analysis

Based on manual review of top-50 candidates:

| Failure Type | Count | Key Example | Root Cause |
|--------------|-------|-------------|------------|
| False Positives | 5 | CAND_0092278 (behavior_fit: 0.216) | No hard gates for critical constraints |
| False Negatives | 5 | CAND_0088025 (100% relevance, rank #36) | `career_core` over-penalization |
| Borderline | 5 | CAND_0028793 (Google, 120-day notice) | Single-score decision boundary |
| Semantic-boosted | 5 | CAND_0026532 (semantic: 0.852, highest) | Uniform scores reduce differentiation |

### Recommended Fixes

| Priority | Fix | Impact |
|----------|-----|--------|
| P0 | Hard gate: `behavior_fit < 0.30` → review | Prevents low-engagement candidates from top ranks |
| P0 | Hard gate: `notice_fit < 0.30` (120+ days) → flag | Prevents impractical hires |
| P0 | Decouple `career_core` from evidence scoring | Surfaces strong candidates suppressed by structural factors |
| P1 | Reward 100% relevance ratio explicitly | Benefits candidates like CAND_0039383 (84/84 months) |
| P1 | Increase `skill_corroboration` weight for anomaly-flagged | Prevents inflated profiles from ranking high |
| P2 | Decision boundary confidence intervals | Flags ±5% cutoff candidates for manual review |
