# Final Release Review

## Final status: BLOCKED BY METADATA

1. Validator result: PASS (`reports/final_validator_output.txt`).
2. Test result: PASS (`reports/final_test_output.txt`).
3. End-to-end runtime: optional audit pipeline previously measured under 2 minutes; official ranking command 17.68s.
4. Ranking-only runtime: 17.68s.
5. Peak real RSS memory: 26.43 MB.
6. Determinism hashes: 115952cd4b5e1d2396707271d8db8c565abd79027781b71baac71bf59caa2277 and 115952cd4b5e1d2396707271d8db8c565abd79027781b71baac71bf59caa2277; match=True.
7. Offline execution result: PASS for source/runtime path; firewall-level block not verified.
8. Top-10 review result: PASS by automated evidence review; see `reports/top10_final_review.md`.
9. Hard-exclusion audit result: completed; see `reports/hard_exclusion_review.md` and CSV.
10. Honeypot/integrity result: top 100 contains zero anomaly flags.
11. Reasoning factuality result: completed; see `reports/reasoning_factuality_audit.csv`.
12. Reasoning variation result: no exact duplicates; common templates remain.
13. Repository result: dataset not committed; repo audit generated.
14. Git result: claimed commits exist; final-review changes need final commit after this report.
15. Metadata result: FAIL, placeholders remain.
16. Sandbox result: local sandbox/Docker added; public hosted URL configured and tested: https://huggingface.co/spaces/ronak-ravtode/redrob-ranker.
17. Exact changes made: safe malformed-value parsing, malformed input tests, process RSS measurement, local sandbox/Docker, final audit reports.
18. Remaining risks: missing official JD/spec/schema docs; metadata placeholders; company founding years are locally curated.
19. Exact information required from user: participant/team name, contact name/phone, and final team member list if different from inferred values.
20. Exact commands before uploading: `python rank.py --candidates ./candidates.jsonl --out ./redrob_submission.csv`; `python validate_submission.py ./redrob_submission.csv`; `python scripts/manual_audit.py --submission ./redrob_submission.csv --dataset ./candidates.jsonl`.
21. Exact files/URLs to submit: `redrob_submission.csv`, `https://github.com/ronak-ravtode/redrob-ranker`, completed `submission_metadata.yaml`, `https://huggingface.co/spaces/ronak-ravtode/redrob-ranker`.
