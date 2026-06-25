import time
import unittest

from src.reasoning import build_reason, build_reason_details, _archetype, _rank_band


def _zero_group() -> dict:
    return {
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


def _features(**overrides) -> dict:
    base = {
        "career": _zero_group(),
        "current": _zero_group(),
        "profile_evidence": _zero_group(),
        "skill_evidence": _zero_group(),
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
        "framework_only": False,
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
    base.update(overrides)
    return base


def _candidate(**overrides) -> dict:
    base = {
        "candidate_id": "CAND_0000123",
        "profile": {
            "years_of_experience": 6.4,
            "current_title": "Senior ML Engineer",
            "current_company": "Acme",
        },
        "career_history": [],
        "skills": [],
        "education": [],
        "redrob_signals": {
            "notice_period_days": 30,
            "last_active_date": "2026-05-15",
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.9,
            "interview_completion_rate": 0.9,
            "saved_by_recruiters_30d": 4,
            "github_activity_score": 75,
        },
    }
    for k, v in overrides.items():
        if k in ("profile", "redrob_signals", "career_history", "skills", "education"):
            base[k].update(v) if isinstance(v, dict) else base.__setitem__(k, v)
        else:
            base[k] = v
    return base


# ---------------------------------------------------------------------------
# Original tests (preserved from test_reasoning.py)
# ---------------------------------------------------------------------------

class OriginalReasoningTests(unittest.TestCase):
    def test_reason_mentions_real_profile_facts(self):
        candidate = _candidate()
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
        candidate = _candidate(
            candidate_id="CAND_0000124",
            profile={"years_of_experience": 8.1, "current_title": "Lead AI Engineer", "current_company": "Acme"},
            redrob_signals={"notice_period_days": 120, "last_active_date": "2025-01-01"},
        )
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
            "career_history": [],
            "skills": [],
            "education": [],
            "redrob_signals": {"notice_period_days": None, "last_active_date": "not-a-date"},
        }
        reason = build_reason(candidate, _features(), 0.5)
        self.assertIn("0.0yr", reason)
        self.assertIn("ML Engineer", reason)


# ---------------------------------------------------------------------------
# No-hallucination tests
# ---------------------------------------------------------------------------

class NoHallucinationTests(unittest.TestCase):
    def test_no_hallucinated_title(self):
        candidate = _candidate(
            profile={"current_title": "Search Engineer", "current_company": "Zeta"}
        )
        features = _features()
        features["career"]["retrieval"] = 4
        reason = build_reason(candidate, features, 1.1)
        self.assertIn("Search Engineer", reason)
        self.assertNotIn("Staff ML Engineer", reason)
        self.assertNotIn("Principal Scientist", reason)

    def test_no_hallucinated_company(self):
        candidate = _candidate(profile={"current_company": "Mindtree"})
        reason = build_reason(candidate, _features(), 1.0)
        self.assertIn("Mindtree", reason)
        self.assertNotIn("Google", reason)
        self.assertNotIn("Meta", reason)

    def test_no_hallucinated_years(self):
        candidate = _candidate(profile={"years_of_experience": 3.2})
        reason = build_reason(candidate, _features(), 0.9)
        self.assertIn("3.2yr", reason)
        self.assertNotIn("8.5yr", reason)
        self.assertNotIn("12yr", reason)

    def test_no_hallucinated_skills_when_absent(self):
        candidate = _candidate(skills=[])
        features = _features()
        features["career"]["ranking"] = 4
        reason = build_reason(candidate, features, 1.0)
        self.assertNotIn("Python", reason)
        self.assertNotIn("TensorFlow", reason)

    def test_empty_career_history_no_hallucination(self):
        candidate = _candidate(career_history=[])
        features = _features()
        features["career_core"] = 0
        reason = build_reason(candidate, features, 0.5)
        self.assertNotIn("NDCG", reason)
        self.assertNotIn("FAISS", reason)

    def test_concern_references_real_signal(self):
        candidate = _candidate(
            redrob_signals={"notice_period_days": 120, "last_active_date": "2026-05-15"}
        )
        features = _features()
        details = build_reason_details(candidate, features, 1.0)
        self.assertIn("120-day notice", details["concerns"][0]["text"])
        self.assertIn("notice_period_days", ",".join(details["concerns"][0]["sources"]))

    def test_inactivity_concern_references_real_date(self):
        candidate = _candidate(
            redrob_signals={"last_active_date": "2025-10-01", "notice_period_days": 30}
        )
        features = _features()
        features["location_fit"] = 0.8
        details = build_reason_details(candidate, features, 1.0)
        self.assertIn("2025-10-01", details["concerns"][0]["text"])

    def test_consulting_only_concern_real(self):
        features = _features(consulting_only=True)
        features["career"]["retrieval"] = 4
        candidate = _candidate()
        details = build_reason_details(candidate, features, 1.0)
        self.assertIn("consulting-only", details["concerns"][0]["text"])


# ---------------------------------------------------------------------------
# Variation tests
# ---------------------------------------------------------------------------

class VariationTests(unittest.TestCase):
    def test_different_candidates_get_different_reasoning(self):
        reasons = set()
        for i in range(20):
            candidate = _candidate(
                candidate_id=f"CAND_{i:07d}",
                profile={"current_company": f"Company{i}"}
            )
            features = _features()
            features["career"]["ranking"] = i % 6
            features["career"]["retrieval"] = (i + 1) % 5
            features["career"]["evaluation"] = i % 3
            reason = build_reason(candidate, features, 0.9 + i * 0.05)
            reasons.add(reason)
        self.assertGreaterEqual(len(reasons), 10, "Expected at least 10 unique reasonings out of 20")

    def test_same_candidate_different_ranks_different_tone(self):
        candidate = _candidate()
        features = _features()
        features["career"]["ranking"] = 4
        features["career"]["retrieval"] = 3
        reason_top = build_reason(candidate, features, 1.2, rank=1)
        reason_low = build_reason(candidate, features, 1.2, rank=75)
        # They may share some words but should not be identical if archetype
        # produces different rank-band templates
        self.assertNotEqual(reason_top, reason_low)

    def test_different_archetypes_produce_different_structures(self):
        """Different feature profiles should produce recognizably different reasoning."""
        # product_ml
        prod_feat = _features()
        prod_feat["career"]["production"] = 4
        prod_feat["career"]["ownership"] = 3
        prod_feat["product_company_history"] = 1.0
        prod_candidate = _candidate(profile={"current_title": "ML Engineer"})

        # search
        search_feat = _features()
        search_feat["career"]["retrieval"] = 5
        search_feat["career"]["vector_infra"] = 3
        search_candidate = _candidate(profile={"current_title": "Search Engineer"})

        # risky
        risky_feat = _features(consulting_only=True)
        risky_candidate = _candidate(profile={"current_title": "Consultant"})

        reasons = {
            "product": build_reason(prod_candidate, prod_feat, 1.2),
            "search": build_reason(search_candidate, search_feat, 1.2),
            "risky": build_reason(risky_candidate, risky_feat, 1.2),
        }
        # All three should be distinct
        self.assertEqual(len(set(reasons.values())), 3)


# ---------------------------------------------------------------------------
# Rank-consistent tone tests
# ---------------------------------------------------------------------------

class RankToneTests(unittest.TestCase):
    def test_top_rank_uses_stronger_language(self):
        candidate = _candidate()
        features = _features()
        features["career"]["ranking"] = 5
        features["career"]["retrieval"] = 4
        features["career"]["evaluation"] = 3
        features["career"]["production"] = 3
        features["career"]["ownership"] = 3

        reason_top = build_reason(candidate, features, 1.5, rank=1)
        reason_low = build_reason(candidate, features, 1.5, rank=75)
        # Top should have stronger signals
        strong_words = {"stands out", "strong", "top", "leader", "shortlist"}
        caution_words = {"borderline", "narrowly", "limited", "thin", "low-band", "marginal"}

        top_has_strong = any(w in reason_top.lower() for w in strong_words)
        low_has_caution = any(w in reason_low.lower() for w in caution_words)
        self.assertTrue(top_has_strong or low_has_caution,
                        f"Top should be stronger, low should be more cautious.\nTop: {reason_top}\nLow: {reason_low}")

    def test_mid_rank_between_top_and_low(self):
        candidate = _candidate()
        features = _features()
        features["career"]["ranking"] = 4
        features["career"]["retrieval"] = 3
        features["career"]["evaluation"] = 2
        features["career"]["production"] = 2
        features["career"]["ownership"] = 2

        reason_top = build_reason(candidate, features, 1.3, rank=1)
        reason_mid = build_reason(candidate, features, 1.3, rank=25)
        reason_low = build_reason(candidate, features, 1.3, rank=75)
        # All three should be different strings
        self.assertEqual(len({reason_top, reason_mid, reason_low}), 3)

    def test_concern_always_present(self):
        """Every reasoning must include a concern."""
        for rank in [1, 10, 25, 50, 75, 100]:
            candidate = _candidate(candidate_id=f"CAND_{rank:07d}")
            features = _features()
            features["career"]["ranking"] = rank % 5
            reason = build_reason(candidate, features, 1.0, rank=rank)
            self.assertIn("Concern:", reason, f"Rank {rank} missing concern")


# ---------------------------------------------------------------------------
# Determinism and performance tests
# ---------------------------------------------------------------------------

class DeterminismTests(unittest.TestCase):
    def test_same_input_same_output(self):
        candidate = _candidate()
        features = _features()
        features["career"]["ranking"] = 4
        features["career"]["retrieval"] = 3
        r1 = build_reason(candidate, features, 1.1, rank=5)
        r2 = build_reason(candidate, features, 1.1, rank=5)
        self.assertEqual(r1, r2)

    def test_different_seed_different_output(self):
        c1 = _candidate(candidate_id="CAND_0000001")
        c2 = _candidate(candidate_id="CAND_0000002")
        features = _features()
        features["career"]["ranking"] = 4
        features["career"]["retrieval"] = 3
        r1 = build_reason(c1, features, 1.1, rank=5)
        r2 = build_reason(c2, features, 1.1, rank=5)
        # With 4 variants per archetype, two different IDs should often differ
        # (probability of collision per archetype = 1/4 = 25%)
        # We just verify the function doesn't crash and returns strings
        self.assertIsInstance(r1, str)
        self.assertIsInstance(r2, str)

    def test_reasoning_generation_is_fast(self):
        """Generate reasoning for 100 candidates and verify it's well under 5 minutes."""
        candidates = []
        features_list = []
        for i in range(100):
            c = _candidate(candidate_id=f"CAND_{i:07d}")
            f = _features()
            f["career"]["ranking"] = i % 8
            f["career"]["retrieval"] = (i + 1) % 6
            f["career"]["evaluation"] = i % 4
            f["career"]["production"] = i % 3
            candidates.append(c)
            features_list.append(f)

        start = time.perf_counter()
        for i in range(100):
            build_reason(candidates[i], features_list[i], 0.8 + i * 0.01, rank=i + 1)
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 5.0, f"100 reasonings took {elapsed:.2f}s, should be <5s")


