import json
import tempfile
import unittest
from pathlib import Path

from rank import rank_candidates, write_submission
from validate_submission import validate_submission


def _candidate(cid: str, skills: list[dict] | None = None) -> dict:
    return {
        "candidate_id": cid,
        "profile": {
            "years_of_experience": 7.0,
            "current_title": "Machine Learning Engineer",
            "current_company": "Acme",
            "country": "India",
            "location": "Pune",
        },
        "career_history": [
            {
                "title": "Machine Learning Engineer",
                "company": "Acme",
                "description": "Built candidate matching and ranking systems with offline metrics and A/B tests.",
                "start_date": "2020-01-01",
                "end_date": "2024-01-01",
                "duration_months": 48,
                "is_current": False,
            },
            {
                "title": "Engineer",
                "company": "Acme",
                "description": "Shipped production search and retrieval services.",
                "start_date": "2018-01-01",
                "end_date": "2020-01-01",
                "duration_months": 24,
                "is_current": False,
            },
        ],
        "skills": skills or [{"name": "Python", "proficiency": "expert", "duration_months": 36}],
        "redrob_signals": {
            "notice_period_days": 30,
            "last_active_date": "2026-05-15",
            "willing_to_relocate": True,
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.9,
            "avg_response_time_hours": 12,
            "interview_completion_rate": 0.9,
            "saved_by_recruiters_30d": 3,
            "github_activity_score": 50,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }


class RankPipelineTests(unittest.TestCase):
    def test_tie_break_uses_candidate_id_ascending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.jsonl"
            path.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        _candidate("CAND_0000002"),
                        _candidate("CAND_0000001"),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            ranked = rank_candidates(path, keep=10)
            self.assertEqual([row["candidate"]["candidate_id"] for row in ranked], ["CAND_0000001", "CAND_0000002"])

    def test_anomalies_are_excluded_from_submission(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.jsonl"
            out = Path(tmpdir) / "submission.csv"
            rows = [_candidate(f"CAND_{index:07d}") for index in range(1, 101)]
            rows.append(
                _candidate(
                    "CAND_0000101",
                    skills=[
                        {"name": "Ranking", "proficiency": "expert", "duration_months": 0},
                        {"name": "Retrieval", "proficiency": "expert", "duration_months": 0},
                        {"name": "Evaluation", "proficiency": "expert", "duration_months": 0},
                    ],
                )
            )
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            ranked = rank_candidates(path, keep=100)
            self.assertEqual(len(ranked), 100)
            write_submission(ranked, out, top_k=100)
            self.assertEqual(validate_submission(out), [])


if __name__ == "__main__":
    unittest.main()
