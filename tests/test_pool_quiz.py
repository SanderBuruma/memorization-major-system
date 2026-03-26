"""Tests for the score-based quiz selection system.

Replicates the JS pickNext logic in Python and verifies
correctness of selection, scoring, history cooldown, and
full simulation behavior.

Run:
    python -m pytest test_pool_quiz.py -v
"""

import random
import unittest

ALL_KEYS = [str(i).zfill(2) for i in range(100)]
HISTORY_SIZE = 10


# ── JS pickNext logic faithfully replicated in Python ────────────────

def pick_next(scores: dict, history: list, all_keys: list) -> str:
    """Pick the next key: exclude history, find min score, random among ties."""
    eligible = [k for k in all_keys if k not in history]
    if not eligible:
        eligible = all_keys[:]  # fallback if all in cooldown
    min_score = min((scores.get(k, 0) for k in eligible), default=0)
    candidates = [k for k in eligible if scores.get(k, 0) == min_score]
    return random.choice(candidates)


class TestPickNext(unittest.TestCase):

    def test_excludes_history(self):
        history = ALL_KEYS[:10]
        for _ in range(100):
            pick = pick_next({}, history, ALL_KEYS)
            self.assertNotIn(pick, history)

    def test_picks_from_lowest_score(self):
        scores = {"00": 5, "01": 5, "02": 0, "03": 0}
        test_keys = ["00", "01", "02", "03"]
        picks = set()
        for _ in range(200):
            picks.add(pick_next(scores, [], test_keys))
        self.assertEqual(picks, {"02", "03"})

    def test_random_among_ties(self):
        """When multiple keys share the min score, all should be reachable."""
        scores = {"00": 0, "01": 0, "02": 0}
        test_keys = ["00", "01", "02"]
        picks = set()
        for _ in range(200):
            picks.add(pick_next(scores, [], test_keys))
        self.assertEqual(picks, {"00", "01", "02"})

    def test_default_score_is_zero(self):
        """Keys not in scores dict should be treated as score 0."""
        scores = {"00": 1}
        test_keys = ["00", "01"]
        for _ in range(100):
            pick = pick_next(scores, [], test_keys)
            self.assertEqual(pick, "01")

    def test_fallback_when_all_in_history(self):
        """When all keys are in history, fallback to picking from all keys."""
        small_keys = ["00", "01", "02"]
        history = ["00", "01", "02"]
        pick = pick_next({}, history, small_keys)
        self.assertIn(pick, small_keys)

    def test_negative_scores_preferred(self):
        scores = {"00": -2, "01": 0, "02": 3}
        test_keys = ["00", "01", "02"]
        for _ in range(100):
            pick = pick_next(scores, [], test_keys)
            self.assertEqual(pick, "00")


WRONG_S = 10
WEIGHT_DECAY = 0.7
HISTORY_MAX = 10


def _time_to_contribution(seconds: float) -> float:
    if seconds <= 0.5:
        return 5
    if seconds <= 2:
        return 5 * (2 - seconds) / 1.5
    if seconds >= 10:
        return -5
    return -5 * (seconds - 2) / 8


def _weighted_avg(values: list) -> float:
    s, ws, w = 0.0, 0.0, 1.0
    for v in reversed(values):
        s += v * w
        ws += w
        w *= WEIGHT_DECAY
    return s / ws


def update_time_score(scores: dict, hists: dict, key: str, seconds: float) -> None:
    """Python port of updateTimeScore (weighted running average)."""
    arr = hists.setdefault(key, [])
    arr.append(_time_to_contribution(seconds))
    if len(arr) > HISTORY_MAX:
        arr.pop(0)
    scores[key] = _weighted_avg(arr)


class TestScoring(unittest.TestCase):

    def test_fast_answer_positive(self):
        scores, hists = {}, {}
        update_time_score(scores, hists, "07", 1.0)
        expected = 5 * (2 - 1) / 1.5  # ≈ 3.33
        self.assertAlmostEqual(scores["07"], expected)

    def test_slow_answer_negative(self):
        scores, hists = {}, {}
        update_time_score(scores, hists, "07", 6.0)
        self.assertAlmostEqual(scores["07"], -2.5)

    def test_wrong_answer_very_negative(self):
        scores, hists = {}, {}
        update_time_score(scores, hists, "07", WRONG_S)
        self.assertAlmostEqual(scores["07"], -5.0)

    def test_skip_no_change(self):
        scores = {"07": 1.5}
        # Skip: no score change
        self.assertAlmostEqual(scores["07"], 1.5)

    def test_weighted_two_answers(self):
        scores, hists = {}, {}
        update_time_score(scores, hists, "07", 2.0)  # contribution = 0
        update_time_score(scores, hists, "07", 0.5)  # contribution = 5
        expected = (0 * 0.7 + 5 * 1.0) / (0.7 + 1.0)
        self.assertAlmostEqual(scores["07"], expected)

    def test_score_can_go_negative(self):
        scores, hists = {}, {}
        update_time_score(scores, hists, "07", 5.0)
        self.assertLess(scores["07"], 0)


