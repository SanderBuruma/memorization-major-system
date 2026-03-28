"""Tests for time-based EMA scoring system.

Covers:
- updateTimeScore EMA formula (first answer, subsequent, convergence)
- Timer state: resetResponseTimer, pauseTimer, resumeTimer, getElapsedSeconds
- Prefix-match timer pausing via handleQuizInput
- getTimeLimit float-score mapping
- Score ranges and boundary behavior

Run:
    python -m pytest tests/test_time_scoring.py -v
"""

import math
import unittest

from tests.js_harness import run_js_tests as _run_js_tests

WRONG_ANSWER_SECONDS = 10
SCORE_HISTORY_MAX = 10
WEIGHT_DECAY = 0.7


def time_to_contribution(seconds: float) -> float:
    """Python port of timeToContribution: +5 at ≤0.5s, 0 at 2s, -5 at ≥10s."""
    if seconds <= 0.5:
        return 5
    if seconds <= 2:
        return 5 * (2 - seconds) / 1.5
    if seconds >= 10:
        return -5
    return -5 * (seconds - 2) / 8


def weighted_average(values: list[float]) -> float:
    """Python port of weightedAverage: newest weighs 1, each older 0.7x less."""
    s, ws = 0.0, 0.0
    w = 1.0
    for v in reversed(values):
        s += v * w
        ws += w
        w *= WEIGHT_DECAY
    return s / ws


def update_score(hist: list[float], seconds: float) -> float:
    """Push contribution to history, return weighted average."""
    hist.append(time_to_contribution(seconds))
    if len(hist) > SCORE_HISTORY_MAX:
        hist.pop(0)
    return weighted_average(hist)


# ── Pure Python EMA math tests ─────────────────────────────────────


class TestTimeToContribution(unittest.TestCase):
    """Verify the piecewise contribution function."""

    def test_instant_capped_at_5(self):
        self.assertAlmostEqual(time_to_contribution(0.0), 5.0)

    def test_half_second_is_5(self):
        self.assertAlmostEqual(time_to_contribution(0.5), 5.0)

    def test_breakeven_at_2s(self):
        self.assertAlmostEqual(time_to_contribution(2.0), 0.0)

    def test_1s_is_positive(self):
        expected = 5 * (2 - 1) / 1.5  # ≈ 3.33
        self.assertAlmostEqual(time_to_contribution(1.0), expected)

    def test_10s_is_neg5(self):
        self.assertAlmostEqual(time_to_contribution(10.0), -5.0)

    def test_6s_is_neg2_5(self):
        expected = -5 * (6 - 2) / 8  # = -2.5
        self.assertAlmostEqual(time_to_contribution(6.0), expected)

    def test_beyond_10s_capped_at_neg5(self):
        self.assertAlmostEqual(time_to_contribution(20.0), -5.0)


class TestWeightedAverage(unittest.TestCase):
    """Verify the weighted running average math independent of JS."""

    def test_single_value(self):
        """Single value → that value."""
        self.assertAlmostEqual(weighted_average([3.0]), 3.0)

    def test_two_values_decay(self):
        """Two values: newest weight 1, oldest weight 0.7."""
        result = weighted_average([2.0, 4.0])
        expected = (2.0 * 0.7 + 4.0 * 1.0) / (0.7 + 1.0)
        self.assertAlmostEqual(result, expected)

    def test_newest_weighs_most(self):
        """Newest value has the highest individual weight."""
        result = weighted_average([0.0, 0.0, 0.0, 10.0])
        # weight: 1/(1+0.7+0.49+0.343) ≈ 0.395 of total → 10*0.395 ≈ 3.95
        self.assertGreater(result, 3.5)

    def test_all_same(self):
        """All same values → that value regardless of weights."""
        self.assertAlmostEqual(weighted_average([3.0, 3.0, 3.0]), 3.0)

    def test_first_answer_fast(self):
        hist = []
        score = update_score(hist, 1.0)
        self.assertAlmostEqual(score, 5 * (2 - 1) / 1.5, places=2)

    def test_first_answer_breakeven(self):
        hist = []
        score = update_score(hist, 2.0)
        self.assertAlmostEqual(score, 0.0)

    def test_first_answer_wrong(self):
        hist = []
        score = update_score(hist, WRONG_ANSWER_SECONDS)
        self.assertAlmostEqual(score, -5.0)

    def test_first_answer_half_second(self):
        hist = []
        score = update_score(hist, 0.5)
        self.assertAlmostEqual(score, 5.0)

    def test_history_capped_at_10(self):
        hist = []
        for _ in range(15):
            update_score(hist, 1.0)
        self.assertEqual(len(hist), 10)

    def test_recovery_from_wrong_answer(self):
        """After a wrong answer, fast answers pull score back up."""
        hist = []
        update_score(hist, WRONG_ANSWER_SECONDS)
        for _ in range(9):
            update_score(hist, 0.5)
        score = weighted_average(hist)
        # 9 fast answers at +5 should dominate the 1 wrong at -5
        self.assertGreater(score, 3.0)

    def test_recent_answers_dominate(self):
        """Recent fast answers outweigh older slow ones."""
        hist = []
        for _ in range(5):
            update_score(hist, 8.0)  # slow → negative
        for _ in range(5):
            update_score(hist, 0.5)  # fast → +5
        score = weighted_average(hist)
        # Recent +5 values weigh more than older negative ones
        self.assertGreater(score, 0)


