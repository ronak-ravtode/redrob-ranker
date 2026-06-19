#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.anomaly import detect_anomalies


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit high-confidence anomalies in streaming mode.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path("reports/anomaly_summary.csv"))
    args = parser.parse_args()

    counts = Counter()
    examples: dict[str, list[str]] = {}
    total = 0
    flagged_candidates: set[str] = set()

    with args.candidates.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            candidate = json.loads(line)
            flags = detect_anomalies(candidate)
            if not flags:
                continue
            flagged_candidates.add(candidate.get("candidate_id", ""))
            for flag in flags:
                counts[flag] += 1
                examples.setdefault(flag, [])
                if len(examples[flag]) < 5:
                    examples[flag].append(candidate.get("candidate_id", ""))

    out_rows = []
    union = len(flagged_candidates)
    for flag, count in counts.most_common():
        out_rows.append({"flag": flag, "count": count, "examples": ";".join(examples.get(flag, []))})
    out_rows.append({"flag": "high_confidence_union_flags", "count": union, "examples": ""})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["flag", "count", "examples"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Scanned {total} candidates; wrote {args.out}")


if __name__ == "__main__":
    main()
