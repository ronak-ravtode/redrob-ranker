---
title: Redrob Ranker
emoji: 🔎
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Redrob Intelligent Candidate Ranker

Redrob Intelligent Candidate Discovery Challenge submission. Ranks 100K candidates for Senior AI Engineer role, outputs top 100 with candidate-specific reasoning.

**Team**: Code With Errors  
**Submission**: `Code_With_Errors.csv`

## Architecture

```
candidates.jsonl (100K)
        │
        ▼
┌──────────────────┐
│  JD Understanding │  Senior AI Engineer ontology
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Coarse Filter    │  Regex skip → ~5K candidates
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Anomaly Detect   │  Hard-exclude frauds, penalize anomalies
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Feature Extract  │  Career evidence + 23 behavioral signals
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Semantic Score   │  MiniLM-L6-v2 or deterministic fallback
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Hybrid Score     │  0.75 × evidence + 0.25 × semantic
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Reasoning Gen    │  Evidence-grounded, candidate-specific
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  CSV Output       │  100 rows, ranks 1-100
└──────────────────┘
```

## Quick Start

```bash
pip install -r requirements.txt
make rank       # Produces Code_With_Errors.csv
make validate   # Check format
make test       # Run 46 tests
```

## Scoring

```
final_score = 0.75 × evidence_only + 0.25 × semantic
```

**Evidence signals** (68%): Career-history descriptions for ranking, retrieval, evaluation, production ownership, vector infrastructure.

**Supporting signals** (9%): Skills with duration, profile summaries, skill corroboration.

**Fit signals** (18%): Experience years, location, notice period, salary, education tier, company size, industry.

**Behavioral signals** (8.5%): 23 Redrob platform signals (recency, response rate, interview completion, GitHub activity, etc.).

**Penalties**: Keyword stuffing (-0.34), consulting-only (-0.16), CV-only (-0.22), research-only (-0.18), inactive candidates (-0.20).

## Modules

| Module | Purpose |
|--------|---------|
| `rank.py` | Main CLI, CSV writers, self-evaluation |
| `src/features.py` | Career, skill, behavior, location extraction |
| `src/scoring.py` | Weighted score computation |
| `src/reasoning.py` | Candidate-specific explanations |
| `src/anomaly.py` | Fraud detection and penalty |
| `src/semantic.py` | Transformer semantic scoring |
| `src/config.py` | JD ontology and patterns |
| `src/evaluation.py` | NDCG@10, MAP, P@10 metrics |
| `validate_submission.py` | CSV format validator |
| `sandbox_app.py` | HuggingFace demo |

## Tests

```bash
make test
```

46 tests covering: ontology matching, anomaly exclusion, malformed data, determinism, reasoning quality, scoring edge cases.

## Runtime

- Wall time: ~70s on CPU
- Memory: <500 MB
- No GPU, no network, no API calls during ranking

## Sandbox

HuggingFace Space: https://huggingface.co/spaces/ronak-ravtode/redrob-ranker

Paste up to 100 JSONL candidate records, get ranked CSV back.

```bash
make sandbox        # Local demo on port 7860
make docker-build   # Build container
make docker-run     # Run container
```

## Documentation

- [Architecture](docs/architecture.md) — Pipeline design and scoring weights
- [Evaluation](docs/evaluation.md) — Metrics and known limitations
- [Judge Notes](docs/judge_notes.md) — Quick start and file map

## AI Use

OpenCode / gpt-5.5 used for implementation, code review, tests, and documentation. Ranking is deterministic, CPU-only, offline.
