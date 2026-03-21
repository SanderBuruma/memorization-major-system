"""Tests for quiz state persistence via localStorage.

Loads the esbuild-compiled bundle (static/js/app.js), runs in Node.js with
a localStorage mock and minimal DOM stubs, and verifies saveState/loadState
round-trips correctly.

Run:
    python -m pytest test_persistence.py -v
"""

import json
import os
import subprocess
import tempfile
import unittest

# JS helper: mock browser globals, extract just the state + persistence
# functions from the app, and run assertions in Node.
_NODE_HARNESS = r"""
// -- localStorage mock --
var _store = {};
var localStorage = {
  getItem: function(k){ return _store[k] || null; },
  setItem: function(k,v){ _store[k] = v; },
  removeItem: function(k){ delete _store[k]; },
  clear: function(){ _store = {}; }
};

// -- minimal DOM stubs (never actually called in persistence tests) --
var _stubEl = {textContent:'',value:'',innerHTML:'',disabled:false,className:'',
  focus:function(){},appendChild:function(){},addEventListener:function(){},
  classList:{add:function(){},remove:function(){}},
  setAttribute:function(){},getAttribute:function(){return 'dark';},
  removeAttribute:function(){},
  querySelector:function(){ return _stubEl; },
  querySelectorAll:function(){ return {forEach:function(){}}; },
  insertAdjacentHTML:function(){},
  parentNode:{querySelector:function(){return _stubEl;}},
  remove:function(){}};
var document = {
  getElementById: function(){ return _stubEl; },
  querySelectorAll: function(){ return {forEach:function(){}}; },
  querySelector: function(){ return _stubEl; },
  createElement: function(){ return Object.create(_stubEl); },
  documentElement: {getAttribute:function(){return 'dark';},setAttribute:function(){}},
  cookie: ''
};
var fetch = function(){ return Promise.resolve({ok:true,json:function(){return Promise.resolve({})}}); };
function clearTimeout(){}
function setTimeout(){ return 0; }

// -- paste the app state + persistence code --
%JSCODE%

// -- test runner --
var fs = require('fs');
var _tests = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
var results = [];
for(var _ti = 0; _ti < _tests.length; _ti++){
  try {
    eval(_tests[_ti].code);
    results.push({name: _tests[_ti].name, pass: true});
  } catch(e) {
    results.push({name: _tests[_ti].name, pass: false, error: e.message});
  }
}
process.stdout.write(JSON.stringify(results));
"""


_JS_FILES = [
    "static/js/app.js",
]

def _extract_js_block():
    """Concatenate all JS files in include order."""
    parts = []
    for path in _JS_FILES:
        with open(path, encoding="utf-8") as f:
            parts.append(f.read())
    return "\n".join(parts)


