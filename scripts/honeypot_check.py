#!/usr/bin/env python3
"""Check honeypot rate in a submission CSV.

Loads the full dataset, detects honeypot candidates using the anomaly detector,
and checks whether any honeypots appear in the submission's top 100.

Usage:
    python scripts/honeypot_check.py --submission ./Code_With_Errors.csv --dataset ./candidates.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.anomaly import detect_anomalies


def main() -> None:
    parser = argparse.ArgumentParser(description="Check honeypot rate in submission top 100.")
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    args = parser.parse_args()

    # Load submission candidate IDs (top 100)
    submission_ids: list[str] = []
    with args.submission.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            submission_ids.append(row["candidate_id"])
    print(f"Loaded {len(submission_ids)} candidates from submission.")

    # Load all candidates and detect honeypots
    honeypot_ids: set[str] = set()
    total = 0
    with args.dataset.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            candidate = json.loads(line)
            flags = detect_anomalies(candidate)
            if flags:
                honeypot_ids.add(candidate["candidate_id"])

    print(f"Scanned {total} candidates; detected {len(honeypot_ids)} with high-confidence anomaly flags.")

    # Check overlap
    flagged_in_submission = [cid for cid in submission_ids if cid in honeypot_ids]
    rate = len(flagged_in_submission) / len(submission_ids) * 100 if submission_ids else 0

    if flagged_in_submission:
        print(f"\nWARNING: {len(flagged_in_submission)} honeypot candidate(s) in top {len(submission_ids)}:")
        for cid in flagged_in_submission:
            rank = submission_ids.index(cid) + 1
            print(f"  {cid} (rank {rank})")
        print(f"\nHoneypot rate: {rate:.1f}% (limit: 10%)")
        if rate > 10:
            print("FAIL: Honeypot rate exceeds 10% limit. Submission would be disqualified at Stage 3.")
            sys.exit(1)
        else:
            print("PASS: Rate within acceptable limits.")
    else:
        print(f"\nPASS: No honeypot candidates found in top {len(submission_ids)}.")
        print(f"Honeypot rate: {rate:.1f}%")


if __name__ == "__main__":
    main()
