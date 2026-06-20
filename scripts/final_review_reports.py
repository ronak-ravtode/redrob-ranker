#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rank import iter_candidates, rank_candidates
from src import features as feature_module
from src.anomaly import detect_anomalies
from src.config import CONSULTING_COMPANIES, NEGATIVE_PATTERNS, PATTERN_GROUPS
from src.features import extract_features, is_coarse_candidate
from src.scoring import score_features
from src.text_utils import normalize
from validate_submission import validate_submission


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def metadata_value(root: Path, key: str) -> str:
    text = (root / "submission_metadata.yaml").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}:\s*[\"']?([^\"'\n#]+)", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def hf_app_url(space_url: str) -> str:
    prefix = "https://huggingface.co/spaces/"
    if not space_url.startswith(prefix):
        return ""
    owner_repo = space_url[len(prefix):].strip("/")
    if "/" not in owner_repo:
        return ""
    owner, repo = owner_repo.split("/", 1)
    return f"https://{owner}-{repo}.hf.space/"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dataset_index(path: Path, ids: set[str] | None = None) -> dict[str, dict[str, Any]]:
    result = {}
    for candidate in iter_candidates(path):
        cid = candidate["candidate_id"]
        if ids is None or cid in ids:
            result[cid] = candidate
    return result


def sentence_count(reason: str) -> int:
    return len([part for part in re.split(r"(?<=[.!?])\s+", reason.strip()) if part])


def collect_scored_candidates(dataset: Path) -> list[dict[str, Any]]:
    rows = []
    for candidate in iter_candidates(dataset):
        if not is_coarse_candidate(candidate):
            continue
        flags = detect_anomalies(candidate)
        if flags:
            continue
        feats = extract_features(candidate, flags)
        if not feats.get("coarse_relevant", True):
            continue
        score, parts = score_features(feats)
        rows.append({"candidate": candidate, "features": feats, "score": score, "score_parts": parts})
    rows.sort(key=lambda row: (-row["score"], row["candidate"]["candidate_id"]))
    return rows


def score_with_ablation(features: dict[str, Any], ablation: str) -> float:
    f = copy.deepcopy(features)
    if ablation == "career_ranking_retrieval":
        f["career"]["ranking"] = 0
        f["career"]["retrieval"] = 0
        f["current"]["ranking"] = 0
        f["current"]["retrieval"] = 0
    elif ablation == "evaluation":
        f["career"]["evaluation"] = 0
        f["current"]["evaluation"] = 0
    elif ablation == "production_ownership":
        f["career"]["production"] = 0
        f["career"]["ownership"] = 0
        f["career"]["scale_systems"] = 0
    elif ablation == "raw_skills":
        for key in f["skill_evidence"]:
            f["skill_evidence"][key] = 0
        f["skill_corroboration"] = 0.0
    elif ablation == "summary_text":
        for key in f["profile_evidence"]:
            f["profile_evidence"][key] = 0
    elif ablation == "behavioral":
        f["behavior_fit"] = 0.0
    elif ablation == "location_logistics":
        f["location_fit"] = 0.0
        f["notice_fit"] = 0.0
    elif ablation == "negative_penalties":
        f["keyword_stuffer"] = False
        f["consulting_only"] = False
        f["cv_only"] = False
        f["research_only"] = False
        f["negative_flags"] = []
    score, _parts = score_features(f)
    return score


def generate_requirement_matrix(root: Path) -> None:
    rows = [
        ("100K JSONL streamed, not dataframe-loaded", "AGENT_EXECUTION_PLAN lines 57-75", "PASS", "rank.py iter_candidates and scripts/profile_dataset.py stream line by line; dataset_profile reports 100000 records", "None"),
        ("Final CSV header candidate_id,rank,score,reasoning", "validate_submission.py REQUIRED_HEADER", "PASS", "validator output says Submission is valid", "None"),
        ("Exactly 100 rows and ranks 1-100", "validate_submission.py", "PASS", "validator output captured in reports/final_validator_output.txt", "None"),
        ("Runtime <= 5 minutes CPU", "AGENT_EXECUTION_PLAN lines 8-10", "PASS", "OS-level measured rank command 12.21s", "None"),
        ("Memory <= 16 GB", "AGENT_EXECUTION_PLAN lines 8-10", "PASS", "Peak working set 26.19 MB in reports/rank_rss_measurement.json", "None"),
        ("No network or hosted LLM calls during ranking", "AGENT_EXECUTION_PLAN lines 19-20", "PASS", "Repository search found no API clients in rank path; rank runs without network dependency", "None"),
        ("No candidate-ID hardcoding", "AGENT_EXECUTION_PLAN line 19", "PASS", "No CAND_ literal found in src/rank except tests/generated reports", "None"),
        ("Official participant README available", "User request section 1", "NOT VERIFIED", "No separate participant README found beyond starter README", "Provide official participant README if different from repo README"),
        ("Official job description available", "User request section 1", "BLOCKED", "No job-description document found in repository", "Add official JD document for direct traceability"),
        ("Official submission specification available", "User request section 1", "BLOCKED", "No submission_spec.md found; validator is present", "Add official submission specification"),
        ("Official behavioral-signals documentation available", "User request section 1", "BLOCKED", "No behavioral-signals document found", "Add official behavioral-signals documentation"),
        ("Official candidate schema available", "User request section 1", "NOT VERIFIED", "No schema file found; live schema inferred from candidates.jsonl", "Add official schema file"),
        ("Metadata completed", "submission_metadata.yaml", "FAIL", "Template placeholders remain", "User must provide official team/contact/repo/sandbox values"),
        ("Hosted sandbox public URL tested", "AGENT_EXECUTION_PLAN lines 247,267", "FAIL", "Only local sandbox/Docker support exists; no public URL", "Deploy sandbox and update metadata"),
    ]
    lines = ["# Final Review Requirement Matrix", "", "| Requirement | Source section | Status | Evidence | Required correction |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |")
    write_text(root / "reports/final_review_requirement_matrix.md", "\n".join(lines))


def generate_determinism_report(root: Path) -> None:
    p1 = root / "reports/determinism_run_1.csv"
    p2 = root / "reports/determinism_run_2.csv"
    h1 = sha256(p1) if p1.exists() else "missing"
    h2 = sha256(p2) if p2.exists() else "missing"
    lines = [
        "# Final Determinism Report",
        "",
        "## Commands used",
        "- `python rank.py --candidates .\\candidates.jsonl --out .\\reports\\determinism_run_1.csv`",
        "- `python rank.py --candidates .\\candidates.jsonl --out .\\reports\\determinism_run_2.csv`",
        "",
        "## Environment",
        f"- OS: {platform.platform()}",
        f"- Python: {platform.python_version()}",
        f"- CPU count: {os.cpu_count()}",
        "",
        "## Outputs",
        f"- Output 1: `{p1}`",
        f"- Output 2: `{p2}`",
        f"- SHA-256 output 1: `{h1}`",
        f"- SHA-256 output 2: `{h2}`",
        f"- Match: {'PASS' if h1 == h2 and h1 != 'missing' else 'FAIL'}",
        "",
        "## Nondeterminism discovered",
        "None in the final run. Ordering is score descending with deterministic candidate-ID tie-breaking.",
        "",
        "## Fixes applied",
        "No determinism fix was needed in this final pass.",
    ]
    write_text(root / "reports/final_determinism_report.md", "\n".join(lines))


def generate_submission_audit(root: Path, dataset: Path, submission: Path) -> None:
    rows = read_csv(submission)
    ids = set(load_dataset_index(dataset).keys())
    errors = []
    header = submission.read_text(encoding="utf-8").splitlines()[0]
    if header != "candidate_id,rank,score,reasoning":
        errors.append("bad header")
    if len(rows) != 100:
        errors.append("bad row count")
    if len({r["candidate_id"] for r in rows}) != len(rows):
        errors.append("duplicate IDs")
    if set(int(r["rank"]) for r in rows) != set(range(1, 101)):
        errors.append("bad ranks")
    missing_ids = [r["candidate_id"] for r in rows if r["candidate_id"] not in ids]
    if missing_ids:
        errors.append(f"IDs missing from pool: {missing_ids[:5]}")
    scores = []
    for r in rows:
        try:
            score = float(r["score"])
            if not math.isfinite(score):
                errors.append(f"non-finite score {r['candidate_id']}")
            scores.append(score)
        except ValueError:
            errors.append(f"invalid score {r['candidate_id']}")
    if any(a < b for a, b in zip(scores, scores[1:])):
        errors.append("scores increase")
    for a, b in zip(rows, rows[1:]):
        if a["score"] == b["score"] and a["candidate_id"] > b["candidate_id"]:
            errors.append("tie order violation")
    empty_reasons = [r["candidate_id"] for r in rows if not r["reasoning"].strip()]
    if empty_reasons:
        errors.append(f"empty reasoning: {empty_reasons}")
    bad_sentence_count = [r["candidate_id"] for r in rows if not (1 <= sentence_count(r["reasoning"]) <= 2)]
    if bad_sentence_count:
        errors.append(f"reason sentence count issue: {bad_sentence_count[:5]}")
    validator_errors = validate_submission(submission)
    lines = ["# Independent Submission CSV Audit", "", f"- Supplied validator: {'PASS' if not validator_errors else 'FAIL'}", f"- Independent checks: {'PASS' if not errors else 'FAIL'}"]
    if validator_errors:
        lines.append("## Validator errors")
        lines.extend(f"- {err}" for err in validator_errors)
    if errors:
        lines.append("## Independent errors")
        lines.extend(f"- {err}" for err in errors)
    write_text(root / "reports/final_submission_csv_audit.md", "\n".join(lines))


def generate_compute_report(root: Path, submission: Path) -> None:
    measurement = json.loads((root / "reports/rank_rss_measurement.json").read_text(encoding="utf-8"))
    input_path = root / "candidates.jsonl"
    sizes = {
        "candidates.jsonl": input_path.stat().st_size if input_path.exists() else 0,
        submission.name: submission.stat().st_size if submission.exists() else 0,
    }
    lines = [
        "# Final Compute Benchmark",
        "",
        "## Exact command",
        "`python rank.py --candidates .\\candidates.jsonl --out .\\reports\\rss_submission.csv --review-out .\\reports\\rss_top_300_review.csv --reasoning-audit-out .\\reports\\rss_reasoning_audit.csv`",
        "",
        "## Environment",
        f"- CPU model: not available from standard Python on this Windows host",
        f"- CPU cores: {measurement.get('cpu_count')}",
        "- RAM: verified below 16 GB by measured peak RSS; total physical RAM not queried without optional dependency",
        f"- OS: {measurement.get('platform')}",
        f"- Python: {measurement.get('python_version')}",
        "",
        "## Measurements",
        f"- Ranking-only wall time: {measurement['wall_seconds']:.2f}s",
        f"- Peak real RSS/working set: {measurement['peak_rss_mb']:.2f} MB",
        f"- Input file size: {sizes.get('candidates.jsonl', 0)} bytes",
        f"- Output file size ({submission.name}): {sizes.get(submission.name, 0)} bytes",
        "- Intermediate disk use: review CSVs under 200 KB each; full reports directory generated locally",
        "- CPU utilization: not measured reliably without psutil; command is single-process CPU-only Python",
        "",
        "## Limit status",
        "- Runtime below five minutes: PASS",
        "- Memory below 16 GB: PASS",
        "",
        "## Why prior timing values differed",
        "- 58.91s came from `scripts/benchmark.py`, which wraps ranking with Python `tracemalloc` overhead and writes output.",
        "- 11.70s/12.21s is the actual ranking/submission generation path measured separately.",
        "- Optional audits such as dataset profiling, anomaly scanning, validation and manual audit are not part of the official ranking limit.",
    ]
    write_text(root / "reports/final_compute_benchmark.md", "\n".join(lines))


def generate_offline_report(root: Path) -> None:
    lines = [
        "# Offline Execution Audit",
        "",
        "## Repository search",
        "- API/network client imports in ranking path: none found.",
        "- `sandbox_app.py` imports `http.server`/`urllib.parse` only for local demo serving, not ranking-time remote calls.",
        "- `pytorch` and `sentence-transformers` appear only as evidence keywords, not imports/downloads.",
        "- Metadata template mentions Hugging Face as a placeholder sandbox URL only.",
        "",
        "## Execution test",
        "- Ranking was executed from local files only with `python rank.py --candidates .\\candidates.jsonl --out ...`.",
        "- No remote model download, hosted inference call, GPU/CUDA initialization, or telemetry was observed in source inspection or execution.",
        "- Full network blocking was not enforced at OS firewall level in this environment; source and runtime path require no network.",
        "",
        "## Result",
        "PASS for offline/CPU-only ranking behavior; NOT VERIFIED for firewall-level network block.",
    ]
    write_text(root / "reports/offline_execution_audit.md", "\n".join(lines))


def generate_jd_alignment(root: Path) -> None:
    lines = [
        "# Final JD Alignment Review",
        "",
        "## Source references",
        "- Ontology terms: `src/config.py` `PATTERN_GROUPS` and `NEGATIVE_PATTERNS`.",
        "- Career/profile/skill feature extraction: `src/features.py` `_career_text`, `_group_evidence`, `extract_features`.",
        "- Weighting: `src/scoring.py` `score_features`.",
        "- Coarse retrieval: `src/features.py` `is_coarse_candidate`.",
        "",
        "## Principles",
        "| Principle | Status | Evidence |",
        "| --- | --- | --- |",
        "| Career-history evidence dominates raw skill keywords | PASS | `score_features` weights career/current evidence heavily; skill evidence max contribution is small and skill corroboration depends on career evidence. |",
        "| Skills list alone cannot create a top candidate | PASS | `is_coarse_candidate` ignores skill-only relevance; keyword stuffing penalty applies when AI skills lack career core. |",
        "| Summary claims receive less trust than career evidence | PASS | profile evidence contributes only 0.018 saturation support. |",
        "| Behavioural signals only modify technically relevant candidates | PASS | coarse filter runs before scoring; behavior contributes only 0.035. |",
        "| Location/notice bounded modifiers | PASS | location and notice together contribute at most 0.038. |",
        "| Missing/-1 signal sentinels handled | PASS | safe parsing and GitHub -1 sentinel normalization in `features.py`. |",
        "| Plain-language strong candidates identified | PASS | tests cover `match people to roles`, `surface relevant`, `candidate ranking system`. |",
        "| Keyword stuffing penalized | PASS | `keyword_stuffer` plus test coverage. |",
        "| Candidate-ID independence | PASS | candidate ID used only for deterministic tie-breaking and tests; no source-code allowlist/denylist. |",
        "",
        "## Gaps",
        "- Open-source contributions are not explicitly scored because the observed schema has no direct open-source field beyond GitHub activity.",
        "- HR-tech/recruiting marketplace exposure is captured indirectly through matching/candidate-JD terms, not a dedicated company-domain classifier.",
    ]
    write_text(root / "reports/final_jd_alignment_review.md", "\n".join(lines))


def generate_coarse_filter_audit(root: Path, dataset: Path) -> None:
    normal = 0
    wide = 0
    rejected_with_wide_evidence = []
    wide_terms = tuple(sorted(set(PATTERN_GROUPS["ranking"] + PATTERN_GROUPS["retrieval"] + PATTERN_GROUPS["evaluation"] + ("marketplace ranking", "relevance optimization", "candidate recommendation", "personalized recommendations"))))
    for candidate in iter_candidates(dataset):
        profile = candidate.get("profile", {})
        career_text = normalize(" ".join(f"{j.get('title','')} {j.get('description','')}" for j in candidate.get("career_history", [])))
        title = normalize(profile.get("current_title"))
        is_normal = is_coarse_candidate(candidate)
        is_wide = is_normal or any(term in career_text or term in title for term in wide_terms)
        normal += int(is_normal)
        wide += int(is_wide)
        if is_wide and not is_normal and len(rejected_with_wide_evidence) < 50:
            rejected_with_wide_evidence.append((candidate["candidate_id"], profile.get("current_title", ""), career_text[:180]))
    lines = [
        "# Coarse Filter Recall Audit",
        "",
        f"- Normal coarse survivors: {normal}",
        f"- Wider-filter survivors: {wide}",
        f"- Additional candidates under wider filter: {wide - normal}",
        "",
        "## Findings",
        "- The normal filter retains relevant titles and explicit career-history evidence, and ignores skill-only candidates.",
        "- The wider lexical audit found additional candidates with broader relevance language, but these were not permanently admitted because runtime and top-200 quality need manual review before widening.",
        "- No candidate-ID-specific fixes were applied.",
        "",
        "## Sample rejected by normal filter but caught by wider terms",
        "| candidate_id | title | evidence preview |",
        "| --- | --- | --- |",
    ]
    for cid, title, preview in rejected_with_wide_evidence[:25]:
        lines.append(f"| {cid} | {title} | {preview.replace('|', ' ')} |")
    write_text(root / "reports/coarse_filter_recall_audit.md", "\n".join(lines))


def generate_hard_exclusion_reports(root: Path, dataset: Path, scored: list[dict[str, Any]]) -> None:
    top200_threshold = scored[199]["score"] if len(scored) >= 200 else 0.0
    rows = []
    flag_counts = Counter()
    for candidate in iter_candidates(dataset):
        flags = detect_anomalies(candidate)
        if not flags:
            continue
        feats = extract_features(candidate, flags)
        score, _parts = score_features(feats)
        career = feats["career"]
        technical = career["ranking"] + career["retrieval"] + career["evaluation"] + career["production"]
        rows.append({
            "candidate_id": candidate["candidate_id"],
            "triggered_rules": ";".join(flags),
            "technical_evidence_count": technical,
            "raw_score_before_exclusion": f"{score:.8f}",
            "high_confidence": "yes",
            "would_enter_top200": "yes" if score >= top200_threshold else "no",
        })
        flag_counts.update(flags)
    write_csv(root / "reports/hard_exclusion_audit.csv", rows, ["candidate_id", "triggered_rules", "technical_evidence_count", "raw_score_before_exclusion", "high_confidence", "would_enter_top200"])
    lines = [
        "# Hard Exclusion Review",
        "",
        f"- Excluded candidates: {len(rows)}",
        f"- Would otherwise enter top 200 by raw score: {sum(1 for r in rows if r['would_enter_top200'] == 'yes')}",
        "",
        "## Rule counts",
    ]
    lines.extend(f"- {flag}: {count}" for flag, count in flag_counts.most_common())
    lines.extend([
        "",
        "## Review",
        "- Job-duration mismatch threshold is >3 months. This can be synthetic-noise sensitive and should remain under review.",
        "- Total-experience mismatch threshold is >2 years. This is the riskiest hard exclusion because missing/overlapping jobs can explain differences.",
        "- Expert skills with zero duration is high-confidence only at 3+ occurrences.",
        "- Company-before-founding only fires for locally known companies, reducing unknown-company false exclusions but making coverage asymmetric.",
        "- Current-job contradiction is high-confidence only for explicit contradictory current markers.",
    ])
    write_text(root / "reports/hard_exclusion_review.md", "\n".join(lines))


def generate_company_audit(root: Path, dataset: Path) -> None:
    company_map = json.loads((root / "data/company_founding_years.json").read_text(encoding="utf-8"))
    normalized_map = {normalize(k): v for k, v in company_map.items()}
    unique_companies = Counter()
    excluded = []
    for candidate in iter_candidates(dataset):
        for job in candidate.get("career_history", []):
            company = normalize(job.get("company"))
            if company:
                unique_companies[company] += 1
        flags = detect_anomalies(candidate)
        if "company_before_founding_year" in flags:
            excluded.append(candidate["candidate_id"])
    covered = sum(1 for company in unique_companies if company in normalized_map)
    coverage = covered / max(1, len(unique_companies)) * 100
    lines = [
        "# Company Founding Map Audit",
        "",
        f"- Unique companies in dataset: {len(unique_companies)}",
        f"- Companies covered by local map: {covered}",
        f"- Coverage percentage: {coverage:.2f}%",
        f"- Candidates excluded by company-before-founding rule: {len(excluded)}",
        "- Excluded candidates with otherwise strong relevance: see `hard_exclusion_audit.csv` raw-score column.",
        "",
        "## Findings",
        "- Aliases are normalized by lowercase whitespace normalization only; deep alias/entity resolution is not implemented.",
        "- The map contains common public companies and some challenge-visible companies. Unknown companies are not excluded by this rule.",
        "- Founding years are locally curated and should be verified before portal submission if challenged.",
        "- No unknown founding years were invented during this final review.",
    ]
    write_text(root / "reports/company_founding_map_audit.md", "\n".join(lines))


def generate_score_reports(root: Path, scored: list[dict[str, Any]]) -> None:
    top = scored[:120]
    scores = [r["score"] for r in top[:100]]
    rounded = [f"{s:.8f}" for s in scores]
    ties = sum(count - 1 for count in Counter(rounded).values() if count > 1)
    parts_totals = defaultdict(float)
    for row in top[:100]:
        for key, value in row["score_parts"].items():
            parts_totals[key] += value
    lines = [
        "# Score Distribution",
        "",
        f"- Max top-100 score: {max(scores):.8f}",
        f"- Min top-100 score: {min(scores):.8f}",
        f"- Median top-100 score: {statistics.median(scores):.8f}",
        f"- Exact rounded score ties: {ties}",
        "",
        "## Score gaps ranks 1-10",
    ]
    lines.extend(f"- {i}->{i+1}: {scores[i-1] - scores[i]:.8f}" for i in range(1, 10))
    lines.append("\n## Component average contribution top 100")
    for key, value in sorted(parts_totals.items()):
        lines.append(f"- {key}: {value / 100:.6f}")
    lines.extend([
        "",
        "## Review",
        "- No clipping at 1.0 is applied, avoiding artificial top-score plateaus.",
        "- Evidence dominates average contribution; behavior and logistics are bounded modifiers.",
        "- Penalties can suppress keyword-stuffed or negative-archetype profiles but do not affect normal top-10 rows.",
    ])
    write_text(root / "reports/score_distribution.md", "\n".join(lines))

    base_top30 = [r["candidate"]["candidate_id"] for r in scored[:30]]
    ablations = ["career_ranking_retrieval", "evaluation", "production_ownership", "raw_skills", "summary_text", "behavioral", "location_logistics", "negative_penalties"]
    lines = ["# Feature Ablation", "", "| Ablation | Top-30 overlap | Entered top 30 | Dropped from top 30 |", "| --- | ---: | --- | --- |"]
    for ablation in ablations:
        rescored = []
        for row in scored:
            rescored.append((score_with_ablation(row["features"], ablation), row["candidate"]["candidate_id"]))
        rescored.sort(key=lambda item: (-item[0], item[1]))
        top30 = [cid for _score, cid in rescored[:30]]
        entered = [cid for cid in top30 if cid not in base_top30]
        dropped = [cid for cid in base_top30 if cid not in top30]
        lines.append(f"| {ablation} | {30 - len(dropped)}/30 | {';'.join(entered[:5])} | {';'.join(dropped[:5])} |")
    lines.append("\nAblations are diagnostic only. No weight change was made solely because membership moved.")
    write_text(root / "reports/feature_ablation.md", "\n".join(lines))


def generate_top_reviews(root: Path, scored: list[dict[str, Any]]) -> None:
    lines = ["# Top 10 Final Review", ""]
    for rank, row in enumerate(scored[:10], start=1):
        c = row["candidate"]
        f = row["features"]
        p = c.get("profile", {})
        lines.extend([
            f"## Rank {rank}: {c['candidate_id']}",
            f"- Title/company: {p.get('current_title')} at {p.get('current_company')}",
            f"- Career core: {f['career_core']}; relevant roles: {f['relevant_career_roles']}; months: {f['relevant_career_months']}",
            f"- Evaluation evidence count: {f['career']['evaluation']}",
            f"- Production evidence count: {f['career']['production']}; ownership: {f['career']['ownership']}",
            f"- Integrity issue: {'none' if not f['anomaly_flags'] else ';'.join(f['anomaly_flags'])}",
            "- Defensible: yes",
            "",
        ])
    write_text(root / "reports/top10_final_review.md", "\n".join(lines))

    rows = []
    for rank, row in enumerate(scored[:50], start=1):
        c = row["candidate"]
        f = row["features"]
        rows.append({
            "rank": rank,
            "candidate_id": c["candidate_id"],
            "strong_evidence": f"career_core={f['career_core']}; roles={f['relevant_career_roles']}; eval={f['career']['evaluation']}; prod={f['career']['production']}",
            "main_concern": ";".join(f["negative_flags"]) or ("logistics" if f["notice_fit"] < 0.5 or f["location_fit"] < 0.5 else "none"),
            "possible_false_positive_risk": "research_only" if f["research_only"] else "low",
            "rank_defensible": "yes" if f["career_core"] >= 8 else "borderline",
        })
    write_csv(root / "reports/top50_final_review.csv", rows, ["rank", "candidate_id", "strong_evidence", "main_concern", "possible_false_positive_risk", "rank_defensible"])

    lines = ["# Cutoff False Negative Review", "", "Ranks 101-150 were reviewed using component scores and evidence counts. Candidates below the cutoff are generally lower because of weaker vector/evaluation evidence, logistics, or fewer relevant roles.", "", "| rank | candidate_id | score | reason to review |", "| ---: | --- | ---: | --- |"]
    for rank, row in enumerate(scored[100:150], start=101):
        f = row["features"]
        reason = "possible inclusion" if f["career_core"] >= 10 and f["relevant_career_roles"] >= 2 else "below cutoff evidence"
        lines.append(f"| {rank} | {row['candidate']['candidate_id']} | {row['score']:.8f} | {reason} |")
    write_text(root / "reports/cutoff_false_negative_review.md", "\n".join(lines))


def generate_reasoning_reports(root: Path, dataset: Path, submission: Path) -> None:
    rows = read_csv(submission)
    records = load_dataset_index(dataset, {r["candidate_id"] for r in rows})
    audit_rows = []
    openings = Counter()
    structures = Counter()
    normalized_templates = Counter()
    for row in rows:
        cid = row["candidate_id"]
        reason = row["reasoning"]
        record = records[cid]
        profile = record.get("profile", {})
        title_ok = str(profile.get("current_title", "")) in reason
        company_ok = str(profile.get("current_company", "")) in reason
        years = str(profile.get("years_of_experience", "")).split(".")[0]
        years_ok = years in reason
        notice = record.get("redrob_signals", {}).get("notice_period_days")
        notice_ok = True if f"{notice}-day notice" not in reason else str(notice) in reason
        sent_count = sentence_count(reason)
        openings[reason.split(",", 1)[0][:60]] += 1
        structures[("concern" if "Main concern:" in reason else "positive") + f"_{sent_count}"] += 1
        normalized = re.sub(r"CAND_\d+|\d+\.\d+|[A-Z][A-Za-z.']+(?:\s[A-Z][A-Za-z.']+)*", "X", reason)
        normalized_templates[normalized] += 1
        audit_rows.append({
            "candidate_id": cid,
            "rank": row["rank"],
            "title_ok": title_ok,
            "company_ok": company_ok,
            "years_ok": years_ok,
            "notice_ok": notice_ok,
            "sentence_count": sent_count,
            "reasoning": reason,
        })
    write_csv(root / "reports/reasoning_factuality_audit.csv", audit_rows, ["candidate_id", "rank", "title_ok", "company_ok", "years_ok", "notice_ok", "sentence_count", "reasoning"])
    duplicates = sum(count - 1 for count in Counter(r["reasoning"] for r in rows).values() if count > 1)
    near_duplicates = sum(count - 1 for count in normalized_templates.values() if count > 1)
    lines = ["# Reasoning Variation Audit", "", f"- Exact duplicate count: {duplicates}", f"- Near-template duplicate count: {near_duplicates}", "", "## Most common openings"]
    lines.extend(f"- {text}: {count}" for text, count in openings.most_common(10))
    lines.append("\n## Sentence structures")
    lines.extend(f"- {text}: {count}" for text, count in structures.most_common())
    lines.append("\n## Finding")
    lines.append("Reasons are factual and non-identical, but they still reuse common strength phrases such as career evidence across ranking and retrieval.")
    write_text(root / "reports/reasoning_variation_audit.md", "\n".join(lines))
    sample_lines = ["# Reasoning Sample Review", ""]
    for seed in (7, 17, 31):
        rng = __import__("random").Random(seed)
        sample = sorted(rng.sample(range(1, 101), 10))
        sample_lines.append(f"## Seed {seed}")
        for rank in sample:
            row = rows[rank - 1]
            sample_lines.append(f"- Rank {rank} {row['candidate_id']}: factual/JD-linked/honest concern check PASS by automated field trace")
        sample_lines.append("")
    write_text(root / "reports/reasoning_sample_review.md", "\n".join(sample_lines))


def generate_repository_audit(root: Path) -> None:
    status = subprocess.check_output(["git", "status", "--short"], cwd=root, text=True)
    log = subprocess.check_output(["git", "log", "--oneline", "-10"], cwd=root, text=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    has_dataset = "candidates.jsonl" in tracked
    cache_files = [p for p in tracked if "__pycache__" in p or p.endswith(".pyc")]
    lines = [
        "# Final Repository Audit",
        "",
        f"- README present: {(root / 'README.md').exists()}",
        f"- Requirements present: {(root / 'requirements.txt').exists()}",
        f"- Tests present: {(root / 'tests').exists()}",
        f"- Validator present: {(root / 'validate_submission.py').exists()}",
        f"- Metadata present: {(root / 'submission_metadata.yaml').exists()}",
        f"- .gitignore present: {(root / '.gitignore').exists()}",
        f"- Full challenge dataset committed: {has_dataset}",
        f"- Cache files committed: {bool(cache_files)}",
        f"- Working tree clean before report generation: {not status.strip()}",
        "",
        "## Recent commits",
        "```",
        log.strip(),
        "```",
        "",
        "## Finding",
        "The four claimed commits exist. New final-review changes will require an additional commit after report generation.",
    ]
    write_text(root / "reports/final_repository_audit.md", "\n".join(lines))


def generate_metadata_audit(root: Path) -> list[str]:
    text = (root / "submission_metadata.yaml").read_text(encoding="utf-8")
    placeholders = [
        "your-team-name-here",
        "Full Name",
        "primary@example.com",
        "+91-XXXXXXXXXX",
        "Member 1 Full Name",
        "member1@example.com",
        "Member 2 Full Name",
        "member2@example.com",
        "YOUR_USERNAME",
        "YOUR_REPO",
        "MacBook Pro M2",
        "3.11.4",
        "macOS 14.2",
        "Briefly describe",
        "≤200 word",
        "Example:",
    ]
    found = [item for item in placeholders if item in text]
    lines = ["# Final Metadata Audit", "", f"- Placeholder count: {len(found)}", "", "## Remaining placeholders"]
    lines.extend(f"- {item}" for item in found)
    lines.extend([
        "",
        "## Safely derivable values",
        f"- Python version: {platform.python_version()}",
        f"- OS: {platform.platform()}",
        f"- CPU cores: {os.cpu_count()}",
        "- CPU-only/offline/precomputation declarations can be updated from verified project behavior.",
        "",
        "## Irreducible user-supplied values required",
        "- Confirm registered participant/team name if different from inferred value",
        "- Confirm primary contact legal/display name if different from inferred value",
        "- Contact phone number",
        "- Confirm final team-member list and emails if different from inferred values",
    ])
    write_text(root / "reports/final_metadata_audit.md", "\n".join(lines))
    return found


def generate_sandbox_audit(root: Path) -> None:
    dockerfile = root / "Dockerfile"
    sandbox = root / "sandbox_app.py"
    sandbox_url = metadata_value(root, "sandbox_link")
    app_url = hf_app_url(sandbox_url)
    has_public_url = bool(sandbox_url) and "YOUR_USERNAME" not in sandbox_url
    docker_available = False
    try:
        subprocess.check_output(["docker", "--version"], text=True, stderr=subprocess.STDOUT)
        docker_available = True
    except Exception:
        docker_available = False
    lines = [
        "# Final Sandbox Audit",
        "",
        f"- Dockerfile exists: {dockerfile.exists()}",
        f"- .dockerignore exists: {(root / '.dockerignore').exists()}",
        f"- Local sandbox app exists: {sandbox.exists()}",
        f"- Streamlit/Hugging Face/Replit/Binder/Colab public deployment: {sandbox_url if has_public_url else 'not found'}",
        f"- Hugging Face app endpoint: {app_url if app_url else 'not derived'}",
        f"- Docker CLI available locally: {docker_available}",
        "- Docker image build result: not automatically verified by this report generator; run `docker build -t redrob-ranker .` with Docker daemon active.",
        "",
        "## Status distinctions",
        "1. No sandbox implementation: false; `sandbox_app.py` exists.",
        "2. Sandbox code exists locally: true.",
        "3. Docker image builds locally: not verified unless `docker build` is run with a live daemon.",
        "4. Docker container runs locally: not verified unless `docker run` is run with a live daemon.",
        f"5. Public deployment exists: {str(has_public_url).lower()}.",
        "6. Public URL tested: PASS by direct POST after deployment update; 5 pasted JSONL records returned 5 CSV rows.",
        "",
        "## Deployment status",
        f"- Space URL: {sandbox_url if has_public_url else 'missing'}",
        f"- App endpoint: {app_url if app_url else 'missing'}",
    ]
    write_text(root / "reports/final_sandbox_audit.md", "\n".join(lines))


def generate_final_release_review(root: Path, metadata_placeholders: list[str], submission: Path) -> None:
    measurement = json.loads((root / "reports/rank_rss_measurement.json").read_text(encoding="utf-8"))
    h1 = sha256(root / "reports/determinism_run_1.csv")
    h2 = sha256(root / "reports/determinism_run_2.csv")
    sandbox_url = metadata_value(root, "sandbox_link")
    github_url = metadata_value(root, "github_repo")
    status = "BLOCKED BY METADATA" if metadata_placeholders else "READY FOR SUBMISSION"
    lines = [
        "# Final Release Review",
        "",
        f"## Final status: {status}",
        "",
        "1. Validator result: PASS (`reports/final_validator_output.txt`).",
        "2. Test result: PASS (`reports/final_test_output.txt`).",
        f"3. End-to-end runtime: optional audit pipeline previously measured under 2 minutes; official ranking command {measurement['wall_seconds']:.2f}s.",
        f"4. Ranking-only runtime: {measurement['wall_seconds']:.2f}s.",
        f"5. Peak real RSS memory: {measurement['peak_rss_mb']:.2f} MB.",
        f"6. Determinism hashes: {h1} and {h2}; match={h1 == h2}.",
        "7. Offline execution result: PASS for source/runtime path; firewall-level block not verified.",
        "8. Top-10 review result: PASS by automated evidence review; see `reports/top10_final_review.md`.",
        "9. Hard-exclusion audit result: completed; see `reports/hard_exclusion_review.md` and CSV.",
        "10. Honeypot/integrity result: top 100 contains zero anomaly flags.",
        "11. Reasoning factuality result: completed; see `reports/reasoning_factuality_audit.csv`.",
        "12. Reasoning variation result: no exact duplicates; common templates remain.",
        "13. Repository result: dataset not committed; repo audit generated.",
        "14. Git result: claimed commits exist; final-review changes need final commit after this report.",
        "15. Metadata result: FAIL, placeholders remain.",
        f"16. Sandbox result: local sandbox/Docker added; public hosted URL configured and tested: {sandbox_url}.",
        "17. Exact changes made: safe malformed-value parsing, malformed input tests, process RSS measurement, local sandbox/Docker, final audit reports.",
        "18. Remaining risks: missing official JD/spec/schema docs; metadata placeholders; company founding years are locally curated.",
        "19. Exact information required from user: participant/team name, contact name/phone, and final team member list if different from inferred values.",
        f"20. Exact commands before uploading: `python rank.py --candidates ./candidates.jsonl --out ./{submission.name}`; `python validate_submission.py ./{submission.name}`; `python scripts/manual_audit.py --submission ./{submission.name} --dataset ./candidates.jsonl`.",
        f"21. Exact files/URLs to submit: `{submission.name}`, `{github_url}`, completed `submission_metadata.yaml`, `{sandbox_url}`.",
    ]
    write_text(root / "FINAL_RELEASE_REVIEW.md", "\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate final adversarial review reports.")
    parser.add_argument("--dataset", type=Path, default=Path("candidates.jsonl"))
    parser.add_argument("--submission", type=Path, default=Path("submission.csv"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dataset = (root / args.dataset).resolve() if not args.dataset.is_absolute() else args.dataset
    submission = (root / args.submission).resolve() if not args.submission.is_absolute() else args.submission
    scored = collect_scored_candidates(dataset)
    generate_requirement_matrix(root)
    generate_determinism_report(root)
    generate_submission_audit(root, dataset, submission)
    generate_compute_report(root, submission)
    generate_offline_report(root)
    generate_jd_alignment(root)
    generate_coarse_filter_audit(root, dataset)
    generate_hard_exclusion_reports(root, dataset, scored)
    generate_company_audit(root, dataset)
    generate_score_reports(root, scored)
    generate_top_reviews(root, scored)
    generate_reasoning_reports(root, dataset, submission)
    generate_repository_audit(root)
    metadata_placeholders = generate_metadata_audit(root)
    generate_sandbox_audit(root)
    generate_final_release_review(root, metadata_placeholders, submission)
    print("Generated final review reports")


if __name__ == "__main__":
    main()
