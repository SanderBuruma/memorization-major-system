"""Pure-math unit tests for scoreToHue hue computation.

Validates boundary values, monotonicity, and sqrt easing behavior
of the piecewise score-to-hue mapping used for OKLCH mastery colors.

The Python port mirrors the TypeScript implementation that will be
created in Plan 01-02. These tests define the contract.

Run:
    python -m pytest tests/test_mastery_colors.py -v
"""

import math
import unittest


def score_to_hue(score: float) -> float:
    """Port of TypeScript scoreToHue for testing.

    Piecewise mapping:
      score in [-10, -5): red (27) -> yellow (90), sqrt easing
      score in [-5, 0):   yellow (90) -> blue (264), sqrt easing
      score in [0, +10]:  blue (264) -> green (145), sqrt easing
    """
    if score < 0:
        if score >= -5:
            t = math.sqrt(-score / 5)
            return 264 - t * (264 - 90)
        else:
            t = math.sqrt(min(1, (-score - 5) / 5))
            return 90 - t * (90 - 27)
    else:
        t = math.sqrt(min(1, score / 10))
        return 264 - t * (264 - 145)


class TestScoreToHueBoundaries(unittest.TestCase):
    """Anchor values at piecewise segment boundaries."""

    def test_score_neg10_is_red(self):
        self.assertAlmostEqual(score_to_hue(-10), 27, places=1)

    def test_score_neg5_is_yellow(self):
        self.assertAlmostEqual(score_to_hue(-5), 90, places=1)

    def test_score_neg1_is_near_blue(self):
        hue = score_to_hue(-1)
        # Between yellow (90) and blue (264), closer to blue
        self.assertGreater(hue, 150)
        self.assertLess(hue, 264)

    def test_score_pos1_is_near_blue(self):
        hue = score_to_hue(1)
        # Between green (145) and blue (264), closer to blue
        self.assertGreater(hue, 200)
        self.assertLess(hue, 264)

    def test_score_pos5_between_green_and_blue(self):
        hue = score_to_hue(5)
        self.assertGreater(hue, 145)
        self.assertLess(hue, 264)

    def test_score_pos10_is_green(self):
        self.assertAlmostEqual(score_to_hue(10), 145, places=1)


class TestScoreToHueMonotonicity(unittest.TestCase):
    """Hue progression is monotonic within each piecewise segment."""

    def test_positive_monotonic(self):
        """Hue at +5 is between hue at +1 and hue at +10."""
        h1 = score_to_hue(1)
        h5 = score_to_hue(5)
        h10 = score_to_hue(10)
        # Positive scores: hue decreases from 264 toward 145
        self.assertLess(h5, h1, "hue at +5 should be less than hue at +1")
        self.assertGreater(h5, h10, "hue at +5 should be greater than hue at +10")

    def test_negative_near_zero_monotonic(self):
        """Hue at -3 is between hue at -1 and hue at -5 (moving from blue toward yellow)."""
        h1 = score_to_hue(-1)
        h3 = score_to_hue(-3)
        h5 = score_to_hue(-5)
        # Negative scores [-5, 0): hue decreases from 264 toward 90
        self.assertLess(h3, h1, "hue at -3 should be less than hue at -1")
        self.assertGreater(h3, h5, "hue at -3 should be greater than hue at -5")

    def test_negative_far_monotonic(self):
        """Hue at -7 is between hue at -5 and hue at -10 (moving from yellow toward red)."""
        h5 = score_to_hue(-5)
        h7 = score_to_hue(-7)
        h10 = score_to_hue(-10)
        # Negative scores [-10, -5): hue decreases from 90 toward 27
        self.assertLess(h7, h5, "hue at -7 should be less than hue at -5")
        self.assertGreater(h7, h10, "hue at -7 should be greater than hue at -10")


class TestScoreToHueSqrtEasing(unittest.TestCase):
    """Sqrt easing gives more separation at low scores than linear would."""

    def test_positive_sqrt_easing(self):
        """Score +1 moves hue more than linearly away from 264."""
        hue_at_1 = score_to_hue(1)
        linear_hue_at_1 = 264 - (1 / 10) * (264 - 145)  # linear interpolation
        sqrt_hue_at_1 = 264 - math.sqrt(1 / 10) * (264 - 145)  # sqrt interpolation
        self.assertAlmostEqual(hue_at_1, sqrt_hue_at_1, places=5)
        # sqrt(0.1) > 0.1, so sqrt moves hue further from 264 (lower value)
        self.assertLess(hue_at_1, linear_hue_at_1,
                        "sqrt easing should move hue further from 264 at low positive scores")

    def test_negative_sqrt_easing(self):
        """Score -1 moves hue more than linearly away from 264."""
        hue_at_neg1 = score_to_hue(-1)
        linear_hue_at_neg1 = 264 - (1 / 5) * (264 - 90)  # linear: t = score/5
        sqrt_hue_at_neg1 = 264 - math.sqrt(1 / 5) * (264 - 90)  # sqrt
        self.assertAlmostEqual(hue_at_neg1, sqrt_hue_at_neg1, places=5)
        # sqrt(0.2) > 0.2, so sqrt moves hue further from 264 (lower value)
        self.assertLess(hue_at_neg1, linear_hue_at_neg1,
                        "sqrt easing should move hue further from 264 at low negative scores")


if __name__ == "__main__":
    unittest.main()
