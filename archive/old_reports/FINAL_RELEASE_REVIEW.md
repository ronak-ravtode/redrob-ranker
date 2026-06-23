# Final Release Review

## Final status: READY FOR SUBMISSION

1. Validator result: PASS (`reports/final_validator_output.txt`).
2. Test result: PASS (`reports/final_test_output.txt`).
3. End-to-end runtime: optional audit pipeline previously measured under 2 minutes; official ranking command 15.78s.
4. Ranking-only runtime: 15.78s.
5. Peak real RSS memory: 26.33 MB.
6. Determinism hashes: c700832d7b68bcf7c3b9e125199e0566f05fd664330e038fbf10ad03fd1dd6b0 and c700832d7b68bcf7c3b9e125199e0566f05fd664330e038fbf10ad03fd1dd6b0; match=True.
7. Offline execution result: PASS for source/runtime path; firewall-level block not verified.
8. Top-10 review result: PASS by automated evidence review; see `reports/top10_final_review.md`.
9. Hard-exclusion audit result: completed; see `reports/hard_exclusion_review.md` and CSV.
10. Honeypot/integrity result: top 100 contains zero anomaly flags.
11. Reasoning factuality result: completed; see `reports/reasoning_factuality_audit.csv`.
12. Reasoning variation result: no exact duplicates; candidate-specific career evidence is included.
13. Repository result: dataset not committed; repo audit generated.
14. Git result: release history is present and final changes are ready to commit/push.
15. Metadata result: PASS, no placeholders remain.
16. Sandbox result: local sandbox/Docker added; public hosted URL configured and tested: https://huggingface.co/spaces/ronak-ravtode/redrob-ranker.
17. Exact changes made: safe malformed-value parsing, malformed input tests, process RSS measurement, local sandbox/Docker, final audit reports.
18. Remaining risks: missing official JD/spec/schema docs; company founding years are locally curated.
19. Exact information required from user: none unless portal team/contact/member values differ from `submission_metadata.yaml`.
20. Exact commands before uploading: `python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv`; `python validate_submission.py ./Code_With_Errors.csv`; `python scripts/manual_audit.py --submission ./Code_With_Errors.csv --dataset ./candidates.jsonl`.
21. Exact files/URLs to submit: `Code_With_Errors.csv`, `https://github.com/ronak-ravtode/redrob-ranker`, completed `submission_metadata.yaml`, `https://huggingface.co/spaces/ronak-ravtode/redrob-ranker`.