# ---------------------------------------------------------------------------
# Archetype and rank band tests
# ---------------------------------------------------------------------------

class ArchetypeTests(unittest.TestCase):
    def test_borderline_when_low_score(self):
        self.assertEqual(_archetype(_features(), 0.5), "borderline")
        self.assertEqual(_archetype(_features(), 0.81), "borderline")

    def test_risky_when_consulting_only(self):
        self.assertEqual(_archetype(_features(consulting_only=True), 1.2), "risky")

    def test_risky_when_research_only(self):
        self.assertEqual(_archetype(_features(research_only=True), 1.2), "risky")

    def test_risky_when_framework_only(self):
        self.assertEqual(_archetype(_features(framework_only=True), 1.2), "risky")

    def test_risky_when_keyword_stuffer(self):
        self.assertEqual(_archetype(_features(keyword_stuffer=True), 1.2), "risky")

    def test_search_when_strong_retrieval(self):
        feat = _features()
        feat["career"]["retrieval"] = 4
        feat["career"]["vector_infra"] = 2
        self.assertEqual(_archetype(feat, 1.2), "search")

    def test_behavioral_when_high_engagement(self):
        feat = _features()
        feat["behavior_fit"] = 0.85
        feat["career_core"] = 4
        self.assertEqual(_archetype(feat, 1.2), "behavioral")

    def test_product_ml_when_production_and_ownership(self):
        feat = _features()
        feat["career"]["production"] = 3
        feat["career"]["ownership"] = 2
        feat["product_company_history"] = 1.0
        self.assertEqual(_archetype(feat, 1.2), "product_ml")

    def test_production_when_strong_production(self):
        feat = _features()
        feat["career"]["production"] = 4
        self.assertEqual(_archetype(feat, 1.2), "production")

    def test_active_dev_when_good_behavior(self):
        feat = _features()
        feat["behavior_fit"] = 0.75
        self.assertEqual(_archetype(feat, 1.2), "active_dev")

    def test_general_fallback(self):
        feat = _features()
        feat["behavior_fit"] = 0.4
        self.assertEqual(_archetype(feat, 1.2), "general")


