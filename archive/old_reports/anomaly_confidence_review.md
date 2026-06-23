# Anomaly Confidence Review

## Policy

| confidence | action | examples |
| --- | --- | --- |
| high | hard exclusion | future job dates, negative duration, company before founding year, contradictory current job, large duration mismatch, multiple expert skills with zero duration |
| medium | ranking penalty | skill duration exceeds profile experience, many low-tenure expert skills, current company absent from career history |
| low | warning only | missing experience/history, thin skill-duration metadata |

## Implementation

- Legacy `detect_anomalies()` is preserved for compatibility and still returns hard-exclusion flags.
- New `detect_anomaly_confidence()` returns `flag`, `confidence`, `action`, and `evidence`.
- `rank.py` excludes high-confidence findings, applies a bounded penalty for medium-confidence findings, and keeps low-confidence findings for audit only.
- `reports/top_300_review.csv` now includes `anomaly_confidence` and `anomaly_action`.

## Observed Hybrid Output

- The top 300 review export shows the new metadata fields.
- Example: `CAND_0086022` is retained with `skill_duration_exceeds_profile_experience:penalize`, confidence `0.65`, and a bounded penalty. It is not hard-excluded because the issue is suspicious metadata, not an impossible profile.
- High-confidence anomalies remain excluded from the official top 100.