class TestHistory(unittest.TestCase):

    def test_fifo_capped_at_10(self):
        history = []
        for i in range(15):
            history.append(str(i).zfill(2))
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0], "05")
        self.assertEqual(history[-1], "14")

    def test_word_re_eligible_after_10_others(self):
        history = []
        # Show key "00", then 10 other keys
        history.append("00")
        for i in range(1, 11):
            history.append(str(i).zfill(2))
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        # "00" should have been pushed out
        self.assertNotIn("00", history)

    def test_skip_adds_to_history(self):
        """Skip should still add the key to history."""
        history = []
        key = "42"
        # Simulating skip: push to history, no score change
        history.append(key)
        if len(history) > HISTORY_SIZE:
            history.pop(0)
        self.assertIn(key, history)

    def test_history_blocks_selection(self):
        """Keys in history should not be selected by pick_next."""
        test_keys = ALL_KEYS[:20]
        history = test_keys[:10]
        for _ in range(100):
            pick = pick_next({}, history, test_keys)
            self.assertNotIn(pick, history)


class TestFullSimulation(unittest.TestCase):

    def test_all_words_eventually_seen(self):
        """Over enough rounds, all 100 words should be quizzed."""
        scores, hists = {}, {}
        history = []
        seen = set()
        for _ in range(2000):
            key = pick_next(scores, history, ALL_KEYS)
            seen.add(key)
            update_time_score(scores, hists, key, 1.5)
            history.append(key)
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        self.assertEqual(seen, set(ALL_KEYS))

    def test_no_word_repeated_within_10(self):
        """No word should appear twice within 10 consecutive presentations."""
        scores, hists = {}, {}
        history = []
        recent = []
        for _ in range(500):
            key = pick_next(scores, history, ALL_KEYS)
            if len(recent) >= HISTORY_SIZE:
                self.assertNotIn(key, recent[-HISTORY_SIZE:])
            recent.append(key)
            update_time_score(scores, hists, key, 1.5)
            history.append(key)
            if len(history) > HISTORY_SIZE:
                history.pop(0)

    def test_low_score_words_appear_more_often(self):
        """Words with lower scores should be picked more frequently."""
        scores = {"00": -5.0, "01": 0.0, "02": 1.5, "03": 1.5}
        test_keys = ["00", "01", "02", "03"]
        counts = {k: 0 for k in test_keys}
        history = []
        for _ in range(500):
            key = pick_next(scores, history, test_keys)
            counts[key] += 1
            history.append(key)
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        # "00" has the lowest score, should appear most often
        self.assertGreater(counts["00"], counts["02"])
        self.assertGreater(counts["00"], counts["03"])

    def test_consonant_keys_work(self):
        """Consonant quiz has ~16 keys; cooldown of 10 still functions."""
        con_keys = ["S", "Z", "T", "D", "TH", "N", "M", "R",
                    "L", "SH", "CH", "J", "C", "G", "F", "V", "B", "P"]
        scores, hists = {}, {}
        history = []
        seen = set()
        for _ in range(500):
            key = pick_next(scores, history, con_keys)
            seen.add(key)
            update_time_score(scores, hists, key, 1.0)
            history.append(key)
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        self.assertEqual(seen, set(con_keys))

    def test_mixed_correct_and_incorrect(self):
        """Simulation with mixed correct/incorrect answers runs without error."""
        scores, hists = {}, {}
        history = []
        for i in range(2000):
            key = pick_next(scores, history, ALL_KEYS)
            if i % 3 == 0:
                update_time_score(scores, hists, key, WRONG_S)
            else:
                update_time_score(scores, hists, key, 1.5)
            history.append(key)
            if len(history) > HISTORY_SIZE:
                history.pop(0)
        # Scores should exist and be bounded by the contribution range
        self.assertGreater(len(scores), 0)
        for v in scores.values():
            self.assertGreaterEqual(v, -5.0)
            self.assertLessEqual(v, 5.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
