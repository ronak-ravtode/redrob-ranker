#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import heapq
import json
import time
from pathlib import Path
from typing import Any

from src.anomaly import anomaly_action_summary, detect_anomaly_confidence
from src.evaluation import evaluate_ranking
from src.features import extract_features, is_coarse_candidate
from src.jd_understanding import get_default_jd_profile
from src.reasoning import build_reason, build_reason_details
from src.scoring import score_features
from src.semantic import semantic_features
from src.text_utils import candidate_id_suffix


JD_PROFILE = get_default_jd_profile()


def iter_candidates(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc


def rank_candidates(path: Path, keep: int = 300, apply_coarse_filter: bool = True) -> list[dict[str, Any]]:
    heap: list[tuple[float, int, str, dict[str, Any]]] = []
    for candidate in iter_candidates(path):
        if apply_coarse_filter and not is_coarse_candidate(candidate):
            continue
        anomaly_findings = detect_anomaly_confidence(candidate)
        hard_flags, anomaly_confidence, anomaly_action, anomaly_penalty = anomaly_action_summary(anomaly_findings)
        if hard_flags:
            continue
        anomaly_flags = [f"{item['flag']}:{item['action']}" for item in anomaly_findings]
        features = extract_features(candidate, anomaly_flags)
        features["anomaly_confidence"] = anomaly_confidence
        features["anomaly_action"] = anomaly_action
        features["anomaly_penalty"] = anomaly_penalty
        if apply_coarse_filter and not features.get("coarse_relevant", True):
            continue
        features.update(semantic_features(candidate, JD_PROFILE))
        score, score_parts = score_features(features)
        cid = candidate["candidate_id"]
        suffix = candidate_id_suffix(cid)
        record = {
            "candidate": candidate,
            "features": features,
            "score": score,
            "score_parts": score_parts,
        }
        key = (score, -suffix, cid, record)
        if len(heap) < keep:
            heapq.heappush(heap, key)
        elif (score, -suffix, cid) > heap[0][:3]:
            heapq.heapreplace(heap, key)

    # Primary: descending score. Exact ties: candidate_id ascending.
    ranked = [item[3] for item in heap]
    ranked.sort(key=lambda row: (-row["score"], candidate_id_suffix(row["candidate"]["candidate_id"]), row["candidate"]["candidate_id"]))
    return ranked


def write_submission(rows: list[dict[str, Any]], out_path: Path, top_k: int = 100) -> None:
    selected = rows[:top_k]
    if len(selected) != top_k:
        raise ValueError(f"Need {top_k} candidates, found {len(selected)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate_id", "rank", "score", "reasoning"],
        )
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            candidate = row["candidate"]
            writer.writerow({
                "candidate_id": candidate["candidate_id"],
                "rank": index,
                "score": f"{row['score']:.8f}",
                "reasoning": build_reason(candidate, row["features"], row["score"]),
            })


def write_review(rows: list[dict[str, Any]], out_path: Path, limit: int = 300) -> None:
    selected = rows[:limit]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "rank",
                "score",
                "score_evidence_only",
                "semantic_fit_score",
                "score_evidence",
                "score_supporting",
                "score_fit",
                "score_behavior",
                "score_availability_penalty",
                "score_penalty",
                "career_core",
                "relevant_career_roles",
                "relevant_career_months",
                "total_career_months",
                "consulting_months",
                "product_months",
                "product_company_history",
                "title_trajectory",
                "job_stability",
                "skill_corroboration",
                "negative_flags",
                "anomaly_flags",
                "anomaly_confidence",
                "anomaly_action",
                "semantic_model",
                "semantic_top_concepts",
            ],
        )
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            features = row["features"]
            parts = row["score_parts"]
            candidate = row["candidate"]
            writer.writerow(
                {
                    "candidate_id": candidate["candidate_id"],
                    "rank": index,
                    "score": f"{row['score']:.8f}",
                    "score_evidence_only": f"{parts.get('evidence_only', row['score']):.8f}",
                    "semantic_fit_score": f"{parts.get('semantic', features.get('semantic_fit_score', 0.0)):.8f}",
                    "score_evidence": f"{parts['evidence']:.8f}",
                    "score_supporting": f"{parts['supporting']:.8f}",
                    "score_fit": f"{parts['fit']:.8f}",
                    "score_behavior": f"{parts['behavior']:.8f}",
                    "score_availability_penalty": f"{parts.get('availability_penalty', 0.0):.8f}",
                    "score_penalty": f"{parts['penalty']:.8f}",
                    "career_core": features.get("career_core", 0),
                    "relevant_career_roles": features.get("relevant_career_roles", 0),
                    "relevant_career_months": features.get("relevant_career_months", 0),
                    "total_career_months": features.get("total_career_months", 0),
                    "consulting_months": features.get("consulting_months", 0),
                    "product_months": features.get("product_months", 0),
                    "product_company_history": features.get("product_company_history", 0),
                    "title_trajectory": f"{features.get('title_trajectory', 0.0):.4f}",
                    "job_stability": f"{features.get('job_stability', 0.0):.4f}",
                    "skill_corroboration": f"{features.get('skill_corroboration', 0.0):.4f}",
                    "negative_flags": ";".join(features.get("negative_flags", [])),
                    "anomaly_flags": ";".join(features.get("anomaly_flags", [])),
                    "anomaly_confidence": f"{features.get('anomaly_confidence', 0.0):.2f}",
                    "anomaly_action": features.get("anomaly_action", "none"),
                    "semantic_model": features.get("semantic_model", "not_scored"),
                    "semantic_top_concepts": ";".join(features.get("semantic_top_concepts", [])),
                }
            )


def write_reasoning_audit(rows: list[dict[str, Any]], out_path: Path, limit: int = 300) -> None:
    selected = rows[:limit]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate_id", "rank", "reasoning", "strength_sources", "concern_sources"],
        )
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            candidate = row["candidate"]
            details = build_reason_details(candidate, row["features"], row["score"])
            writer.writerow(
                {
                    "candidate_id": candidate["candidate_id"],
                    "rank": index,
                    "reasoning": details["reason"],
                    "strength_sources": " | ".join(
                        ",".join(piece["sources"]) for piece in details["strengths"]
                    ),
                    "concern_sources": " | ".join(
                        ",".join(piece["sources"]) for piece in details["concerns"]
                    ),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank Redrob candidates deterministically.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--keep", type=int, default=300)
    parser.add_argument("--review-out", type=Path)
    parser.add_argument("--reasoning-audit-out", type=Path)
    parser.add_argument("--top-k", type=int, default=100)
    args = parser.parse_args()

    start = time.perf_counter()
    ranked = rank_candidates(args.candidates, keep=max(args.keep, args.top_k))
    write_submission(ranked, args.out, top_k=args.top_k)
    if args.review_out:
        write_review(ranked, args.review_out, limit=args.keep)
    if args.reasoning_audit_out:
        write_reasoning_audit(ranked, args.reasoning_audit_out, limit=args.keep)
    elapsed = time.perf_counter() - start

    # Self-evaluation: compute IR metrics on own ranking output.
    metrics = evaluate_ranking(ranked[:100])
    print(f"Wrote {args.out} in {elapsed:.2f}s")
    print(f"Self-evaluation: NDCG@10={metrics['NDCG@10']:.4f}  NDCG@50={metrics['NDCG@50']:.4f}  "
          f"MAP={metrics['MAP']:.4f}  P@10={metrics['P@10']:.4f}  "
          f"relevant={metrics['total_relevant']}/100  strong={metrics['total_strong']}/100")


if __name__ == "__main__":
    main()
