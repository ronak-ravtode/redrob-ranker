# Decision Log

## Baseline snapshot
- Baseline reviewed from `team_demo.csv` and the starter implementation.
- Baseline strength: deterministic, streaming, already grounded in career history.
- Baseline gap: plain-language matching, honeypot detection, title trajectory, and richer reasoning were too thin.

## Current iteration
- Expanded the JD ontology to include more paraphrases for ranking, retrieval, evaluation, and production ownership.
- Added title-trajectory, job-stability, company-mix, and skill-corroboration features.
- Added hard exclusion for high-confidence anomalies before scoring.
- Added optional review and reasoning-audit exports.
- Local verification: `python -m unittest discover -s tests -p "test_*.py" -v` passed; `python -m compileall src scripts tests rank.py validate_submission.py` passed.
- Added `scripts/manual_audit.py` for one-command human sign-off checks.

## Runtime and memory impact
- Full-data end-to-end verification order passed sequentially: profile -> anomaly -> benchmark -> rank -> validate -> manual audit.
- Full-data benchmark wall time: 58.91s.
- Ranking step peak traced memory: 6.04 MB.
- Full verification step timings: profile 39.14s, anomaly 4.91s, rank 11.70s, validate 0.08s, manual audit 5.43s.
- Code-path impact: still streaming; no dataframe load introduced.
- Local unittest suite: 13 tests passed in ~0.03s.
- Dataset-audit script smoke: profile and anomaly reports generated successfully on a 2-candidate sample.
