#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rank import rank_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    for index, row in enumerate(rank_candidates(args.candidates, keep=max(300, args.limit)), start=1):
        if index > args.limit:
            break
        candidate = row["candidate"]
        profile = candidate["profile"]
        print("=" * 100)
        print(index, candidate["candidate_id"], f"score={row['score']:.5f}")
        print(profile["current_title"], "at", profile["current_company"], profile["years_of_experience"], "years")
        print("location:", profile["location"], "| anomalies:", row["features"]["anomaly_flags"])
        print("parts:", json.dumps(row["score_parts"], indent=2))
        for job in candidate["career_history"]:
            print("-", job["title"], "@", job["company"], "::", job["description"])


if __name__ == "__main__":
    main()
