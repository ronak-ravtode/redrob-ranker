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
│  Hybrid Score     │  0.84 × evidence + 0.16 × semantic
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
make test       # Run 93 tests
```

## Scoring

```
final_score = 0.84 × evidence_only + 0.16 × semantic
```

**Evidence signals** (68%): Career-history descriptions for ranking, retrieval, evaluation, production ownership, vector infrastructure.

**Supporting signals** (9%): Skills with duration, profile summaries, skill corroboration.

**Fit signals** (18%): Experience years, location, notice period, salary, education tier/field, company size, industry, current-role relevance.

**Grounded evidence signals**: Quantified ranking/retrieval impact in career descriptions receives a small boost when tied to actual roles.

**Behavioral signals** (8.5%): 23 Redrob platform signals (recency, response rate, interview completion, GitHub activity, etc.).

**Penalties**: Keyword stuffing (-0.34), consulting-only (-0.30), CV-only (-0.22), research-only (-0.30), framework-only (-0.24), plus bounded availability and anomaly penalties.

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

93 tests (plus 30 subtests) covering: ontology matching, anomaly exclusion, malformed data, determinism, reasoning quality, scoring edge cases, and sandbox rendering.

## Measured Results

Full 100,000-candidate run on the declared environment (12 cores, 16 GB RAM, Python 3.14.3, no GPU, no network):

| Metric | Measured |
|--------|----------|
| Rank time | 92.01s / 92.12s (two consecutive runs) |
| Wall clock | 94.19s including process startup |
| Peak working set | 512.1 MB |
| Candidates ranked | 100,000 |
| Submission rows | 100 |
| Tests | 93 passing + 30 subtests |
| Validator | `Submission is valid.` |
| Honeypot rate in top 100 | 0.0% (107 flagged of 100,000 scanned) |
| Determinism | Byte-identical across runs (SHA256 `55e9fee8…`) |

Most of the 512 MB is interpreter plus numpy/sentence-transformers import overhead; the ranker itself keeps only a bounded top-K heap.

Output ordering is stable by construction: descending score, ties broken by ascending numeric candidate ID.

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
- [Evaluation](docs/evaluation.md) — Metrics, fairness, and known limitations
- [Judge Notes](docs/judge_notes.md) — Quick start and file map
- [Judge Q&A](docs/judge_qa.md) — Prepared answers for common questions

## AI Use

OpenCode / gpt-5.5 used for implementation, code review, tests, and documentation. Ranking is deterministic, CPU-only, offline.