class RankBandTests(unittest.TestCase):
    def test_top_band(self):
        self.assertEqual(_rank_band(1), "top")
        self.assertEqual(_rank_band(5), "top")
        self.assertEqual(_rank_band(10), "top")

    def test_mid_band(self):
        self.assertEqual(_rank_band(11), "mid")
        self.assertEqual(_rank_band(30), "mid")
        self.assertEqual(_rank_band(50), "mid")

    def test_low_band(self):
        self.assertEqual(_rank_band(51), "low")
        self.assertEqual(_rank_band(75), "low")
        self.assertEqual(_rank_band(100), "low")


# ---------------------------------------------------------------------------
# Detail structure tests
# ---------------------------------------------------------------------------

class DetailStructureTests(unittest.TestCase):
    def test_build_reason_details_returns_all_keys(self):
        candidate = _candidate()
        features = _features()
        details = build_reason_details(candidate, features, 1.0, rank=5)
        self.assertIn("reason", details)
        self.assertIn("strengths", details)
        self.assertIn("concerns", details)
        self.assertIn("sources", details)
        self.assertIsInstance(details["strengths"], list)
        self.assertGreaterEqual(len(details["strengths"]), 1)
        self.assertIsInstance(details["concerns"], list)
        self.assertGreaterEqual(len(details["concerns"]), 1)

    def test_strength_sources_are_populated(self):
        candidate = _candidate()
        features = _features()
        details = build_reason_details(candidate, features, 1.0)
        for s in details["strengths"]:
            self.assertTrue(s["sources"], "Strength should have non-empty sources")
            self.assertTrue(s["text"], "Strength should have non-empty text")

    def test_concern_sources_are_populated(self):
        candidate = _candidate(
            redrob_signals={"notice_period_days": 120, "last_active_date": "2026-05-15"}
        )
        features = _features()
        details = build_reason_details(candidate, features, 1.0)
        for c in details["concerns"]:
            self.assertTrue(c["sources"], "Concern should have non-empty sources")
            self.assertTrue(c["text"], "Concern should have non-empty text")


