import unittest

from src.reasoning import build_reason, build_reason_details


def _features():
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
        "relevant_career_roles": 2,
        "relevant_career_months": 60,
        "experience_fit": 1.0,
        "location_fit": 1.0,
        "notice_fit": 1.0,
        "behavior_fit": 0.9,
        "keyword_stuffer": False,
        "consulting_only": False,
        "cv_only": False,
        "research_only": False,
        "negative_flags": [],
        "career_core": 8,
        "anomaly_flags": [],
        "total_career_months": 60,
        "consulting_months": 0,
        "product_months": 60,
        "product_company_history": 1.0,
        "title_trajectory": 0.75,
        "job_stability": 0.88,
        "skill_corroboration": 0.4,
    }


class ReasoningTests(unittest.TestCase):
    def test_reason_mentions_real_profile_facts(self):
        candidate = {
            "candidate_id": "CAND_0000123",
            "profile": {
                "years_of_experience": 6.4,
                "current_title": "Senior ML Engineer",
                "current_company": "Acme",
            },
            "redrob_signals": {"notice_period_days": 45, "last_active_date": "2026-05-01"},
        }
        features = _features()
        features["career"]["ranking"] = 3
        features["career"]["retrieval"] = 3
        features["career"]["evaluation"] = 2

        details = build_reason_details(candidate, features, 0.91)
        reason = details["reason"]
        self.assertIn("6.4yr", reason)
        self.assertIn("Senior ML Engineer", reason)
        self.assertIn("Acme", reason)
        self.assertTrue(any(piece["sources"] for piece in details["strengths"]))
        self.assertEqual(reason, build_reason(candidate, features, 0.91))

    def test_reason_includes_concern_when_present(self):
        candidate = {
            "candidate_id": "CAND_0000124",
            "profile": {
                "years_of_experience": 8.1,
                "current_title": "Lead AI Engineer",
                "current_company": "Acme",
            },
            "redrob_signals": {"notice_period_days": 120, "last_active_date": "2025-01-01"},
        }
        features = _features()
        features["career"]["ranking"] = 3
        features["career"]["retrieval"] = 3
        features["career"]["vector_infra"] = 2
        details = build_reason_details(candidate, features, 0.62)
        self.assertIn("Concern:", details["reason"])
        self.assertTrue(details["concerns"])
        self.assertIn("notice_period_days", ",".join(details["concerns"][0]["sources"]))

    def test_reason_handles_malformed_years(self):
        candidate = {
            "candidate_id": "CAND_0000125",
            "profile": {
                "years_of_experience": None,
                "current_title": "ML Engineer",
                "current_company": "Acme",
            },
            "redrob_signals": {"notice_period_days": None, "last_active_date": "not-a-date"},
        }
        reason = build_reason(candidate, _features(), 0.5)
        self.assertIn("0.0yr", reason)
        self.assertIn("ML Engineer", reason)


if __name__ == "__main__":
    unittest.main()
