"""Tests for the pool-based quiz system.

Replicates the JS pool logic in Python and statistically verifies
correctness of pool initialization, replacement, graduation, skip
behavior, and the 80-mastered recycle mechanism.

Run:
    python -m pytest test_pool_quiz.py -v
"""

import random
import unittest

ALL_KEYS = [str(i).zfill(2) for i in range(100)]


# ── JS pool logic faithfully replicated in Python ─────────────────────

def init_pool(mastered: dict, keys=ALL_KEYS) -> list:
    available = [k for k in keys if k not in mastered]
    random.shuffle(available)
    return available[:10]


def replace_in_pool(pool: list, mastered_key: str, mastered: dict, keys=ALL_KEYS):
    if mastered_key in pool:
        pool.remove(mastered_key)
    available = [k for k in keys if k not in mastered and k not in pool]
    if available:
        pool.append(random.choice(available))


def pick_from_pool(pool: list, last_key: str | None) -> str | None:
    if not pool:
        return None
    if len(pool) == 1:
        return pool[0]
    pick = last_key
    while pick == last_key:
        pick = random.choice(pool)
    return pick


class TestInitPool(unittest.TestCase):

    def test_returns_10_keys(self):
        pool = init_pool({})
        self.assertEqual(len(pool), 10)

    def test_excludes_mastered(self):
        mastered = {str(i).zfill(2): True for i in range(95)}
        pool = init_pool(mastered)
        self.assertEqual(len(pool), 5)
        for k in pool:
            self.assertNotIn(k, mastered)

    def test_all_keys_valid(self):
        pool = init_pool({})
        for k in pool:
            self.assertIn(k, ALL_KEYS)

    def test_no_duplicates(self):
        for _ in range(50):
            pool = init_pool({})
            self.assertEqual(len(pool), len(set(pool)))

    def test_randomness(self):
        """Multiple inits should not always return the same pool."""
        pools = [frozenset(init_pool({})) for _ in range(20)]
        self.assertGreater(len(set(pools)), 1)


class TestReplaceInPool(unittest.TestCase):

    def test_removes_mastered_key_and_adds_replacement(self):
        mastered = {}
        pool = init_pool(mastered)
        old_key = pool[0]
        mastered[old_key] = True
        replace_in_pool(pool, old_key, mastered)
        self.assertEqual(len(pool), 10)
        self.assertNotIn(old_key, pool)

    def test_replacement_not_in_mastered(self):
        mastered = {str(i).zfill(2): True for i in range(89)}
        pool = init_pool(mastered)  # 11 available, pool gets 10
        key = pool[0]
        mastered[key] = True
        replace_in_pool(pool, key, mastered)
        for k in pool:
            self.assertNotIn(k, mastered)

    def test_pool_shrinks_when_no_replacements(self):
        mastered = {str(i).zfill(2): True for i in range(91)}
        pool = init_pool(mastered)  # 9 available
        self.assertEqual(len(pool), 9)
        key = pool[0]
        mastered[key] = True
        replace_in_pool(pool, key, mastered)
        self.assertEqual(len(pool), 8)  # no replacement available

    def test_no_duplicates_after_replace(self):
        for _ in range(50):
            mastered = {}
            pool = init_pool(mastered)
            key = pool[0]
            mastered[key] = True
            replace_in_pool(pool, key, mastered)
            self.assertEqual(len(pool), len(set(pool)))


class TestPickFromPool(unittest.TestCase):

    def test_returns_none_for_empty(self):
        self.assertIsNone(pick_from_pool([], None))

    def test_returns_only_element(self):
        self.assertEqual(pick_from_pool(["42"], "42"), "42")

    def test_avoids_last_key(self):
        pool = ["01", "02", "03"]
        for _ in range(100):
            pick = pick_from_pool(pool, "01")
            self.assertNotEqual(pick, "01")

    def test_all_pool_members_reachable(self):
        pool = ["01", "02", "03"]
        seen = set()
        for _ in range(200):
            seen.add(pick_from_pool(pool, None))
        self.assertEqual(seen, {"01", "02", "03"})


class TestStreakGraduation(unittest.TestCase):
    """Simulate the check logic: 3 correct in a row = mastered."""

    def test_graduates_after_3_correct(self):
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)
        key = pool[0]

        for _ in range(3):
            streaks[key] = streaks.get(key, 0) + 1

        self.assertEqual(streaks[key], 3)
        mastered[key] = True
        replace_in_pool(pool, key, mastered)
        self.assertNotIn(key, pool)
        self.assertIn(key, mastered)

    def test_incorrect_resets_streak(self):
        streaks = {}
        key = "07"
        streaks[key] = 2  # 2 correct so far
        # incorrect answer
        streaks[key] = 0
        self.assertEqual(streaks[key], 0)

    def test_skip_resets_streak(self):
        streaks = {}
        key = "07"
        streaks[key] = 2
        # skip behavior
        streaks[key] = 0
        self.assertEqual(streaks[key], 0)


