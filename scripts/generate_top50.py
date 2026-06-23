#!/usr/bin/env python3
"""Generate top 50 review data for human evaluation."""
import json
import csv
import sys
import time
sys.path.insert(0, ".")

from rank import rank_candidates
from src.reasoning import build_reason, build_reason_details
from src.jd_understanding import get_default_jd_profile
from src.semantic import semantic_features

jd = get_default_jd_profile()

t0 = time.time()
ranked = rank_candidates(
    __import__("pathlib").Path("candidates.jsonl"),
    keep=300,
    apply_coarse_filter=True,
)
elapsed = time.time() - t0
print(f"Ranked {len(ranked)} candidates in {elapsed:.1f}s")

# Top 50 detailed review
top50 = ranked[:50]
rows = []
for i, row in enumerate(top50):
    c = row["candidate"]
    f = row["features"]
    parts = row["score_parts"]
    details = build_reason_details(c, f, row["score"])
    
    profile = c.get("profile", {})
    career = c.get("career_history", [])
    skills = c.get("skills", [])
    
    career_evidence = []
    for job in career:
        desc = job.get("description", "")
        title = job.get("title", "")
        company = job.get("company", "")
        career_evidence.append(f"{title} at {company}: {desc[:200]}")
    
    skill_names = [s.get("name", "") for s in skills]
    
    rows.append({
        "rank": i + 1,
        "candidate_id": c.get("candidate_id", ""),
        "score": row["score"],
        "evidence_only": parts.get("evidence_only", 0),
        "semantic_score": parts.get("semantic", 0),
        "semantic_model": f.get("semantic_model", ""),
        "current_title": profile.get("current_title", ""),
        "current_company": profile.get("current_company", ""),
        "years": profile.get("years_of_experience", 0),
        "location": profile.get("location", ""),
        "country": profile.get("country", ""),
        "career_core": f.get("career_core", 0),
        "relevant_roles": f.get("relevant_career_roles", 0),
        "relevant_months": f.get("relevant_career_months", 0),
        "total_months": f.get("total_career_months", 0),
        "title_relevant": f.get("title_relevant", False),
        "experience_fit": f.get("experience_fit", 0),
        "location_fit": f.get("location_fit", 0),
        "behavior_fit": f.get("behavior_fit", 0),
        "notice_fit": f.get("notice_fit", 0),
        "job_stability": f.get("job_stability", 0),
        "title_trajectory": f.get("title_trajectory", 0),
        "skill_corroboration": f.get("skill_corroboration", 0),
        "keyword_stuffer": f.get("keyword_stuffer", False),
        "consulting_only": f.get("consulting_only", False),
        "cv_only": f.get("cv_only", False),
        "research_only": f.get("research_only", False),
        "negative_flags": ";".join(f.get("negative_flags", [])),
        "anomaly_flags": ";".join(f.get("anomaly_flags", [])),
        "anomaly_action": f.get("anomaly_action", "none"),
        "top_concepts": ";".join(f.get("semantic_top_concepts", [])),
        "reasoning": details["reason"],
        "strengths": " | ".join(p["text"] for p in details["strengths"]),
        "concerns": " | ".join(p["text"] for p in details["concerns"]),
        "skills": ", ".join(skill_names[:10]),
        "career_summary": " | ".join(career_evidence[:3]),
    })

with open("reports/top50_review_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote top50_review_data.csv with {len(rows)} rows")

# Also output to JSON for easier processing
with open("reports/top50_review_data.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)
print("Wrote top50_review_data.json")
