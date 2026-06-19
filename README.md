# Redrob Intelligent Candidate Ranker — Agent Starter

This repository is a deterministic, CPU-only baseline for the India Runs / Redrob Data & AI Challenge.
It is intentionally designed to be understandable, testable and easy for coding agents to improve.

## Core design

1. Stream the 100,000-candidate JSONL file; do not load it all into a dataframe.
2. Treat career-history evidence as the primary source of truth.
3. Use profile summaries and skill lists only as supporting signals.
4. Penalize keyword stuffing, consulting-only careers, research-only profiles and CV/speech-only fit.
5. Detect high-confidence impossible-profile patterns before ranking.
6. Use behavioral signals only as a bounded modifier.
7. Generate reasoning from the same matched features used for scoring.

## Run

```bash
python rank.py --candidates ./candidates.jsonl --out ./team_xxx.csv
python validate_submission.py ./team_xxx.csv
```

The standard-library baseline should finish far below the 5-minute CPU limit. On the supplied 100K pool,
JSON parsing alone takes only seconds on a normal laptop.

## Development commands

```bash
python scripts/profile_dataset.py --candidates ./candidates.jsonl
python scripts/audit_anomalies.py --candidates ./candidates.jsonl
python scripts/inspect_top.py --candidates ./candidates.jsonl --limit 50
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/benchmark.py --candidates ./candidates.jsonl --out ./submission.csv
python scripts/manual_audit.py --submission ./submission.csv --dataset ./candidates.jsonl
```

## Important

This is a starting point, not a guaranteed winning ranker. Agents must inspect the top 200, identify false
positives/negatives, tune the rules, add a company-founding-year honeypot check, benchmark, and preserve
real Git history showing those iterations.

The ranker also supports optional review exports:

```bash
python rank.py --candidates ./candidates.jsonl --out ./team_xxx.csv --review-out ./reports/top_300_review.csv --reasoning-audit-out ./reports/reasoning_audit.csv
```