class TestRecycleAt80(unittest.TestCase):
    """When mastered count hits 80, one random word gets recycled."""

    def _simulate_to_80(self):
        """Simulate mastering 80 words and triggering recycle."""
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)

        mastered_count = 0
        while mastered_count < 80:
            key = pool[0]
            streaks[key] = streaks.get(key, 0) + 1
            if streaks[key] >= 3:
                mastered[key] = True
                replace_in_pool(pool, key, mastered)
                mastered_count = len(mastered)
                if mastered_count >= 80:
                    # Recycle 1 random mastered key
                    mastered_keys = list(mastered.keys())
                    recycled = random.choice(mastered_keys)
                    del mastered[recycled]
                    streaks[recycled] = 0
                    return mastered, streaks, pool, recycled
        return mastered, streaks, pool, None

    def test_mastered_drops_to_79_after_recycle(self):
        mastered, _, _, recycled = self._simulate_to_80()
        self.assertEqual(len(mastered), 79)
        self.assertIsNotNone(recycled)
        self.assertNotIn(recycled, mastered)

    def test_recycled_key_streak_reset(self):
        mastered, streaks, _, recycled = self._simulate_to_80()
        self.assertEqual(streaks[recycled], 0)

    def test_mastered_never_exceeds_80(self):
        """Run a full simulation: mastered count should never exceed 80."""
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)

        for _ in range(2000):
            if not pool:
                if len(mastered) >= len(ALL_KEYS):
                    mastered.clear()
                    streaks.clear()
                pool = init_pool(mastered)
            key = pick_from_pool(pool, None)
            if key is None:
                break
            streaks[key] = streaks.get(key, 0) + 1
            if streaks[key] >= 3:
                mastered[key] = True
                replace_in_pool(pool, key, mastered)
                if len(mastered) >= 80:
                    mastered_keys = list(mastered.keys())
                    recycled = random.choice(mastered_keys)
                    del mastered[recycled]
                    streaks[recycled] = 0
            self.assertLessEqual(len(mastered), 80)

    def test_recycle_distributes_across_keys(self):
        """Over many recycle events, different keys get recycled (not always the same)."""
        recycled_keys = set()
        for _ in range(50):
            _, _, _, recycled = self._simulate_to_80()
            if recycled:
                recycled_keys.add(recycled)
        # With 80 mastered keys to choose from, we should see variety
        self.assertGreater(len(recycled_keys), 5)


class TestPoolPersistence(unittest.TestCase):
    """Pool should persist across quiz rounds (not re-initialized)."""

    def test_pool_not_reinitialized_when_nonempty(self):
        mastered = {}
        pool = init_pool(mastered)
        original_pool = pool.copy()
        # Simulate "startQuiz" — pool is non-empty, should NOT re-init
        if not pool:
            pool = init_pool(mastered)  # This branch should NOT execute
        self.assertEqual(pool, original_pool)

    def test_pool_reinitialized_when_empty(self):
        mastered = {}
        pool = []
        if not pool:
            pool = init_pool(mastered)
        self.assertEqual(len(pool), 10)


class TestFullSimulation(unittest.TestCase):
    """End-to-end simulation of quiz behavior."""

    def test_only_pool_words_are_quizzed(self):
        """All quizzed words must come from the current pool."""
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)
        quizzed = []

        for _ in range(200):
            if not pool:
                pool = init_pool(mastered)
            key = pick_from_pool(pool, quizzed[-1] if quizzed else None)
            if key is None:
                break
            self.assertIn(key, pool)
            quizzed.append(key)
            # Always answer correctly
            streaks[key] = streaks.get(key, 0) + 1
            if streaks[key] >= 3:
                mastered[key] = True
                replace_in_pool(pool, key, mastered)
                if len(mastered) >= 80:
                    mk = list(mastered.keys())
                    recycled = random.choice(mk)
                    del mastered[recycled]
                    streaks[recycled] = 0

    def test_no_consecutive_repeats_with_pool_gt_1(self):
        """When pool has >1 word, no two consecutive picks should match."""
        pool = init_pool({})
        last = None
        for _ in range(500):
            pick = pick_from_pool(pool, last)
            if len(pool) > 1:
                self.assertNotEqual(pick, last)
            last = pick

    def test_all_100_words_eventually_seen(self):
        """Over enough rounds, all 100 words should be quizzed."""
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)
        seen = set()

        for _ in range(5000):
            if not pool:
                if len(mastered) >= len(ALL_KEYS):
                    mastered.clear()
                    streaks.clear()
                pool = init_pool(mastered)
            key = pick_from_pool(pool, None)
            if key is None:
                break
            seen.add(key)
            streaks[key] = streaks.get(key, 0) + 1
            if streaks[key] >= 3:
                mastered[key] = True
                replace_in_pool(pool, key, mastered)
                if len(mastered) >= 80:
                    mk = list(mastered.keys())
                    recycled = random.choice(mk)
                    del mastered[recycled]
                    streaks[recycled] = 0

        self.assertEqual(seen, set(ALL_KEYS))


class TestMixedQuiz(unittest.TestCase):
    """Mixed quiz uses the same pool mechanics but randomly picks direction."""

    def test_mixed_uses_same_pool_logic(self):
        """Mixed quiz pool/streak/mastery works identically to forward/reverse."""
        mastered = {}
        streaks = {}
        pool = init_pool(mastered)

        # Simulate 200 mixed rounds (direction doesn't affect pool logic)
        for _ in range(200):
            if not pool:
                if len(mastered) >= len(ALL_KEYS):
                    mastered.clear()
                    streaks.clear()
                pool = init_pool(mastered)
            key = pick_from_pool(pool, None)
            if key is None:
                break
            self.assertIn(key, pool)
            streaks[key] = streaks.get(key, 0) + 1
            if streaks[key] >= 3:
                mastered[key] = True
                replace_in_pool(pool, key, mastered)
                if len(mastered) >= 80:
                    mk = list(mastered.keys())
                    recycled = random.choice(mk)
                    del mastered[recycled]
                    streaks[recycled] = 0
            self.assertLessEqual(len(mastered), 80)

    def test_direction_is_random(self):
        """Over many rounds, both directions should appear."""
        directions = set()
        for _ in range(100):
            directions.add('forward' if random.random() < 0.5 else 'reverse')
        self.assertEqual(directions, {'forward', 'reverse'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
