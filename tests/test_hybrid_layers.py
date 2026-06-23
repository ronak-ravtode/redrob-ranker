import unittest

from src.anomaly import anomaly_action_summary, detect_anomaly_confidence
from src.jd_understanding import get_default_jd_profile
from src.semantic import semantic_features


class HybridLayerTests(unittest.TestCase):
    def test_jd_profile_exposes_structured_requirements(self):
        profile = get_default_jd_profile()
        self.assertIn("ranking", profile.required_skills)
        self.assertIn("evaluation", profile.required_skills)
        self.assertIn("retrieval", profile.pattern_groups)

    def test_semantic_score_rewards_retrieval_paraphrases(self):
        strong = {
            "profile": {"headline": "Search ML engineer", "summary": "Built relevance systems."},
            "career_history": [
                {
                    "title": "Search Engineer",
                    "company": "Acme",
                    "description": "Owned candidate-role matching with semantic search, vector retrieval, and human relevance evaluation.",
                }
            ],
            "skills": [{"name": "FAISS"}, {"name": "Recommendation Systems"}],
        }
        weak = {
            "profile": {"headline": "Data analyst", "summary": "Built dashboards."},
            "career_history": [{"title": "Analyst", "company": "Acme", "description": "Prepared weekly reporting dashboards."}],
            "skills": [{"name": "Excel"}],
        }
        self.assertGreater(semantic_features(strong)["semantic_fit_score"], semantic_features(weak)["semantic_fit_score"])

    def test_medium_anomaly_penalizes_without_excluding(self):
        candidate = {
            "profile": {"years_of_experience": 2.0, "current_company": "Acme"},
            "career_history": [{"company": "Acme", "is_current": True, "duration_months": 24}],
            "skills": [{"name": "Ranking", "proficiency": "expert", "duration_months": 72}],
        }
        findings = detect_anomaly_confidence(candidate)
        hard_flags, confidence, action, penalty = anomaly_action_summary(findings)
        self.assertEqual(hard_flags, [])
        self.assertEqual(action, "penalize")
        self.assertGreater(confidence, 0.0)
        self.assertGreater(penalty, 0.0)


if __name__ == "__main__":
    unittest.main()
