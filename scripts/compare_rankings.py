#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare top-30 ranking changes between two CSV outputs.")
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path("reports/top_30_diff.md"))
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    before_rows = _load(args.before)[: args.limit]
    after_rows = _load(args.after)[: args.limit]

    before = {row["candidate_id"]: (idx + 1, row) for idx, row in enumerate(before_rows)}
    after = {row["candidate_id"]: (idx + 1, row) for idx, row in enumerate(after_rows)}

    all_ids = sorted(set(before) | set(after))
    lines = ["# Top-30 Ranking Diff", "", "| candidate_id | before_rank | after_rank | before_score | after_score |", "| --- | ---: | ---: | ---: | ---: |"]
    for cid in all_ids:
        b_rank, b_row = before.get(cid, ("-", {"score": ""}))
        a_rank, a_row = after.get(cid, ("-", {"score": ""}))
        lines.append(f"| {cid} | {b_rank} | {a_rank} | {b_row.get('score', '')} | {a_row.get('score', '')} |")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
