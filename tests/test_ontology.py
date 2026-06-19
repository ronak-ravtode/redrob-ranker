import unittest

from src.config import NEGATIVE_PATTERNS, PATTERN_GROUPS
from src.features import is_coarse_candidate
from src.text_utils import contains_any, normalize


class OntologyTests(unittest.TestCase):
    def test_key_paraphrases_are_covered(self):
        examples = [
            ("ranking", "learning to rank model"),
            ("ranking", "candidate ranking system"),
            ("ranking", "relevance ranking"),
            ("ranking", "recommendation system"),
            ("ranking", "match quality"),
            ("retrieval", "semantic search"),
            ("retrieval", "hybrid search"),
            ("retrieval", "candidate-jd matching"),
            ("retrieval", "match people to roles"),
            ("retrieval", "information retrieval"),
            ("retrieval", "surface relevant profiles"),
            ("vector_infra", "vector database"),
            ("vector_infra", "embedding versioning"),
            ("vector_infra", "hnsw"),
            ("evaluation", "ndcg"),
            ("evaluation", "offline metrics"),
            ("evaluation", "a/b testing"),
            ("evaluation", "human relevance judgments"),
            ("production", "real users"),
            ("production", "p95 latency"),
            ("production", "production traffic"),
            ("ownership", "from scratch"),
            ("ownership", "owned"),
            ("ownership", "mentored"),
            ("python", "pytorch"),
            ("python", "sentence-transformers"),
            ("fine_tuning", "qlora"),
        ]
        self.assertGreaterEqual(len(examples), 25)
        for group, phrase in examples:
            with self.subTest(group=group, phrase=phrase):
                self.assertTrue(contains_any(normalize(phrase), PATTERN_GROUPS[group]))

    def test_negative_archetypes_are_rejected(self):
        negatives = [
            ("recent_llm_only", "recently started learning langchain and building small rag demos"),
            ("cv_speech_only", "speech recognition and object detection"),
            ("research_only", "academic lab and pure research at a university"),
        ]
        for group, phrase in negatives:
            with self.subTest(group=group):
                self.assertTrue(contains_any(normalize(phrase), NEGATIVE_PATTERNS[group]))

    def test_plain_language_profile_is_coarse_candidate(self):
        candidate = {
            "profile": {"current_title": "Machine Learning Engineer"},
            "career_history": [
                {
                    "title": "ML Engineer",
                    "description": "Built a system to match people to the most relevant jobs and ran A/B tests.",
                }
            ],
        }
        self.assertTrue(is_coarse_candidate(candidate))

    def test_skill_only_profile_is_not_coarse_candidate(self):
        candidate = {
            "profile": {"current_title": "Software Engineer"},
            "career_history": [{"title": "Software Engineer", "description": "Built internal tools."}],
            "skills": [{"name": "ranking"}, {"name": "retrieval"}],
        }
        self.assertFalse(is_coarse_candidate(candidate))


if __name__ == "__main__":
    unittest.main()
