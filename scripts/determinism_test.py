#!/usr/bin/env python3
"""Determinism stress test: run ranking 10 times and verify identical output."""
import hashlib
import json
import time
import sys
from pathlib import Path
sys.path.insert(0, ".")

from rank import rank_candidates

INPUT = Path("candidates.jsonl")
RUNS = 10
KEEP = 200

print(f"Running {RUNS} determinism tests on {INPUT} (top {KEEP})...\n")

hashes = []
durations = []
candidate_counts = []
all_rankings = []

for i in range(RUNS):
    t0 = time.time()
    ranked = rank_candidates(INPUT, keep=KEEP, apply_coarse_filter=True)
    elapsed = time.time() - t0
    durations.append(elapsed)
    candidate_counts.append(len(ranked))

    ranking_ids = [r["candidate"]["candidate_id"] for r in ranked]
    ranking_json = json.dumps(ranking_ids)
    h = hashlib.sha256(ranking_json.encode()).hexdigest()
    hashes.append(h)
    all_rankings.append(ranking_ids)
    print(f"  Run {i+1:2d}: {len(ranked):4d} candidates, {elapsed:6.1f}s, hash={h[:12]}")

print(f"\nDurations: min={min(durations):.1f}s, max={max(durations):.1f}s, avg={sum(durations)/len(durations):.1f}s")
print(f"Candidate counts: {candidate_counts}")

unique_hashes = set(hashes)
is_deterministic = len(unique_hashes) == 1

if is_deterministic:
    print(f"\nDETERMINISM: PASS — all {RUNS} runs produced identical output (hash={hashes[0][:12]})")
else:
    print(f"\nDETERMINISM: FAIL — {len(unique_hashes)} unique hashes found")
    for h in unique_hashes:
        indices = [i for i, x in enumerate(hashes) if x == h]
        print(f"  hash={h[:12]}: runs {[i+1 for i in indices]}")

# Also check ordering is stable (rank 1 = rank 1 every time)
first_ranking = all_rankings[0]
all_same = all(r == first_ranking for r in all_rankings)
print(f"ORDERING STABILITY: {'PASS' if all_same else 'FAIL'}")

# Write report
with open("reports/determinism_stress_test.md", "w", encoding="utf-8") as f:
    f.write("# Determinism Stress Test\n\n")
    f.write(f"## Summary\n\n")
    f.write(f"- **Runs**: {RUNS}\n")
    f.write(f"- **Candidates per run**: {KEEP}\n")
    f.write(f"- **Determinism**: {'PASS' if is_deterministic else 'FAIL'}\n")
    f.write(f"- **Ordering stability**: {'PASS' if all_same else 'FAIL'}\n\n")
    f.write(f"## Performance\n\n")
    f.write(f"| Run | Candidates | Duration | Hash |\n")
    f.write(f"|-----|-----------|----------|------|\n")
    for i in range(RUNS):
        f.write(f"| {i+1} | {candidate_counts[i]} | {durations[i]:.1f}s | {hashes[i][:12]} |\n")
    f.write(f"\n## Conclusion\n\n")
    if is_deterministic:
        f.write("All 10 runs produced identical ranking output. The pipeline is fully deterministic.\n")
    else:
        f.write("Non-deterministic behavior detected. Investigation required.\n")

print(f"\nReport written to reports/determinism_stress_test.md")
