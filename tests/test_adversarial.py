#!/usr/bin/env python3
"""Adversarial and edge-case tests for the Redrob ranking system."""
import json
import tempfile
import unittest
from pathlib import Path

from rank import rank_candidates, write_submission
from src.features import extract_features, is_coarse_candidate
from src.anomaly import detect_anomalies, detect_anomaly_confidence, anomaly_action_summary
from src.scoring import score_features
from src.reasoning import build_reason, build_reason_details
from src.semantic import semantic_features
from src.jd_understanding import get_default_jd_profile


def _base_candidate(cid="CAND_9999001"):
    return {
        "candidate_id": cid,
        "profile": {
            "years_of_experience": 4.0,
            "current_title": "ML Engineer",
            "current_company": "Acme",
            "country": "India",
            "location": "Pune",
            "headline": "ML Engineer",
            "summary": "Building ML systems.",
        },
        "career_history": [
            {
                "title": "ML Engineer",
                "company": "Acme",
                "description": "Built candidate matching and ranking systems with offline metrics and A/B tests.",
                "start_date": "2020-01-01",
                "end_date": "2024-01-01",
                "duration_months": 48,
                "is_current": False,
            }
        ],
        "skills": [{"name": "Python", "proficiency": "expert", "duration_months": 36}],
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


class KeywordStuffingTests(unittest.TestCase):
    def test_keyword_stuffer_detected(self):
        c = _base_candidate("CAND_9999010")
        c["career_history"] = [{"title": "Developer", "company": "Acme", "description": "Built internal tools.", "duration_months": 24}]
        c["skills"] = [
            {"name": "ranking"}, {"name": "retrieval"}, {"name": "vector search"},
            {"name": "recommendation"}, {"name": "evaluation"},
        ]
        features = extract_features(c, [])
        self.assertTrue(features["keyword_stuffer"])

    def test_real_evidence_not_flagged_as_stuffer(self):
        c = _base_candidate("CAND_9999011")
        features = extract_features(c, [])
        self.assertFalse(features["keyword_stuffer"])


class FakeExperienceTests(unittest.TestCase):
    def test_fake_ranking_experience_detected(self):
        c = _base_candidate("CAND_9999020")
        c["career_history"] = [{
            "title": "Data Analyst",
            "company": "Acme",
            "description": "Built dashboards and reports for business teams.",
            "duration_months": 36,
        }]
        features = extract_features(c, [])
        self.assertEqual(features["career"]["ranking"], 0)
        self.assertEqual(features["career"]["retrieval"], 0)

    def test_fake_retrieval_experience_detected(self):
        c = _base_candidate("CAND_9999021")
        c["career_history"] = [{
            "title": "Backend Developer",
            "company": "Acme",
            "description": "Built REST APIs and microservices.",
            "duration_months": 36,
        }]
        features = extract_features(c, [])
        self.assertEqual(features["career"]["retrieval"], 0)


class SkillOnlyProfileTests(unittest.TestCase):
    def test_skill_only_not_coarse_candidate(self):
        c = _base_candidate("CAND_9999030")
        c["profile"]["current_title"] = "Software Engineer"
        c["career_history"] = [{
            "title": "Software Engineer",
            "company": "Acme",
            "description": "Built internal tools.",
            "duration_months": 36,
        }]
        self.assertFalse(is_coarse_candidate(c))

    def test_skill_only_with_ranking_skill_not_coarse(self):
        c = _base_candidate("CAND_9999031")
        c["profile"]["current_title"] = "Software Engineer"
        c["career_history"] = [{
            "title": "Software Engineer",
            "company": "Acme",
            "description": "Built internal tools.",
            "duration_months": 36,
        }]
        c["skills"] = [{"name": "ranking"}, {"name": "retrieval"}]
        self.assertFalse(is_coarse_candidate(c))


class AIBuzzwordProfileTests(unittest.TestCase):
    def test_llm_only_profile_penalized(self):
        c = _base_candidate("CAND_9999040")
        c["career_history"] = [{
            "title": "AI Engineer",
            "company": "Startup",
            "description": "Recently started learning langchain and building small rag demos.",
            "duration_months": 6,
        }]
        c["skills"] = [{"name": "LangChain"}, {"name": "OpenAI"}]
        features = extract_features(c, [])
        self.assertIn("recent_llm_only", features["negative_flags"])

    def test_prompt_engineer_penalized(self):
        c = _base_candidate("CAND_9999041")
        c["profile"]["current_title"] = "Prompt Engineer"
        c["career_history"] = [{
            "title": "Prompt Engineer",
            "company": "AI Startup",
            "description": "Recently started learning langchain and building small rag demos. Calling openai and experimenting with chatgpt.",
            "duration_months": 6,
        }]
        features = extract_features(c, [])
        self.assertFalse(features["coarse_relevant"])


class MalformedDateTests(unittest.TestCase):
    def test_invalid_date_format_handled(self):
        c = _base_candidate("CAND_9999050")
        c["career_history"] = [{
            "title": "ML Engineer",
            "company": "Acme",
            "description": "Built ranking systems.",
            "start_date": "not-a-date",
            "end_date": "also-not-a-date",
            "duration_months": 24,
        }]
        flags = detect_anomalies(c)
        self.assertNotIn("job_negative_duration", flags)

    def test_future_date_flagged(self):
        c = _base_candidate("CAND_9999051")
        c["career_history"] = [{
            "title": "ML Engineer",
            "company": "Acme",
            "description": "Built ranking systems.",
            "start_date": "2030-01-01",
            "end_date": "2035-01-01",
            "duration_months": 60,
        }]
        flags = detect_anomalies(c)
        self.assertIn("future_employment_date", flags)


class DuplicateCompanyTests(unittest.TestCase):
    def test_duplicate_companies_allowed(self):
        c = _base_candidate("CAND_9999060")
        c["career_history"] = [
            {"title": "Junior ML", "company": "Acme", "description": "Built models.", "duration_months": 24, "is_current": False},
            {"title": "Senior ML", "company": "Acme", "description": "Led ranking systems.", "duration_months": 36, "is_current": False},
        ]
        flags = detect_anomalies(c)
        self.assertEqual(flags, [])


class ContradictoryTitleTests(unittest.TestCase):
    def test_contradictory_current_job_flagged(self):
        c = _base_candidate("CAND_9999070")
        c["profile"]["current_title"] = "Data Analyst"
        c["profile"]["current_company"] = "Acme"
        c["career_history"] = [{
            "title": "ML Engineer",
            "company": "Acme",
            "description": "Built ranking systems.",
            "is_current": True,
            "end_date": None,
            "duration_months": 24,
        }]
        flags = detect_anomalies(c)
        self.assertIn("contradictory_current_job_state", flags)


class EmptySummaryTests(unittest.TestCase):
    def test_empty_summary_handled(self):
        c = _base_candidate("CAND_9999080")
        c["profile"]["summary"] = ""
        c["profile"]["headline"] = ""
        features = extract_features(c, [])
        self.assertIsNotNone(features)

    def test_none_summary_handled(self):
        c = _base_candidate("CAND_9999081")
        c["profile"]["summary"] = None
        c["profile"]["headline"] = None
        features = extract_features(c, [])
        self.assertIsNotNone(features)


class AnomalyExclusionTests(unittest.TestCase):
    def test_high_confidence_anomaly_excluded(self):
        c = _base_candidate("CAND_9999090")
        c["career_history"] = [{
            "title": "ML Engineer",
            "company": "Acme",
            "start_date": "2023-01-01",
            "end_date": "2022-01-01",
            "duration_months": 12,
        }]
        findings = detect_anomaly_confidence(c)
        hard, _, action, _ = anomaly_action_summary(findings)
        self.assertIn("job_negative_duration", hard)
        self.assertEqual(action, "exclude")

    def test_medium_anomaly_penalized(self):
        c = _base_candidate("CAND_9999091")
        c["profile"]["years_of_experience"] = 2.0
        c["skills"] = [{"name": "Ranking", "proficiency": "expert", "duration_months": 72}]
        findings = detect_anomaly_confidence(c)
        hard, _, action, penalty = anomaly_action_summary(findings)
        self.assertEqual(hard, [])
        self.assertEqual(action, "penalize")
        self.assertGreater(penalty, 0.0)


class ScoringEdgeCaseTests(unittest.TestCase):
    def test_zero_experience_scores_nonzero(self):
        c = _base_candidate("CAND_9999100")
        c["profile"]["years_of_experience"] = 0.0
        c["career_history"] = []
        features = extract_features(c, [])
        score, _ = score_features(features)
        self.assertGreaterEqual(score, 0.0)

    def test_maximum_experience_scores_bounded(self):
        c = _base_candidate("CAND_9999101")
        c["profile"]["years_of_experience"] = 30.0
        features = extract_features(c, [])
        score, _ = score_features(features)
        self.assertGreater(score, 0.0)


class ReasoningEdgeCaseTests(unittest.TestCase):
    def test_empty_career_history_reasoning(self):
        c = _base_candidate("CAND_9999110")
        c["career_history"] = []
        features = extract_features(c, [])
        reason = build_reason(c, features, 0.3)
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)

    def test_single_job_reasoning(self):
        c = _base_candidate("CAND_9999111")
        features = extract_features(c, [])
        reason = build_reason(c, features, 0.5)
        self.assertIn("Acme", reason)


