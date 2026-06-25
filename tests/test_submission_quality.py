import json
import tempfile
import unittest
from pathlib import Path

from rank import rank_candidates, write_submission
from src.features import extract_features
from src.reasoning import build_reason
from src.scoring import score_features
from validate_submission import validate_submission


def _candidate(cid: str, company: str = "Acme", active: str = "2026-05-15") -> dict:
    return {
        "candidate_id": cid,
        "profile": {
            "years_of_experience": 7.0,
            "current_title": "Search ML Engineer",
            "current_company": company,
            "country": "India",
            "location": "Pune",
            "headline": "Search ML Engineer",
            "summary": "Built ranking and retrieval systems for product search.",
        },
        "career_history": [
            {
                "title": "Search ML Engineer",
                "company": company,
                "description": "Owned production ranking, semantic retrieval, vector search, NDCG evaluation, A/B testing, Python services, and p95 latency improvements.",
                "start_date": "2020-01-01",
                "end_date": "2026-01-01",
                "duration_months": 72,
                "is_current": False,
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 72},
            {"name": "Vector Search", "proficiency": "advanced", "duration_months": 48},
        ],
        "redrob_signals": {
            "notice_period_days": 30,
            "last_active_date": active,
            "willing_to_relocate": True,
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.9,
            "avg_response_time_hours": 12,
            "interview_completion_rate": 0.9,
            "saved_by_recruiters_30d": 4,
            "github_activity_score": 80,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
            "offer_acceptance_rate": 0.8,
        },
    }


class SubmissionQualityTests(unittest.TestCase):
    def test_submission_scores_ids_and_ranks_are_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.jsonl"
            out = Path(tmpdir) / "quality.csv"
            rows = [_candidate(f"CAND_{index:07d}") for index in range(1, 111)]
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            ranked = rank_candidates(path, keep=100, apply_coarse_filter=False)
            write_submission(ranked, out, top_k=100)

            self.assertEqual(validate_submission(out), [])
            scores = [row["score"] for row in ranked[:100]]
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertEqual(len({row["candidate"]["candidate_id"] for row in ranked[:100]}), 100)

    def test_reasoning_is_factual_and_varied(self):
        reasons = []
        for index in range(1, 5):
            candidate = _candidate(f"CAND_000010{index}", company=f"Acme{index}")
            features = extract_features(candidate, [])
            reason = build_reason(candidate, features, 1.0)
            reasons.append(reason)
            self.assertIn(candidate["profile"]["current_title"], reason)
            self.assertIn(candidate["profile"]["current_company"], reason)
            self.assertNotIn("Unknown", reason)
            self.assertIn("Concern:", reason)

        self.assertGreaterEqual(len(set(reasons)), 3)

    def test_honeypot_profile_is_excluded_from_ranking(self):
        good = _candidate("CAND_0000201")
        honeypot = _candidate("CAND_0000202")
        honeypot["skills"] = [
            {"name": "Ranking", "proficiency": "expert", "duration_months": 0},
            {"name": "Retrieval", "proficiency": "expert", "duration_months": 0},
            {"name": "Evaluation", "proficiency": "expert", "duration_months": 0},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.jsonl"
            path.write_text(json.dumps(good) + "\n" + json.dumps(honeypot) + "\n", encoding="utf-8")
            ranked = rank_candidates(path, keep=10, apply_coarse_filter=False)

        self.assertEqual([row["candidate"]["candidate_id"] for row in ranked], ["CAND_0000201"])

    def test_consulting_only_and_inactivity_penalties(self):
        product = _candidate("CAND_0000301", company="Acme")
        consulting = _candidate("CAND_0000302", company="TCS")
        inactive = _candidate("CAND_0000303", company="Acme", active="2025-01-01")
        inactive["redrob_signals"].update({
            "open_to_work_flag": False,
            "recruiter_response_rate": 0.05,
            "github_activity_score": 0,
        })

        product_score, _ = score_features(extract_features(product, []))
        consulting_score, _ = score_features(extract_features(consulting, []))
        inactive_score, _ = score_features(extract_features(inactive, []))

        self.assertGreater(product_score, consulting_score + 0.20)
        self.assertGreater(product_score, inactive_score + 0.20)

    def test_ranking_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.jsonl"
            rows = [_candidate(f"CAND_{index:07d}") for index in range(400, 420)]
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            first = rank_candidates(path, keep=20, apply_coarse_filter=False)
            second = rank_candidates(path, keep=20, apply_coarse_filter=False)

        self.assertEqual(
            [(row["candidate"]["candidate_id"], row["score"]) for row in first],
            [(row["candidate"]["candidate_id"], row["score"]) for row in second],
        )


if __name__ == "__main__":
    unittest.main()
