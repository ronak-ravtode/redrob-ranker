# Hard Exclusion Review

- Excluded candidates: 107
- Would otherwise enter top 200 by raw score: 21

## Rule counts
- experience_sum_mismatch: 48
- company_before_founding_year: 39
- job_duration_mismatch: 35
- multiple_expert_skills_with_zero_duration: 21

## Review
- Job-duration mismatch threshold is >3 months. This can be synthetic-noise sensitive and should remain under review.
- Total-experience mismatch threshold is >2 years. This is the riskiest hard exclusion because missing/overlapping jobs can explain differences.
- Expert skills with zero duration is high-confidence only at 3+ occurrences.
- Company-before-founding only fires for locally known companies, reducing unknown-company false exclusions but making coverage asymmetric.
- Current-job contradiction is high-confidence only for explicit contradictory current markers.
