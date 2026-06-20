# Final Compute Benchmark

## Exact command
`python rank.py --candidates .\candidates.jsonl --out .\Code_With_Errors.csv`

## Environment
- CPU model: not available from standard Python on this Windows host
- CPU cores: 12
- RAM: verified below 16 GB by measured peak RSS; total physical RAM not queried without optional dependency
- OS: Windows-11-10.0.26200-SP0
- Python: 3.14.3

## Measurements
- Ranking-only wall time: 15.78s
- Peak real RSS/working set: 26.33 MB
- Input file size: 487259903 bytes
- Output file size (Code_With_Errors.csv): 53187 bytes
- Intermediate disk use: review CSVs under 200 KB each; full reports directory generated locally
- CPU utilization: not measured reliably without psutil; command is single-process CPU-only Python

## Limit status
- Runtime below five minutes: PASS
- Memory below 16 GB: PASS

## Why prior timing values differed
- `scripts/benchmark.py` wraps ranking with Python `tracemalloc` overhead and is slower than the official command.
- The value above is the measured official reproduction path for the final CSV.
- Optional audits such as dataset profiling, anomaly scanning, validation and manual audit are not part of the official ranking limit.