def _run_js_tests(tests):
    """Run a list of {name, code} JS test snippets in Node and return results."""
    js_code = _extract_js_block()
    # Remove the init() call at the bottom (it calls fetch which we don't need)
    import re
    # Unwrap esbuild IIFE so variables are global in test scope
    js_code = js_code.replace('"use strict";\n(() => {\n', "")
    js_code = js_code.replace("\n})();\n", "\n")
    # Strip Object.assign(window, ...) since window doesn't exist in Node
    js_code = re.sub(r"Object\.assign\(window,\s*\{[^}]*\}\);", "", js_code)
    # Remove init() call (may be indented by esbuild)
    js_code = re.sub(r"\n\s*init\(\);\n", "\n", js_code)
    # Convert let/const to var so they're accessible across eval scopes
    js_code = js_code.replace("\nlet ", "\nvar ").replace("\nconst ", "\nvar ")

    harness = _NODE_HARNESS.replace("%JSCODE%", js_code)

    # Write harness and tests to temp files (avoids -e arg-passing issues)
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as hf:
        hf.write(harness)
        harness_path = hf.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(tests, tf)
        tests_path = tf.name
    try:
        result = subprocess.run(
            ["node", harness_path, tests_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Node failed:\n{result.stderr}")
        return json.loads(result.stdout)
    finally:
        os.unlink(harness_path)
        os.unlink(tests_path)


class TestSaveLoadRoundTrip(unittest.TestCase):
    """saveState() writes to localStorage, loadState() restores from it."""

    def test_empty_state_round_trips(self):
        """Default empty state survives save/load cycle."""
        results = _run_js_tests([{
            "name": "empty_round_trip",
            "code": """
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(!saved) throw new Error('nothing saved');
                if(saved.score.correct !== 0) throw new Error('score.correct not 0');
                if(saved.score.total !== 0) throw new Error('score.total not 0');
                if(saved.quizHistory.length !== 0) throw new Error('quizHistory not empty');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_score_persists(self):
        """Score modifications survive save/load."""
        results = _run_js_tests([{
            "name": "score_persists",
            "code": """
                S.score = {correct: 7, total: 12};
                saveState();
                S.score = {correct: 0, total: 0};
                loadState();
                if(S.score.correct !== 7) throw new Error('correct: ' + S.score.correct);
                if(S.score.total !== 12) throw new Error('total: ' + S.score.total);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_scores_persist(self):
        """Quiz scores object survives save/load."""
        results = _run_js_tests([{
            "name": "scores_persist",
            "code": """
                MODES.quiz.scores = {'03': 5, '17': -2, '42': 0};
                saveState();
                MODES.quiz.scores = {};
                loadState();
                if(MODES.quiz.scores['03'] !== 5) throw new Error('03: ' + MODES.quiz.scores['03']);
                if(MODES.quiz.scores['17'] !== -2) throw new Error('17: ' + MODES.quiz.scores['17']);
                if(MODES.quiz.scores['42'] !== 0) throw new Error('42: ' + MODES.quiz.scores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_history_persists(self):
        """Quiz history array survives save/load."""
        results = _run_js_tests([{
            "name": "history_persists",
            "code": """
                MODES.quiz.history = ['03','17','42'];
                saveState();
                MODES.quiz.history = [];
                loadState();
                if(MODES.quiz.history.length !== 3) throw new Error('length: ' + MODES.quiz.history.length);
                if(MODES.quiz.history[2] !== '42') throw new Error('item: ' + MODES.quiz.history[2]);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_all_four_quiz_types_independent(self):
        """Each quiz type's state is saved/loaded independently."""
        results = _run_js_tests([{
            "name": "independent_types",
            "code": """
                MODES.quiz.scores = {'01': 3};
                MODES.reverse.scores = {'02': -1};
                MODES.mixed.scores = {'03': 7};
                MODES.consonant.scores = {'S': 2};
                MODES.quiz.history = ['01'];
                MODES.reverse.history = ['02'];
                MODES.mixed.history = ['03'];
                MODES.consonant.history = ['S'];
                saveState();

                MODES.quiz.scores = {}; MODES.reverse.scores = {}; MODES.mixed.scores = {}; MODES.consonant.scores = {};
                MODES.quiz.history = []; MODES.reverse.history = []; MODES.mixed.history = []; MODES.consonant.history = [];
                loadState();

                if(MODES.quiz.scores['01'] !== 3) throw new Error('quizScores');
                if(MODES.reverse.scores['02'] !== -1) throw new Error('reverseScores');
                if(MODES.mixed.scores['03'] !== 7) throw new Error('mixedScores');
                if(MODES.consonant.scores['S'] !== 2) throw new Error('conScores');
                if(MODES.quiz.history[0] !== '01') throw new Error('quizHistory');
                if(MODES.reverse.history[0] !== '02') throw new Error('reverseHistory');
                if(MODES.mixed.history[0] !== '03') throw new Error('mixedHistory');
                if(MODES.consonant.history[0] !== 'S') throw new Error('conHistory');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestCustomWordsPersistence(unittest.TestCase):
    """customWords survives saveState/loadState round-trip."""

    def test_custom_words_round_trip(self):
        results = _run_js_tests([{
            "name": "customWords_round_trip",
            "code": """
                S.customWords = {'03': 'myword', '42': 'hammer'};
                saveState();
                S.customWords = {};
                loadState();
                if(S.customWords['03'] !== 'myword') throw new Error('03: ' + S.customWords['03']);
                if(S.customWords['42'] !== 'hammer') throw new Error('42: ' + S.customWords['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_custom_words_in_save_payload(self):
        results = _run_js_tests([{
            "name": "customWords_in_payload",
            "code": """
                S.customWords = {'10': 'dice'};
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(!saved.customWords) throw new Error('customWords missing from saved state');
                if(saved.customWords['10'] !== 'dice') throw new Error('value: ' + saved.customWords['10']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_rebuild_wordlist_merges(self):
        results = _run_js_tests([{
            "name": "rebuildWordlist_merges",
            "code": """
                S.defaultWordlist = {'00': 'sauce', '01': 'seed', '02': 'sun'};
                S.customWords = {'01': 'custom'};
                rebuildWordlist();
                if(S.wordlist['00'] !== 'sauce') throw new Error('00: ' + S.wordlist['00']);
                if(S.wordlist['01'] !== 'custom') throw new Error('01: ' + S.wordlist['01']);
                if(S.wordlist['02'] !== 'sun') throw new Error('02: ' + S.wordlist['02']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestLoadStateEdgeCases(unittest.TestCase):
    """loadState() handles missing or corrupt data gracefully."""

    def test_no_stored_data(self):
        """loadState() with empty localStorage keeps defaults."""
        results = _run_js_tests([{
            "name": "no_data",
            "code": """
                localStorage.clear();
                S.score = {correct: 5, total: 10};
                loadState();
                // score should stay as-is when nothing stored
                if(S.score.correct !== 5) throw new Error('score changed: ' + S.score.correct);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_corrupt_json(self):
        """loadState() with invalid JSON doesn't crash."""
        results = _run_js_tests([{
            "name": "corrupt_json",
            "code": """
                localStorage.setItem('quizState', '{broken json!!!');
                S.score = {correct: 3, total: 5};
                loadState();
                if(S.score.correct !== 3) throw new Error('score changed on corrupt data');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_partial_data(self):
        """loadState() with partial blob fills in defaults for missing fields."""
        results = _run_js_tests([{
            "name": "partial_data",
            "code": """
                localStorage.setItem('quizState', JSON.stringify({score: {correct:1, total:2}}));
                MODES.quiz.scores = {old: 99};
                loadState();
                if(S.score.correct !== 1) throw new Error('score not loaded');
                if(Object.keys(MODES.quiz.scores).length !== 0) throw new Error('quizScores not defaulted');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_old_format_discarded(self):
        """loadState() detects old pool/mastered format and discards it."""
        results = _run_js_tests([{
            "name": "old_format_discarded",
            "code": """
                localStorage.setItem('quizState', JSON.stringify({
                    score: {correct: 50, total: 100},
                    quizPool: ['01','02'],
                    quizMastered: {'03': true}
                }));
                S.score = {correct: 0, total: 0};
                loadState();
                // Old format should be discarded, score stays at default
                if(S.score.correct !== 0) throw new Error('old data loaded: ' + S.score.correct);
                // localStorage should be cleared
                if(localStorage.getItem('quizState') !== null)
                    throw new Error('old data not removed from localStorage');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestSaveCallSites(unittest.TestCase):
    """Verify engine functions call saveState and wrappers delegate correctly."""

    @classmethod
    def setUpClass(cls):
        cls.js = _extract_js_block()

    def _function_body(self, name):
        """Extract the body of a JS function by name."""
        start = self.js.index("function " + name + "(")
        # Find the opening brace
        brace = self.js.index("{", start)
        depth = 1
        i = brace + 1
        while depth > 0:
            if self.js[i] == "{":
                depth += 1
            elif self.js[i] == "}":
                depth -= 1
            i += 1
        return self.js[brace:i]

    def test_checkMode_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("checkMode"))

    def test_skipMode_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("skipMode"))

    def test_checkMode_pushes_to_history(self):
        self.assertIn("m.history.push(", self._function_body("checkMode"))

    def test_skipMode_pushes_to_history(self):
        self.assertIn("m.history.push(", self._function_body("skipMode"))

    def test_checkMode_modifies_scores(self):
        self.assertIn("m.scores[", self._function_body("checkMode"))

    def test_init_calls_loadState(self):
        self.assertIn("loadState()", self._function_body("init"))

    def test_wrapper_functions_delegate(self):
        """All check/skip wrappers delegate to the generic engine."""
        for wrapper, engine, mode in [
            ("checkQuiz", "checkMode", "MODES.quiz"),
            ("skipQuiz", "skipMode", "MODES.quiz"),
            ("checkReverse", "checkMode", "MODES.reverse"),
            ("skipReverse", "skipMode", "MODES.reverse"),
            ("checkMixed", "checkMode", "MODES.mixed"),
            ("skipMixed", "skipMode", "MODES.mixed"),
            ("checkCon", "checkMode", "MODES.consonant"),
            ("skipCon", "skipMode", "MODES.consonant"),
        ]:
            with self.subTest(wrapper=wrapper):
                body = self._function_body(wrapper)
                self.assertIn(engine + "(" + mode + ")", body)


class TestJSPickNext(unittest.TestCase):
    """Test the actual JS pickNext function in Node."""

    def test_excludes_history(self):
        results = _run_js_tests([{
            "name": "pickNext_excludes_history",
            "code": """
                var allKeys = ['00','01','02','03','04'];
                var history = ['00','01','02'];
                var scores = {};
                for(var i = 0; i < 100; i++){
                    var pick = pickNext(scores, history, allKeys);
                    if(history.indexOf(pick) !== -1)
                        throw new Error('picked ' + pick + ' which is in history');
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_picks_lowest_score(self):
        results = _run_js_tests([{
            "name": "pickNext_lowest_score",
            "code": """
                var allKeys = ['00','01','02'];
                var scores = {'00': 5, '01': 5, '02': -1};
                for(var i = 0; i < 100; i++){
                    var pick = pickNext(scores, [], allKeys);
                    if(pick !== '02')
                        throw new Error('picked ' + pick + ' instead of 02 (lowest score)');
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_random_among_ties(self):
        results = _run_js_tests([{
            "name": "pickNext_random_ties",
            "code": """
                var allKeys = ['00','01','02'];
                var scores = {};
                var seen = {};
                for(var i = 0; i < 300; i++){
                    var pick = pickNext(scores, [], allKeys);
                    seen[pick] = true;
                }
                if(!seen['00'] || !seen['01'] || !seen['02'])
                    throw new Error('not all keys seen: ' + JSON.stringify(seen));
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_fallback_when_all_in_history(self):
        results = _run_js_tests([{
            "name": "pickNext_fallback",
            "code": """
                var allKeys = ['00','01'];
                var history = ['00','01'];
                var pick = pickNext({}, history, allKeys);
                if(allKeys.indexOf(pick) === -1)
                    throw new Error('picked invalid key: ' + pick);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


if __name__ == "__main__":
    unittest.main()