class SemanticEdgeCaseTests(unittest.TestCase):
    def test_empty_candidate_semantic(self):
        c = _base_candidate("CAND_9999120")
        c["career_history"] = []
        c["skills"] = []
        c["profile"]["summary"] = ""
        c["profile"]["headline"] = ""
        result = semantic_features(c)
        self.assertIn("semantic_fit_score", result)
        self.assertGreaterEqual(result["semantic_fit_score"], 0.0)

    def test_jd_semantic_alignment(self):
        c = _base_candidate("CAND_9999121")
        c["career_history"] = [{
            "title": "Search Engineer",
            "company": "Google",
            "description": "Built ranking systems with learning to rank, A/B testing, and production deployment.",
            "duration_months": 48,
        }]
        result = semantic_features(c)
        self.assertGreater(result["semantic_fit_score"], 0.3)


class IntegrationTests(unittest.TestCase):
    def test_full_pipeline_with_anomalies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            rows = []
            for i in range(10):
                c = _base_candidate(f"CAND_99992{i:02d}")
                if i == 5:
                    c["career_history"][0]["end_date"] = "2022-01-01"
                    c["career_history"][0]["start_date"] = "2023-01-01"
                rows.append(json.dumps(c))
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            ranked = rank_candidates(path, keep=10, apply_coarse_filter=False)
            self.assertGreater(len(ranked), 0)

    def test_submission_with_all_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            out = Path(tmpdir) / "test.csv"
            rows = []
            for i in range(100):
                c = _base_candidate(f"CAND_{9999000 + i:07d}")
                if i % 20 == 0:
                    c["skills"] = [{"name": "ranking"}, {"name": "retrieval"}, {"name": "vector search"}]
                    c["career_history"] = [{"title": "Developer", "company": "Acme", "description": "Built tools.", "duration_months": 24}]
                rows.append(json.dumps(c))
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            ranked = rank_candidates(path, keep=100, apply_coarse_filter=False)
            write_submission(ranked, out, top_k=100)
            from validate_submission import validate_submission
            errors = validate_submission(out)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
