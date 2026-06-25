import unittest

from src.features import extract_features
from src.scoring import score_features


def base_features():
    zero = {
        "ranking": 0,
        "retrieval": 0,
        "vector_infra": 0,
        "evaluation": 0,
        "production": 0,
        "ownership": 0,
        "python": 0,
        "fine_tuning": 0,
        "scale_systems": 0,
    }
    return {
        "career": dict(zero),
        "current": dict(zero),
        "profile_evidence": dict(zero),
        "skill_evidence": dict(zero),
        "title_relevant": True,
        "relevant_career_roles": 1,
        "relevant_career_months": 48,
        "experience_fit": 1.0,
        "location_fit": 1.0,
        "notice_fit": 1.0,
        "behavior_fit": 0.8,
        "keyword_stuffer": False,
        "consulting_only": False,
        "cv_only": False,
        "research_only": False,
        "negative_flags": [],
        "career_core": 0,
        "anomaly_flags": [],
        "total_career_months": 48,
        "consulting_months": 0,
        "product_months": 48,
        "product_company_history": 1.0,
        "title_trajectory": 0.75,
        "job_stability": 0.9,
        "skill_corroboration": 0.0,
        "current_relevance_score": 0.0,
        "measured_impact_score": 0.0,
        "education_field_fit": 0.5,
    }


class ScoringTests(unittest.TestCase):
    def test_real_career_evidence_beats_skill_only(self):
        real = base_features()
        real["career"].update({"ranking": 4, "retrieval": 4, "evaluation": 3, "production": 3, "ownership": 4})
        real["career_core"] = 11
        real["skill_corroboration"] = 0.6

        stuffed = base_features()
        stuffed["skill_evidence"].update({"ranking": 4, "retrieval": 4, "vector_infra": 3})
        stuffed["keyword_stuffer"] = True
        stuffed["skill_corroboration"] = 0.0

        score_real, _ = score_features(real)
        score_stuffed, _ = score_features(stuffed)
        self.assertGreater(score_real, score_stuffed)

    def test_plain_language_career_is_not_suppressed(self):
        plain = base_features()
        plain["career"].update({"ranking": 2, "retrieval": 3, "evaluation": 2, "production": 2, "ownership": 2})
        plain["career_core"] = 7
        plain["skill_corroboration"] = 0.4

        keyword = base_features()
        keyword["skill_evidence"].update({"ranking": 5, "retrieval": 5, "vector_infra": 5})
        keyword["keyword_stuffer"] = True

        score_plain, _ = score_features(plain)
        score_keyword, _ = score_features(keyword)
        self.assertGreater(score_plain, score_keyword)

    def test_missing_and_malformed_signals_do_not_crash_features(self):
        candidate = {
            "candidate_id": "CAND_9999998",
            "profile": {
                "years_of_experience": None,
                "current_title": "Software Engineer",
                "current_company": "Acme",
                "country": "India",
                "location": "Pune",
            },
            "career_history": [
                {
                    "title": "Software Engineer",
                    "company": "Acme",
                    "description": "Built internal tools.",
                    "duration_months": None,
                }
            ],
            "skills": [],
            "redrob_signals": {
                "notice_period_days": None,
                "recruiter_response_rate": None,
                "avg_response_time_hours": None,
                "interview_completion_rate": None,
                "saved_by_recruiters_30d": None,
                "github_activity_score": -1,
            },
        }
        features = extract_features(candidate, [])
        self.assertEqual(features["years"], 0.0)
        self.assertGreaterEqual(features["behavior_fit"], 0.0)
        self.assertGreaterEqual(features["notice_fit"], 0.0)

    def test_grounded_recruiter_signals_lift_score(self):
        baseline = base_features()
        baseline["career"].update({"ranking": 2, "retrieval": 2, "evaluation": 1})
        baseline["career_core"] = 5

        enhanced = dict(baseline)
        enhanced["career"] = dict(baseline["career"])
        enhanced.update({
            "current_relevance_score": 1.0,
            "measured_impact_score": 1.0,
            "education_field_fit": 1.0,
        })

        score_baseline, _ = score_features(baseline)
        score_enhanced, parts = score_features(enhanced)
        self.assertGreater(score_enhanced, score_baseline)
        self.assertGreater(parts["supporting"], 0.0)

    def test_extracts_new_signals_from_existing_fields(self):
        candidate = {
            "candidate_id": "CAND_9999997",
            "profile": {
                "years_of_experience": 7.0,
                "current_title": "Search ML Engineer",
                "current_company": "Acme",
                "country": "India",
                "location": "Pune",
            },
            "career_history": [
                {
                    "title": "Search ML Engineer",
                    "company": "Acme",
                    "description": "Owned ranking and retrieval models, improving NDCG by 8% and p95 latency by 20ms.",
                    "duration_months": 36,
                    "is_current": True,
                }
            ],
            "education": [{"field_of_study": "Computer Science", "tier": "tier_2"}],
            "skills": [{"name": "Python", "proficiency": "expert", "duration_months": 48}],
            "redrob_signals": {"last_active_date": "2026-05-15"},
        }
        features = extract_features(candidate, [])
        self.assertGreater(features["current_relevance_score"], 0.0)
        self.assertEqual(features["measured_impact_score"], 1.0)
        self.assertEqual(features["education_field_fit"], 1.0)


if __name__ == "__main__":
    unittest.main()
