# Final Compute Benchmark

## Exact command
`python rank.py --candidates .\candidates.jsonl --out .\reports\rss_submission.csv --review-out .\reports\rss_top_300_review.csv --reasoning-audit-out .\reports\rss_reasoning_audit.csv`

## Environment
- CPU model: not available from standard Python on this Windows host
- CPU cores: 12
- RAM: verified below 16 GB by measured peak RSS; total physical RAM not queried without optional dependency
- OS: Windows-11-10.0.26200-SP0
- Python: 3.14.3

## Measurements
- Ranking-only wall time: 17.68s
- Peak real RSS/working set: 26.43 MB
- Input file size: 487259903 bytes
- Output file size (redrob_submission.csv): 26797 bytes
- Intermediate disk use: review CSVs under 200 KB each; full reports directory generated locally
- CPU utilization: not measured reliably without psutil; command is single-process CPU-only Python

## Limit status
- Runtime below five minutes: PASS
- Memory below 16 GB: PASS

## Why prior timing values differed
- 58.91s came from `scripts/benchmark.py`, which wraps ranking with Python `tracemalloc` overhead and writes output.
- 11.70s/12.21s is the actual ranking/submission generation path measured separately.
- Optional audits such as dataset profiling, anomaly scanning, validation and manual audit are not part of the official ranking limit.
