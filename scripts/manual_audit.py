#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_submission import validate_submission


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_dataset(path: Path) -> dict[str, dict]:
    import json

    rows: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            rows[record["candidate_id"]] = record
    return rows


def _text(value: object) -> str:
    return str(value or "")


def _find_any_job(record: dict, field: str) -> str:
    for job in record.get("career_history", []):
        value = _text(job.get(field))
        if value:
            return value
    return ""


def _trace_sources(record: dict, sources: str) -> list[str]:
    problems: list[str] = []
    tokens = [token.strip() for token in sources.replace("|", ",").split(",") if token.strip()]
    for token in tokens:
        if token == "career_history.title" and not _find_any_job(record, "title"):
            problems.append(token)
        elif token == "career_history.description" and not _find_any_job(record, "description"):
            problems.append(token)
        elif token == "skills.name" and not any(_text(skill.get("name")) for skill in record.get("skills", [])):
            problems.append(token)
        elif token == "profile.current_title" and not _text(record.get("profile", {}).get("current_title")):
            problems.append(token)
        elif token == "profile.current_company" and not _text(record.get("profile", {}).get("current_company")):
            problems.append(token)
        elif token == "profile.country" and not _text(record.get("profile", {}).get("country")):
            problems.append(token)
        elif token == "profile.location" and not _text(record.get("profile", {}).get("location")):
            problems.append(token)
        elif token == "redrob_signals.notice_period_days" and record.get("redrob_signals", {}).get("notice_period_days") is None:
            problems.append(token)
        elif token == "redrob_signals.last_active_date" and not _text(record.get("redrob_signals", {}).get("last_active_date")):
            problems.append(token)
        elif token == "redrob_signals.willing_to_relocate" and record.get("redrob_signals", {}).get("willing_to_relocate") is None:
            problems.append(token)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a one-command manual audit of the final submission.")
    parser.add_argument("--submission", type=Path, default=Path("submission.csv"))
    parser.add_argument("--dataset", type=Path, default=Path("candidates.jsonl"))
    parser.add_argument("--top300-review", type=Path, default=Path("reports/top_300_review.csv"))
    parser.add_argument("--reasoning-audit", type=Path, default=Path("reports/reasoning_audit.csv"))
    parser.add_argument("--anomalies", type=Path, default=Path("reports/anomaly_summary.csv"))
    parser.add_argument("--dataset-profile", type=Path, default=Path("reports/dataset_profile.md"))
    parser.add_argument("--benchmark", type=Path, default=Path("reports/submission_benchmark.csv"))
    parser.add_argument("--top30-diff", type=Path, default=Path("reports/top_30_diff.md"))
    parser.add_argument("--sample-count", type=int, default=10)
    args = parser.parse_args()

    failures: list[str] = []

    if not args.submission.exists():
        failures.append(f"Missing submission: {args.submission}")
    else:
        errors = validate_submission(args.submission)
        if errors:
            failures.extend([f"validate_submission: {err}" for err in errors])

    submission_rows = _load_csv(args.submission) if args.submission.exists() else []
    if len(submission_rows) != 100:
        failures.append(f"submission row count is {len(submission_rows)}, expected 100")

    if submission_rows:
        ranks = [int(row["rank"]) for row in submission_rows]
        if ranks != list(range(1, 101)):
            failures.append("submission ranks are not exactly 1..100")
        scores = [float(row["score"]) for row in submission_rows]
        if any(a < b for a, b in zip(scores, scores[1:])):
            failures.append("submission scores increase somewhere")

    if not args.top300_review.exists():
        failures.append(f"Missing top-300 review: {args.top300_review}")
    else:
        review_rows = _load_csv(args.top300_review)
        top100 = review_rows[:100]
        flagged = [row["candidate_id"] for row in top100 if row.get("anomaly_flags", "").strip()]
        if flagged:
            failures.append(f"top 100 has anomaly flags: {', '.join(flagged[:5])}")
        top10 = top100[:10]
        for row in top10:
            if int(row["career_core"]) < 11:
                failures.append(f"top 10 weak career_core for {row['candidate_id']}")
            if int(row["relevant_career_roles"]) < 2:
                failures.append(f"top 10 weak relevant_career_roles for {row['candidate_id']}")
            if float(row["score_evidence"]) < 0.84:
                failures.append(f"top 10 weak score_evidence for {row['candidate_id']}")

    dataset = _load_dataset(args.dataset) if args.dataset.exists() else {}
    if not dataset:
        failures.append(f"Missing or unreadable dataset: {args.dataset}")

    if not args.reasoning_audit.exists():
        failures.append(f"Missing reasoning audit: {args.reasoning_audit}")
    elif dataset:
        reasoning_rows = _load_csv(args.reasoning_audit)
        rng = random.Random(7)
        sample_ranks = sorted(rng.sample(range(1, min(100, len(reasoning_rows)) + 1), min(args.sample_count, len(reasoning_rows))))
        for rank in sample_ranks:
            row = reasoning_rows[rank - 1]
            record = dataset.get(row["candidate_id"])
            if not record:
                failures.append(f"reasoning row {rank} candidate not found in dataset")
                continue
            title = _text(record.get("profile", {}).get("current_title"))
            company = _text(record.get("profile", {}).get("current_company"))
            years = _text(record.get("profile", {}).get("years_of_experience"))
            reason = row["reasoning"]
            if title and title not in reason:
                failures.append(f"reasoning rank {rank} missing title: {row['candidate_id']}")
            if company and company not in reason:
                failures.append(f"reasoning rank {rank} missing company: {row['candidate_id']}")
            if years and years.split(".")[0] not in reason:
                failures.append(f"reasoning rank {rank} missing years: {row['candidate_id']}")
            for col in ("strength_sources", "concern_sources"):
                problems = _trace_sources(record, row.get(col, ""))
                if problems:
                    failures.append(f"reasoning rank {rank} invalid {col}: {row['candidate_id']} -> {', '.join(problems)}")

    for path, label in [
        (args.anomalies, "anomaly summary"),
        (args.dataset_profile, "dataset profile"),
        (args.benchmark, "benchmark"),
        (args.top30_diff, "top-30 diff"),
    ]:
        if not path.exists():
            failures.append(f"Missing {label}: {path}")

    print("Manual audit summary")
    print(f"submission: {args.submission}")
    if args.benchmark.exists():
        for line in args.benchmark.read_text(encoding="utf-8").splitlines():
            if line.startswith("Wall seconds:") or line.startswith("Peak traced memory MB:"):
                print(line)
    if args.anomalies.exists():
        anomaly_rows = _load_csv(args.anomalies)
        print(f"high-confidence anomaly union: {next((row['count'] for row in anomaly_rows if row['flag'] == 'high_confidence_union_flags'), 'unknown')}")
    if submission_rows:
        print("top 10:")
        for row in submission_rows[:10]:
            print(f"  {row['rank']:>3} {row['candidate_id']} {row['score']} {row['reasoning']}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS")
    print("git log:")
    try:
        log = subprocess.check_output(["git", "log", "--oneline", "-2"], text=True, cwd=Path(__file__).resolve().parents[1])
        print(log.strip())
    except Exception as exc:  # pragma: no cover - best effort only
        print(f"git log unavailable: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
