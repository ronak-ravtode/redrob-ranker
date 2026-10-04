import re
import unittest

from sandbox_app import _build_results_html, _score_bar_width


def _row(cid: str, score: float) -> dict:
    return {
        "candidate": {
            "candidate_id": cid,
            "profile": {
                "current_title": "Civil Engineer",
                "current_company": "Wipro",
                "years_of_experience": 5.5,
                "anonymized_name": "Test",
            },
        },
        "features": {},
        "score": score,
        "score_parts": {
            "evidence": 0.0,
            "semantic": 0.65,
            "behavior": 0.1,
            "penalty": 0.3,
        },
    }


class ScoreBarWidthTest(unittest.TestCase):
    def test_narrow_score_band_still_produces_visible_separation(self):
        scores = [0.1067, 0.1061, 0.1047, 0.1043, 0.1041, 0.1041, 0.1039]
        widths = [_score_bar_width(s, min(scores), max(scores)) for s in scores]

        self.assertTrue(all(0.0 <= w <= 100.0 for w in widths), widths)
        self.assertGreaterEqual(max(widths) - min(widths), 60.0)
        self.assertEqual(widths[0], max(widths))

    def test_flat_scores_do_not_all_collapse_to_the_same_stub(self):
        widths = [_score_bar_width(0.1, 0.1, 0.1) for _ in range(3)]
        self.assertTrue(all(w > 0 for w in widths), widths)

    def test_wider_band_still_respects_bounds(self):
        self.assertEqual(_score_bar_width(2.0, 0.0, 2.0), 100.0)
        self.assertEqual(_score_bar_width(1.0, 0.0, 2.0), 54.0)


class ResultsHtmlTest(unittest.TestCase):
    def test_bar_widths_are_not_all_identical(self):
        ranked = [_row("CAND_0000001", 0.1067), _row("CAND_0000002", 0.1039)]
        body = _build_results_html(ranked)

        widths = [float(w) for w in re.findall(r"width:([0-9.]+)px;\"", body)]
        self.assertGreater(len(set(widths)), 1, widths)

    def test_bar_is_labelled_relative_and_keeps_absolute_score(self):
        ranked = [_row("CAND_0000001", 0.1067), _row("CAND_0000002", 0.1039)]
        body = _build_results_html(ranked)

        self.assertIn("scaled across the top 10 only", body)
        self.assertIn("0.1067", body)


if __name__ == "__main__":
    unittest.main()