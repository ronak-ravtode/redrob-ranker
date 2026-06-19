#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features import is_coarse_candidate
from src.text_utils import normalize


def _fingerprint(candidate: dict) -> str:
    profile = candidate.get("profile", {})
    career_bits = []
    for job in candidate.get("career_history", []):
        career_bits.append(f"{job.get('title', '')}::{job.get('description', '')}")
    summary_bits = [profile.get("headline", ""), profile.get("summary", ""), profile.get("current_title", "")]
    return normalize(" || ".join(career_bits + summary_bits))


def _bucket_years(value: object) -> str:
    try:
        years = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if years < 2:
        return "0-1.9"
    if years < 4:
        return "2-3.9"
    if years < 6:
        return "4-5.9"
    if years < 8:
        return "6-7.9"
    if years < 10:
        return "8-9.9"
    if years < 13:
        return "10-12.9"
    return "13+"


def _emit_table(counter: collections.Counter, limit: int = 20) -> str:
    lines = ["| item | count |", "| --- | ---: |"]
    for item, count in counter.most_common(limit):
        lines.append(f"| {item} | {count} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the candidate dataset using streaming counters.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path("reports/dataset_profile.md"))
    parser.add_argument("--top-archetypes", type=int, default=20)
    args = parser.parse_args()

    titles = collections.Counter()
    countries = collections.Counter()
    cities = collections.Counter()
    companies = collections.Counter()
    skills = collections.Counter()
    industries = collections.Counter()
    years_buckets = collections.Counter()
    archetypes = collections.Counter()
    summary_fingerprints = collections.Counter()

    count = 0
    open_to_work = 0
    willing_to_relocate = 0
    evidence_backed = 0
    missing_profile_fields = collections.Counter()
    missing_job_fields = collections.Counter()

    with args.candidates.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            count += 1
            profile = candidate.get("profile", {})
            signals = candidate.get("redrob_signals", {})

            title = profile.get("current_title")
            company = profile.get("current_company")
            country = profile.get("country")
            city = profile.get("location")
            industry = profile.get("industry")

            if title:
                titles[title] += 1
            else:
                missing_profile_fields["current_title"] += 1
            if company:
                companies[company] += 1
            else:
                missing_profile_fields["current_company"] += 1
            if country:
                countries[country] += 1
            else:
                missing_profile_fields["country"] += 1
            if city:
                cities[city] += 1
            else:
                missing_profile_fields["location"] += 1
            if industry:
                industries[industry] += 1

            years_buckets[_bucket_years(profile.get("years_of_experience"))] += 1
            skills.update(skill.get("name", "") for skill in candidate.get("skills", []) if skill.get("name"))

            if signals.get("open_to_work_flag"):
                open_to_work += 1
            if signals.get("willing_to_relocate"):
                willing_to_relocate += 1

            if is_coarse_candidate(candidate):
                evidence_backed += 1

            fingerprint = _fingerprint(candidate)
            archetypes[fingerprint] += 1

            summary = normalize(" ".join([profile.get("headline", ""), profile.get("summary", "")]))
            if summary:
                summary_fingerprints[summary] += 1

            if not candidate.get("career_history"):
                missing_profile_fields["career_history"] += 1
            if not candidate.get("skills"):
                missing_profile_fields["skills"] += 1
            for job in candidate.get("career_history", []):
                for field in ("title", "company", "description", "start_date", "duration_months"):
                    if not job.get(field):
                        missing_job_fields[field] += 1

    out = []
    out.append("# Dataset Profile")
    out.append("")
    out.append(f"- Candidate records: {count}")
    out.append(f"- Evidence-backed coarse candidates: {evidence_backed}")
    out.append(f"- Open-to-work: {open_to_work}")
    out.append(f"- Willing to relocate: {willing_to_relocate}")
    out.append("")
    out.append("## Top titles")
    out.append(_emit_table(titles))
    out.append("")
    out.append("## Top countries")
    out.append(_emit_table(countries))
    out.append("")
    out.append("## Top cities")
    out.append(_emit_table(cities))
    out.append("")
    out.append("## Top companies")
    out.append(_emit_table(companies))
    out.append("")
    out.append("## Top industries")
    out.append(_emit_table(industries))
    out.append("")
    out.append("## Top skills")
    out.append(_emit_table(skills, 30))
    out.append("")
    out.append("## Experience buckets")
    out.append(_emit_table(years_buckets, 20))
    out.append("")
    out.append("## Missing profile fields")
    out.append(_emit_table(missing_profile_fields, 20))
    out.append("")
    out.append("## Missing job fields")
    out.append(_emit_table(missing_job_fields, 20))
    out.append("")
    out.append(f"## Repeated archetypes (top {args.top_archetypes})")
    out.append("| fingerprint | count |")
    out.append("| --- | ---: |")
    for item, count_item in archetypes.most_common(args.top_archetypes):
        preview = item[:180] + ("..." if len(item) > 180 else "")
        out.append(f"| {preview} | {count_item} |")
    out.append("")
    out.append("## Repeated summaries")
    out.append("| summary | count |")
    out.append("| --- | ---: |")
    for item, count_item in summary_fingerprints.most_common(args.top_archetypes):
        preview = item[:180] + ("..." if len(item) > 180 else "")
        out.append(f"| {preview} | {count_item} |")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} for {count} candidates")


if __name__ == "__main__":
    main()
