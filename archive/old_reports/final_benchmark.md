# Final Benchmark

## Commands

- Official ranking: `python rank.py --candidates .\candidates.jsonl --out .\Code_With_Errors.csv --review-out .\reports\top_300_review.csv --reasoning-audit-out .\reports\reasoning_audit.csv`
- Validator: `python validate_submission.py .\Code_With_Errors.csv`
- Process memory: `python scripts\measure_process.py --out .\reports\rank_rss_measurement.json python rank.py --candidates .\candidates.jsonl --out .\reports\determinism_run_1.csv`
- Determinism: second full run compared with `fc.exe`; no differences encountered.

## Results

| metric | result | target | status |
| --- | ---: | ---: | --- |
| full hybrid ranking wall time | 16.66s | < 60s | pass |
| measured process wall time | 17.00s | < 60s | pass |
| peak process RSS/working set | 29.27 MB | < 500 MB | pass |
| traced memory benchmark | 6.12 MB | < 500 MB | pass |
| validator | passed | pass | pass |
| deterministic output | byte-identical | required | pass |

## Semantic Retrieval Overhead

- Prior evidence-only release measurement: about 15.78s and 26.33 MB.
- Hybrid measured process run: 17.00s and 29.27 MB.
- Approximate overhead: 1.22s and 2.94 MB on this machine.
- The default semantic layer uses deterministic local embeddings, so overhead is mostly tokenization and vector math.

## Notes

- `scripts/benchmark.py` uses `tracemalloc`, which slows wall time to 38.26s; this is an instrumentation artifact, not the official ranking path.
- Optional local transformer mode is available but not enabled in this benchmark because local model weights are not committed to the repository.
