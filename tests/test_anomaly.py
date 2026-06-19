import unittest

from src.anomaly import detect_anomalies


class AnomalyTests(unittest.TestCase):
    def test_expert_zero_duration_is_flagged(self):
        candidate = {
            "profile": {"years_of_experience": 3.0},
            "career_history": [
                {
                    "start_date": "2023-01-01",
                    "end_date": None,
                    "duration_months": 41,
                }
            ],
            "skills": [
                {"proficiency": "expert", "duration_months": 0},
                {"proficiency": "expert", "duration_months": 0},
                {"proficiency": "expert", "duration_months": 0},
            ],
        }
        flags = detect_anomalies(candidate)
        self.assertIn("multiple_expert_skills_with_zero_duration", flags)

    def test_company_before_founding_year_is_flagged(self):
        candidate = {
            "profile": {"years_of_experience": 5.0},
            "career_history": [
                {
                    "company": "Sarvam AI",
                    "title": "ML Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2021-01-01",
                    "duration_months": 12,
                }
            ],
            "skills": [],
        }
        flags = detect_anomalies(candidate)
        self.assertIn("company_before_founding_year", flags)

    def test_current_job_contradiction_is_flagged(self):
        candidate = {
            "profile": {
                "current_title": "Senior ML Engineer",
                "current_company": "Acme",
                "years_of_experience": 8.0,
            },
            "career_history": [
                {
                    "company": "Acme",
                    "title": "Senior ML Engineer",
                    "start_date": "2022-01-01",
                    "end_date": "2024-01-01",
                    "duration_months": 24,
                    "is_current": True,
                },
                {
                    "company": "Acme",
                    "title": "ML Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2022-01-01",
                    "duration_months": 24,
                },
            ],
            "skills": [],
        }
        flags = detect_anomalies(candidate)
        self.assertIn("contradictory_current_job_state", flags)


if __name__ == "__main__":
    unittest.main()
