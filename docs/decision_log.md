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

## Runtime and memory impact
- Full-data benchmark: pending dataset path.
- Code-path impact: still streaming; no dataframe load introduced.
- Expected memory increase: modest, from extra per-candidate feature bookkeeping only.
- Local unittest suite: 13 tests passed in ~0.03s.
- Synthetic benchmark smoke: 100 valid + 1 anomalous candidate finished in ~0.05s with ~0.97 MB peak traced memory.
- Dataset-audit script smoke: profile and anomaly reports generated successfully on a 2-candidate sample.