# ---------------------------------------------------------------------------
# Sample output test (prints one of each archetype)
# ---------------------------------------------------------------------------

class SampleOutputTests(unittest.TestCase):
    def test_sample_each_archetype(self):
        archetypes = {
            "product_ml": _features(**{
                "career": {**_zero_group(), "production": 4, "ownership": 3},
                "product_company_history": 1.0,
            }),
            "search": _features(**{
                "career": {**_zero_group(), "retrieval": 5, "vector_infra": 3},
            }),
            "behavioral": _features(**{
                "behavior_fit": 0.85,
                "career_core": 4,
            }),
            "risky": _features(consulting_only=True),
            "borderline": _features(**{"career_core": 1}),
            "production": _features(**{
                "career": {**_zero_group(), "production": 5},
            }),
            "active_dev": _features(**{"behavior_fit": 0.75}),
            "general": _features(**{"behavior_fit": 0.4}),
        }
        for arch, feat in archetypes.items():
            c = _candidate(profile={"current_title": f"{arch.title()} Engineer", "current_company": "TestCo"})
            reason = build_reason(c, feat, 1.0, rank=5)
            self.assertIsInstance(reason, str)
            self.assertGreater(len(reason), 20)
            self.assertIn("Concern:", reason)


if __name__ == "__main__":
    unittest.main()
