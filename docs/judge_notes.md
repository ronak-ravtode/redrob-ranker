# Judge Notes

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run ranking (produces Code_With_Errors.csv)
python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv

# Validate format
python validate_submission.py Code_With_Errors.csv

# Check honeypot rate
python scripts/honeypot_check.py --submission Code_With_Errors.csv --dataset candidates.jsonl

# Run tests
python -m pytest tests/ -q
```

## What This System Does

Ranks 100K candidates for a Senior AI Engineer role. Outputs top 100 with candidate-specific reasoning.

## What Judges Should Look For

### Strengths

- **Evidence-first**: 68% of score comes from career-history evidence. Skill lists are supporting only.
- **23 behavioral signals**: All Redrob platform signals integrated (recency, response rate, interview completion, GitHub activity, etc.).
- **Anomaly handling**: High-confidence frauds excluded, medium-confidence penalized.
- **Reasoning quality**: Each explanation references actual career roles and specific concerns.
- **Deterministic**: Same input always produces same output. No randomness.
- **Offline**: No network calls, no GPU, no API during ranking. Runs in ~70s on CPU.

### Weaknesses

- **Synthetic data bias**: Career descriptions are boilerplate. System may overfit to keyword patterns in the training data.
- **No visual dashboard**: Pure CSV output. No interactive demo beyond the HuggingFace sandbox.
- **Static ontology**: Hardcoded for "Senior AI Engineer." Not easily adaptable to other roles.

## File Map

| File | Purpose |
|------|---------|
| `rank.py` | Main ranking CLI |
| `src/features.py` | Feature extraction (career, skills, behavior, location) |
| `src/scoring.py` | Score computation with weights and penalties |
| `src/reasoning.py` | Candidate-specific explanation generation |
| `src/anomaly.py` | Honeypot/fraud detection |
| `src/semantic.py` | Transformer-based semantic scoring |
| `src/config.py` | JD ontology and pattern groups |
| `src/evaluation.py` | Self-evaluation IR metrics |
| `validate_submission.py` | CSV format validator |
| `sandbox_app.py` | HuggingFace demo app |
| `scripts/honeypot_check.py` | Honeypot rate checker |

## Reproduction

```bash
python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv
```

Output: 100 rows, ranks 1-100, scores non-increasing, reasoning column with candidate-specific explanations.
