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

Final submission repository for the Redrob Intelligent Candidate Discovery Challenge. The project ranks the supplied `candidates.jsonl` pool for the Senior AI Engineer role and produces the official top-100 CSV submission.

Final submission file:

```bash
Code_With_Errors.csv
```

## Problem Statement

The ranker must identify candidates with strong hands-on evidence for production AI engineering, search/ranking, retrieval, vector infrastructure, evaluation, and ownership. It must run deterministically on CPU, offline, without hosted inference or API calls, and it must produce explainable candidate-level reasoning.

## Architecture

The pipeline is implemented with the Python standard library.

```text
candidates.jsonl
  -> stream JSONL records
  -> coarse relevance filter
  -> high-confidence anomaly exclusion
  -> career/profile/skill feature extraction
  -> deterministic additive scoring
  -> stable rank ordering
  -> CSV reasoning generation
```

Important modules:

```text
rank.py              main ranking CLI and CSV writers
src/config.py        Senior AI Engineer ontology and negative patterns
src/features.py      career, skill, logistics and behavior feature extraction
src/scoring.py       deterministic additive score
src/anomaly.py       high-confidence impossible-profile exclusion
src/reasoning.py     grounded explanation generation
sandbox_app.py       small-sample hosted demo for reviewers
```

## Scoring Methodology

The score is a raw additive ranking score, not a probability. Scores are intentionally not clipped at 1.0 because clipping flattened strong candidates into ties.

The strongest positive signals are:

```text
career-history evidence for ranking, recommendation or matching
hands-on search/retrieval systems
vector infrastructure such as dense retrieval, FAISS/HNSW or embeddings
offline/online evaluation such as NDCG, MRR, recall@K or A/B testing
production ownership, rollout, monitoring, latency and scale evidence
relevant Senior/Lead/Staff ML or AI engineering trajectory
```

Supporting signals include skills, profile summaries, experience fit, location fit, notice period, platform behavior and recruiter engagement. Skill lists are never allowed to dominate career-history evidence.

Penalties are applied for keyword stuffing, consulting-only careers, CV/speech-only profiles, research-only profiles without production evidence, weak career-core evidence, and other negative archetypes.

## Anomaly Handling

`src/anomaly.py` hard-excludes high-confidence integrity anomalies before ranking. Examples include impossible job durations, future employment dates, company-before-founding-year cases, experience sum mismatches, contradictory current-job state, and multiple expert skills with zero duration.

The top 100 contains zero candidates flagged by these hard-exclusion rules.

## Reasoning

Each CSV row includes a concise explanation grounded in the same evidence used for scoring. Reasoning now references candidate-specific facts from career history, such as named ranking or retrieval systems, vector databases, evaluation metrics, scale, migration work, index/versioning ownership, and measurable production impact where present.

## Reproduce Final Submission

The challenge dataset must be present locally as `candidates.jsonl`. It is intentionally not committed.

```bash
python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv
python validate_submission.py ./Code_With_Errors.csv
python scripts/manual_audit.py --submission ./Code_With_Errors.csv --dataset ./candidates.jsonl
```

Optional review exports:

```bash
python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv --review-out ./reports/top_300_review.csv --reasoning-audit-out ./reports/reasoning_audit.csv
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests cover ontology matching, short-token boundary safety, anomaly exclusion, malformed JSONL handling, missing input handling, malformed/missing numeric signals, deterministic tie-breaking, sample sandbox behavior, reasoning generation, and scoring behavior.

## Runtime And Memory

Measured on the documented local Windows CPU environment:

```text
Ranking wall time: 17.68s
Peak process RSS/working set: 26.43 MB
Runtime limit: under 5 minutes
Memory limit: under 16 GB
```

See `reports/final_compute_benchmark.md` and `reports/rank_rss_measurement.json` for details.

## Hosted Sandbox

The Hugging Face Space is a small-sample demo, not the full-dataset runner.

```text
https://huggingface.co/spaces/ronak-ravtode/redrob-ranker
```

The app accepts up to 100 pasted JSONL candidate records and returns `sample_ranking.csv`. It disables the production coarse filter for samples so unrelated examples still return rows, although unrelated candidates can correctly score `0.00000000`.

Run locally:

```bash
python sandbox_app.py --host 127.0.0.1 --port 7860
```

Docker sandbox:

```bash
docker build -t redrob-ranker .
docker run --rm -p 7860:7860 redrob-ranker
```

## Offline Design

Ranking uses only local files and the Python standard library. No network access, hosted LLM, embedding API, vector service, database, or GPU inference is used during ranking.

## Limitations

Official JD/spec/schema files were not present in the repository, so the ontology is based on the challenge description available during development. Company founding years are locally curated and used only for high-confidence anomaly detection. Hidden-ground-truth ranking quality cannot be known before challenge results are released.

## AI Use

OpenCode / gpt-5.5 was used for implementation support, code review, tests, documentation, and release auditing. The ranker itself is deterministic, CPU-only and offline; it does not call any AI model or external service during ranking.
