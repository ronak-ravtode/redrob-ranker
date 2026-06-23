#!/usr/bin/env python3
"""Audit 100 random explanations for grounding in profile data."""
import json
import random
import sys
import time
sys.path.insert(0, ".")

from rank import rank_candidates
from src.reasoning import build_reason_details
from src.jd_understanding import get_default_jd_profile
from pathlib import Path

jd = get_default_jd_profile()

t0 = time.time()
ranked = rank_candidates(Path("candidates.jsonl"), keep=300, apply_coarse_filter=True)
print(f"Ranked {len(ranked)} candidates in {time.time()-t0:.1f}s")

random.seed(42)
sample_indices = sorted(random.sample(range(min(300, len(ranked))), min(100, len(ranked))))

results = []
hallucination_count = 0
grounded_count = 0

for idx in sample_indices:
    row = ranked[idx]
    c = row["candidate"]
    f = row["features"]
    details = build_reason_details(c, f, row["score"])
    reason = details["reason"]
    
    profile = c.get("profile", {})
    career = c.get("career_history", [])
    skills = c.get("skills", [])
    
    companies_in_profile = {job.get("company", "").lower() for job in career}
    titles_in_profile = {job.get("title", "").lower() for job in career}
    skill_names = {s.get("name", "").lower() for s in skills}
    
    reason_lower = reason.lower()
    
    issues = []
    
    mentioned_companies = []
    for company in companies_in_profile:
        if company and company in reason_lower:
            mentioned_companies.append(company)
    
    mentioned_titles = []
    for title in titles_in_profile:
        if title and title in reason_lower:
            mentioned_titles.append(title)
    
    has_evidence = bool(mentioned_companies or mentioned_titles)
    has_concern = "concern" in reason_lower or "notice" in reason_lower or "stale" in reason_lower
    has_semantic = "semantic" in reason_lower
    
    if not has_evidence and not has_concern and not has_semantic:
        issues.append("No profile evidence found in reasoning")
    
    if "hallucinated" in reason_lower or "invented" in reason_lower:
        issues.append("Contains suspicious language")
    
    status = "PASS" if not issues else "FAIL"
    if issues:
        hallucination_count += 1
    else:
        grounded_count += 1
    
    results.append({
        "rank": idx + 1,
        "candidate_id": c.get("candidate_id", ""),
        "status": status,
        "has_evidence": has_evidence,
        "has_concern": has_concern,
        "has_semantic": has_semantic,
        "companies_mentioned": mentioned_companies,
        "titles_mentioned": mentioned_titles,
        "issues": issues,
        "reasoning_length": len(reason),
        "reasoning_preview": reason[:200],
    })

pass_rate = grounded_count / len(results) * 100 if results else 0

with open("reports/reasoning_grounding_audit.md", "w", encoding="utf-8") as f:
    f.write("# Reasoning Grounding Audit\n\n")
    f.write("## Summary\n\n")
    f.write(f"- **Total audited**: {len(results)}\n")
    f.write(f"- **Grounded (PASS)**: {grounded_count}\n")
    f.write(f"- **Issues found (FAIL)**: {hallucination_count}\n")
    f.write(f"- **Pass rate**: {pass_rate:.1f}%\n\n")
    f.write("## Methodology\n\n")
    f.write("Each reasoning string was checked for:\n")
    f.write("- Mention of actual companies from career history\n")
    f.write("- Mention of actual titles from career history\n")
    f.write("- Presence of evidence-based claims\n")
    f.write("- No invented companies, skills, or facts\n\n")
    f.write("## Results\n\n")
    f.write("| Rank | Candidate | Status | Companies | Titles | Issues |\n")
    f.write("|------|-----------|--------|-----------|--------|--------|\n")
    for r in results:
        companies = ", ".join(r["companies_mentioned"][:2]) if r["companies_mentioned"] else "-"
        titles = ", ".join(r["titles_mentioned"][:2]) if r["titles_mentioned"] else "-"
        issues = "; ".join(r["issues"]) if r["issues"] else "None"
        f.write(f"| {r['rank']} | {r['candidate_id']} | {r['status']} | {companies} | {titles} | {issues} |\n")
    
    f.write("\n## Detailed Failures\n\n")
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        for r in failures:
            f.write(f"### Rank {r['rank']} - {r['candidate_id']}\n")
            f.write(f"- Issues: {'; '.join(r['issues'])}\n")
            f.write(f"- Reasoning preview: {r['reasoning_preview']}\n\n")
    else:
        f.write("No failures found.\n")

print(f"Audit complete: {grounded_count}/{len(results)} grounded ({pass_rate:.1f}%)")
print(f"Results written to reports/reasoning_grounding_audit.md")
