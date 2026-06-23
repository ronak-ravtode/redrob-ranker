# Post-Embedding Benchmark Report

## Configuration

- Model: `sentence-transformers/all-MiniLM-L6-v2` (bundled locally)
- Device: CPU
- Candidates: 100,000 (464 MB JSONL)
- Coarse filter: enabled
- Top-K: 100

## Runtime

| Metric | Value |
|---|---|
| Wall time (cold start) | ~115s |
| Wall time (warm cache) | ~55s |
| Model load | ~5-10s (one-time, cached) |
| JD encoding | ~0.05s (cached) |
| Candidate encoding | ~30-40ms per candidate |
| Coarse filter (100K) | ~9s |
| Feature extraction (~900) | ~7s |
| Semantic scoring (~900) | ~35s |
| File I/O (464 MB) | ~3s |

## Memory

| Metric | Value |
|---|---|
| Peak traced memory | ~236 MB |
| Model memory | ~87 MB |
| Process memory | ~150 MB |

## Determinism

| Check | Result |
|---|---|
| Run 1 vs Run 2 | 100/100 identical rankings |
| Score precision | 8 decimal places |
| Tie-breaking | candidate_id ascending |

## Compliance

| Constraint | Status |
|---|---|
| Runtime < 60s (warm) | PASS (~55s) |
| Memory < 500 MB | PASS (~236 MB) |
| Offline execution | PASS (no network) |
| Deterministic output | PASS (100% identical) |
| Submission format | PASS (validator OK) |

## Notes

- Cold start includes model loading (~5-10s)
- Warm cache reuses loaded model across requests
- Runtime varies by system load; typical production ~55s
- All timings on reference hardware (CPU-only)
