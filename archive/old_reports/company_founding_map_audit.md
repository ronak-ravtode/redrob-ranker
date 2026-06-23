# Company Founding Map Audit

- Unique companies in dataset: 63
- Companies covered by local map: 37
- Coverage percentage: 58.73%
- Candidates excluded by company-before-founding rule: 39
- Excluded candidates with otherwise strong relevance: see `hard_exclusion_audit.csv` raw-score column.

## Findings
- Aliases are normalized by lowercase whitespace normalization only; deep alias/entity resolution is not implemented.
- The map contains common public companies and some challenge-visible companies. Unknown companies are not excluded by this rule.
- Founding years are locally curated and should be verified before portal submission if challenged.
- No unknown founding years were invented during this final review.
