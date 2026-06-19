#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
import tracemalloc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rank import rank_candidates, write_submission


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the streaming ranker.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path("submission.csv"))
    parser.add_argument("--keep", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=100)
    args = parser.parse_args()

    tracemalloc.start()
    start = time.perf_counter()
    ranked = rank_candidates(args.candidates, keep=max(args.keep, args.top_k))
    write_submission(ranked, args.out, top_k=args.top_k)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Wrote {args.out}")
    print(f"Wall seconds: {elapsed:.2f}")
    print(f"Peak traced memory MB: {peak / (1024 * 1024):.2f}")


if __name__ == "__main__":
    main()
