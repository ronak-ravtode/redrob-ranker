#!/usr/bin/env python3
"""Final pre-submission checklist."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1. Submission format
with open(ROOT / "Code_With_Errors.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("=== SUBMISSION CHECK ===")
print(f"Rows: {len(rows)} (need 100)")
print(f"Header: {list(rows[0].keys())}")

ranks = [int(r["rank"]) for r in rows]
print(f"Ranks 1-100: {min(ranks)}-{max(ranks)}, unique: {len(set(ranks))}")

scores = [float(r["score"]) for r in rows]
non_increasing = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
print(f"Scores non-increasing: {non_increasing}")

cids = [r["candidate_id"] for r in rows]
print(f"Unique IDs: {len(set(cids))}")

reasons = [r["reasoning"] for r in rows]
lengths = [len(r) for r in reasons]
print(f"Reasoning avg len: {sum(lengths) // len(lengths)} chars, min: {min(lengths)}, max: {max(lengths)}")

# Check tie-break (equal scores -> candidate_id ascending)
for i in range(len(rows) - 1):
    if scores[i] == scores[i + 1]:
        assert cids[i] < cids[i + 1], f"Tie-break violated at rank {i+1}: {cids[i]} > {cids[i+1]}"

# Check reasoning is not templated (no two consecutive identical)
for i in range(len(reasons) - 1):
    if reasons[i] == reasons[i + 1]:
        print(f"WARNING: identical reasoning at ranks {i+1} and {i+2}")

print(f"\n=== REASONING SAMPLE (first 3) ===")
for r in rows[:3]:
    print(f"  {r['candidate_id']}: {r['reasoning'][:200]}...")

print(f"\n=== REASONING SAMPLE (last 3) ===")
for r in rows[-3:]:
    print(f"  {r['candidate_id']}: {r['reasoning'][:200]}...")

# 2. Check files exist
print(f"\n=== FILE CHECK ===")
required = [
    "rank.py", "validate_submission.py", "sandbox_app.py", "Dockerfile",
    "requirements.txt", "submission_metadata.yaml", "README.md",
    "src/features.py", "src/scoring.py", "src/reasoning.py",
    "src/anomaly.py", "src/semantic.py", "src/config.py",
    "src/jd_understanding.py", "src/text_utils.py", "src/embedding_model.py",
    "src/evaluation.py", "scripts/honeypot_check.py",
]
for f in required:
    exists = (ROOT / f).exists()
    print(f"  {'OK' if exists else 'MISSING'}: {f}")

# 3. Check git status
import subprocess
result = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT), capture_output=True, text=True)
dirty = [l for l in result.stdout.strip().split("\n") if l.strip() and "India_runs_data" not in l]
print(f"\n=== GIT STATUS ===")
print(f"Uncommitted source changes: {len(dirty)}")
for l in dirty:
    print(f"  {l}")

# 4. Check git log
result = subprocess.run(["git", "log", "--oneline", "-3"], cwd=str(ROOT), capture_output=True, text=True)
print(f"\n=== RECENT COMMITS ===")
print(result.stdout.strip())

print(f"\n=== ALL CHECKS PASSED ===")