# ── JS updateTimeScore tests ───────────────────────────────────────


class TestTimeToContributionJS(unittest.TestCase):
    """Test the piecewise timeToContribution function in the JS bundle."""

    def test_half_second_is_5(self):
        results = _run_js_tests([{
            "name": "contrib_0_5s",
            "code": """
                var c = timeToContribution(0.5);
                if (Math.abs(c - 5) > 0.001) throw new Error('expected 5, got ' + c);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_breakeven_at_2s(self):
        results = _run_js_tests([{
            "name": "contrib_2s",
            "code": """
                var c = timeToContribution(2.0);
                if (Math.abs(c) > 0.001) throw new Error('expected 0, got ' + c);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_10s_is_neg5(self):
        results = _run_js_tests([{
            "name": "contrib_10s",
            "code": """
                var c = timeToContribution(10);
                if (Math.abs(c - (-5)) > 0.001) throw new Error('expected -5, got ' + c);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_beyond_10s_capped(self):
        results = _run_js_tests([{
            "name": "contrib_20s",
            "code": """
                var c = timeToContribution(20);
                if (Math.abs(c - (-5)) > 0.001) throw new Error('expected -5, got ' + c);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestUpdateTimeScoreJS(unittest.TestCase):
    """Test updateTimeScore function in the actual JS bundle."""

    def test_first_answer_sets_contribution(self):
        results = _run_js_tests([{
            "name": "first_answer",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '42', 1.0);
                var expected = 5 * (2 - 1) / 1.5;
                if (Math.abs(scores['42'] - expected) > 0.001)
                    throw new Error('expected ' + expected + ', got ' + scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_two_answers_weighted(self):
        results = _run_js_tests([{
            "name": "two_answers_weighted",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '42', 2.0);  // contribution 0
                updateTimeScore(scores, hist, '42', 0.5);  // contribution 5
                // weighted: (0*0.7 + 5*1) / (0.7 + 1) = 5/1.7
                var expected = 5 / 1.7;
                if (Math.abs(scores['42'] - expected) > 0.01)
                    throw new Error('expected ' + expected + ', got ' + scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_wrong_answer_penalty(self):
        results = _run_js_tests([{
            "name": "wrong_answer_penalty",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '42', 10);
                if (Math.abs(scores['42'] - (-5)) > 0.001)
                    throw new Error('expected -5, got ' + scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_breakeven_at_2s(self):
        results = _run_js_tests([{
            "name": "breakeven_2s",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '42', 2.0);
                if (Math.abs(scores['42']) > 0.001)
                    throw new Error('expected 0, got ' + scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_history_capped_at_10(self):
        results = _run_js_tests([{
            "name": "history_cap",
            "code": """
                var scores = {}, hist = {};
                for (var i = 0; i < 15; i++) updateTimeScore(scores, hist, '42', 1.0);
                if (hist['42'].length !== 10)
                    throw new Error('expected 10 entries, got ' + hist['42'].length);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_recent_values_dominate(self):
        results = _run_js_tests([{
            "name": "recent_dominate",
            "code": """
                var scores = {}, hist = {};
                for (var i = 0; i < 5; i++) updateTimeScore(scores, hist, '42', 10);
                for (var i = 0; i < 5; i++) updateTimeScore(scores, hist, '42', 0.5);
                if (scores['42'] <= 0)
                    throw new Error('expected positive (recent fast), got ' + scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


# ── JS timer state tests ──────────────────────────────────────────


class TestTimerStateJS(unittest.TestCase):
    """Test response timer functions in JS using controlled performance.now()."""

    def test_elapsed_basic(self):
        """getElapsedSeconds returns time since resetResponseTimer."""
        results = _run_js_tests([{
            "name": "elapsed_basic",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 3500;
                var elapsed = getElapsedSeconds();
                if (Math.abs(elapsed - 2.5) > 0.001)
                    throw new Error('expected 2.5, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_elapsed_with_pause(self):
        """Paused time is not counted in getElapsedSeconds."""
        results = _run_js_tests([{
            "name": "elapsed_with_pause",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 2000;  // 1s of thinking
                pauseTimer();
                _time = 5000;  // 3s paused (should not count)
                resumeTimer();
                _time = 6000;  // 1s more thinking
                var elapsed = getElapsedSeconds();
                if (Math.abs(elapsed - 2.0) > 0.001)
                    throw new Error('expected 2.0, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_double_pause_ignored(self):
        """Calling pauseTimer twice doesn't double-count."""
        results = _run_js_tests([{
            "name": "double_pause",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 2000;
                pauseTimer();
                _time = 2500;
                pauseTimer();  // should be no-op
                _time = 4000;
                resumeTimer();
                _time = 5000;
                var elapsed = getElapsedSeconds();
                // 1s before pause + 1s after resume = 2s
                if (Math.abs(elapsed - 2.0) > 0.001)
                    throw new Error('expected 2.0, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_double_resume_ignored(self):
        """Calling resumeTimer when not paused is a no-op."""
        results = _run_js_tests([{
            "name": "double_resume",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 2000;
                resumeTimer();  // no-op, not paused
                _time = 3000;
                var elapsed = getElapsedSeconds();
                if (Math.abs(elapsed - 2.0) > 0.001)
                    throw new Error('expected 2.0, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_reset_clears_all(self):
        """resetResponseTimer clears accumulated time and paused state."""
        results = _run_js_tests([{
            "name": "reset_clears",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 5000;
                pauseTimer();
                // Now reset
                _time = 10000;
                resetResponseTimer();
                _time = 11000;
                var elapsed = getElapsedSeconds();
                if (Math.abs(elapsed - 1.0) > 0.001)
                    throw new Error('expected 1.0, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_elapsed_while_paused(self):
        """getElapsedSeconds during pause returns only pre-pause time."""
        results = _run_js_tests([{
            "name": "elapsed_while_paused",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 3000;  // 2s thinking
                pauseTimer();
                _time = 8000;  // 5s paused
                var elapsed = getElapsedSeconds();
                if (Math.abs(elapsed - 2.0) > 0.001)
                    throw new Error('expected 2.0, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_multiple_pause_resume_cycles(self):
        """Multiple pause/resume cycles correctly accumulate only thinking time."""
        results = _run_js_tests([{
            "name": "multiple_cycles",
            "code": """
                var _time = 0;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 1000;   // 1s thinking
                pauseTimer();
                _time = 3000;   // 2s paused
                resumeTimer();
                _time = 3500;   // 0.5s thinking
                pauseTimer();
                _time = 6000;   // 2.5s paused
                resumeTimer();
                _time = 7000;   // 1s thinking
                var elapsed = getElapsedSeconds();
                // 1 + 0.5 + 1 = 2.5s
                if (Math.abs(elapsed - 2.5) > 0.001)
                    throw new Error('expected 2.5, got ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_elapsed_never_negative(self):
        """getElapsedSeconds never returns negative."""
        results = _run_js_tests([{
            "name": "never_negative",
            "code": """
                var _time = 1000;
                performance.now = function() { return _time; };
                resetResponseTimer();
                _time = 500;  // time went backwards (shouldn't happen, but guard)
                var elapsed = getElapsedSeconds();
                if (elapsed < 0)
                    throw new Error('elapsed is negative: ' + elapsed);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


# ── getTimeLimit float-score mapping ───────────────────────────────


class TestGetTimeLimitJS(unittest.TestCase):
    """Test getTimeLimit maps float scores to countdown seconds."""

    def test_negative_score_no_limit(self):
        results = _run_js_tests([{
            "name": "neg_score",
            "code": """
                var result = getTimeLimit(-2.5);
                if (result !== 0) throw new Error('expected 0, got ' + result);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_zero_score_no_limit(self):
        results = _run_js_tests([{
            "name": "zero_score",
            "code": """
                var result = getTimeLimit(0);
                if (result !== 0) throw new Error('expected 0, got ' + result);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_small_positive_generous_limit(self):
        """Score 0.5 → tier ceil(0.75)=1 → 15s (most generous)."""
        results = _run_js_tests([{
            "name": "small_positive",
            "code": """
                var result = getTimeLimit(0.5);
                if (result !== 15) throw new Error('expected 15, got ' + result);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_moderate_positive_tighter_limit(self):
        """Score 2.0 → tier ceil(3)=3 → 6s."""
        results = _run_js_tests([{
            "name": "moderate_positive",
            "code": """
                var result = getTimeLimit(2.0);
                if (result !== 6) throw new Error('expected 6, got ' + result);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_high_positive_tight_limit(self):
        """Score 5.0 → tier ceil(7.5)=8 → 3s (tightest)."""
        results = _run_js_tests([{
            "name": "high_positive",
            "code": """
                var result = getTimeLimit(5.0);
                if (result !== 3) throw new Error('expected 3, got ' + result);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_limit_increases_with_score(self):
        """Higher scores should have equal or tighter (lower) time limits."""
        results = _run_js_tests([{
            "name": "monotonic_limits",
            "code": """
                var scores = [0.1, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0];
                for (var i = 1; i < scores.length; i++) {
                    var prev = getTimeLimit(scores[i-1]);
                    var curr = getTimeLimit(scores[i]);
                    if (curr > prev)
                        throw new Error('limit at ' + scores[i] + ' (' + curr + ') > limit at ' + scores[i-1] + ' (' + prev + ')');
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


# ── Prefix-match pause grace tests ────────────────────────────────


class TestPrefixPauseGraceJS(unittest.TestCase):
    """Test the 500ms grace window for prefix-matching timer pauses."""

    def test_grace_timeout_exists(self):
        """PAUSE_GRACE_MS constant should be 500."""
        results = _run_js_tests([{
            "name": "grace_constant",
            "code": """
                if (PAUSE_GRACE_MS !== 500)
                    throw new Error('expected 500, got ' + PAUSE_GRACE_MS);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


# ── Integration: scoring + pickNext ────────────────────────────────


class TestScoringPickNextIntegration(unittest.TestCase):
    """Verify pickNext prioritizes items with worse (lower) time-based scores."""

    def test_slow_items_picked_most(self):
        results = _run_js_tests([{
            "name": "slow_items_most",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '00', 1.0);
                updateTimeScore(scores, hist, '01', 8.0);
                updateTimeScore(scores, hist, '02', 0.5);
                var keys = ['00', '01', '02'];
                var counts = {'00': 0, '01': 0, '02': 0};
                for (var i = 0; i < 500; i++) {
                    counts[pickNext(scores, [], keys)]++;
                }
                if (counts['01'] <= counts['00'] || counts['01'] <= counts['02'])
                    throw new Error('slowest item 01 should be picked most: ' + JSON.stringify(counts));
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_wrong_answers_picked_most(self):
        results = _run_js_tests([{
            "name": "wrong_picked_most",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '00', 1.0);
                updateTimeScore(scores, hist, '01', 1.0);
                updateTimeScore(scores, hist, '02', 10);
                var keys = ['00', '01', '02'];
                var counts = {'00': 0, '01': 0, '02': 0};
                for (var i = 0; i < 500; i++) {
                    counts[pickNext(scores, [], keys)]++;
                }
                if (counts['02'] <= counts['00'] || counts['02'] <= counts['01'])
                    throw new Error('wrong-answer item 02 should be picked most: ' + JSON.stringify(counts));
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_unseen_items_preferred(self):
        """Unseen items default to 0, preferred over positive-scored items."""
        results = _run_js_tests([{
            "name": "unseen_preferred",
            "code": """
                var scores = {}, hist = {};
                updateTimeScore(scores, hist, '00', 1.0);
                updateTimeScore(scores, hist, '01', 0.5);
                var keys = ['00', '01', '02'];
                var counts = {'00': 0, '01': 0, '02': 0};
                for (var i = 0; i < 500; i++) {
                    counts[pickNext(scores, [], keys)]++;
                }
                if (counts['02'] <= counts['00'] || counts['02'] <= counts['01'])
                    throw new Error('unseen item 02 should be picked most: ' + JSON.stringify(counts));
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_full_simulation_with_weighted_avg(self):
        """All items eventually seen over many rounds with weighted average scoring."""
        results = _run_js_tests([{
            "name": "full_sim_weighted",
            "code": """
                var allKeys = [];
                for (var i = 0; i < 100; i++) allKeys.push(String(i).padStart(2, '0'));
                var scores = {}, hist = {};
                var history = [];
                var seen = {};
                for (var round = 0; round < 2000; round++) {
                    var key = pickNext(scores, history, allKeys);
                    seen[key] = true;
                    updateTimeScore(scores, hist, key, 1.5);
                    history.push(key);
                    if (history.length > 10) history.shift();
                }
                var seenCount = Object.keys(seen).length;
                if (seenCount !== 100)
                    throw new Error('expected 100 seen, got ' + seenCount);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


# ── Persistence: float scores survive save/load ────────────────────


class TestPersistence(unittest.TestCase):
    """Scores and scoreHistory round-trip through save/load."""

    def test_float_scores_persist(self):
        results = _run_js_tests([{
            "name": "float_persist",
            "code": """
                MODES.quiz.scores = {'03': 1.5, '17': -2.4, '42': 0.0};
                saveState();
                MODES.quiz.scores = {};
                loadState();
                if (Math.abs(MODES.quiz.scores['03'] - 1.5) > 0.001)
                    throw new Error('03: ' + MODES.quiz.scores['03']);
                if (Math.abs(MODES.quiz.scores['17'] - (-2.4)) > 0.001)
                    throw new Error('17: ' + MODES.quiz.scores['17']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_score_history_persists(self):
        results = _run_js_tests([{
            "name": "history_persist",
            "code": """
                MODES.quiz.scoreHistory = {'03': [5, 3.33, -2.5]};
                saveState();
                MODES.quiz.scoreHistory = {};
                loadState();
                var h = MODES.quiz.scoreHistory['03'];
                if (!h || h.length !== 3)
                    throw new Error('length: ' + (h ? h.length : 'null'));
                if (Math.abs(h[2] - (-2.5)) > 0.001)
                    throw new Error('h[2]: ' + h[2]);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_old_scores_without_history_still_load(self):
        """Old data without scoreHistory loads gracefully (history defaults to {})."""
        results = _run_js_tests([{
            "name": "old_compat",
            "code": """
                MODES.quiz.scores = {'03': 5};
                MODES.quiz.scoreHistory = {'03': [5]};
                saveState();
                // Simulate old data: remove scoreHistory from stored blob
                var blob = JSON.parse(localStorage.getItem('quizState'));
                delete blob.quizScoreHistory;
                localStorage.setItem('quizState', JSON.stringify(blob));
                MODES.quiz.scoreHistory = {should: [1, 2, 3]};
                loadState();
                // scoreHistory should default to empty
                if (Object.keys(MODES.quiz.scoreHistory).length !== 0)
                    throw new Error('scoreHistory not empty: ' + JSON.stringify(MODES.quiz.scoreHistory));
                // scores should still load
                if (MODES.quiz.scores['03'] !== 5)
                    throw new Error('03: ' + MODES.quiz.scores['03']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
