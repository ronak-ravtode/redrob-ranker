# Scorecard

## Baseline
- Deterministic and streaming.
- Good at explicit ranking/search titles.
- Weak on plain-language evidence and honeypots.

## Current iteration
- Broader JD ontology.
- Hard exclusion for high-confidence anomalies.
- Added title trajectory, job stability, company mix, and skill corroboration.
- Added review and reasoning audit exports.

## Verification status
- Unit tests: passed locally with `python -m unittest discover -s tests -p "test_*.py" -v`.
- Full-data runtime: pending dataset path.
- Validator: pending final CSV generation.
