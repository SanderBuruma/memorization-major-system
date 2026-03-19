"""Tests for quiz state persistence via localStorage.

Extracts the JS from index.html, runs it in Node.js with a localStorage
mock and minimal DOM stubs, and verifies saveState/loadState round-trips
correctly for the score-based quiz system.

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
  classList:{add:function(){},remove:function(){}}};
var document = {
  getElementById: function(){ return _stubEl; },
  querySelectorAll: function(){ return {forEach:function(){}}; },
  querySelector: function(){ return _stubEl; },
  documentElement: {getAttribute:function(){return 'dark';},setAttribute:function(){}}
};
var fetch = function(){ return Promise.resolve({json:function(){return Promise.resolve({})}}); };
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


def _extract_js_block():
    """Extract the main <script> block from index.html (the second one)."""
    with open("templates/index.html", encoding="utf-8") as f:
        html = f.read()
    # The app script is the last <script>...</script> block
    idx = html.rfind("<script>")
    end = html.rfind("</script>")
    return html[idx + len("<script>"):end]


def _run_js_tests(tests):
    """Run a list of {name, code} JS test snippets in Node and return results."""
    js_code = _extract_js_block()
    # Remove the init() call at the bottom (it calls fetch which we don't need)
    js_code = js_code.replace("\ninit();\n", "\n")
    js_code = js_code.replace("\ninit();", "\n")
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
                score = {correct: 7, total: 12};
                saveState();
                // Reset in-memory
                score = {correct: 0, total: 0};
                // Restore
                loadState();
                if(score.correct !== 7) throw new Error('correct: ' + score.correct);
                if(score.total !== 12) throw new Error('total: ' + score.total);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_scores_persist(self):
        """Quiz scores object survives save/load."""
        results = _run_js_tests([{
            "name": "scores_persist",
            "code": """
                quizScores = {'03': 5, '17': -2, '42': 0};
                saveState();
                quizScores = {};
                loadState();
                if(quizScores['03'] !== 5) throw new Error('03: ' + quizScores['03']);
                if(quizScores['17'] !== -2) throw new Error('17: ' + quizScores['17']);
                if(quizScores['42'] !== 0) throw new Error('42: ' + quizScores['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_history_persists(self):
        """Quiz history array survives save/load."""
        results = _run_js_tests([{
            "name": "history_persists",
            "code": """
                quizHistory = ['03','17','42'];
                saveState();
                quizHistory = [];
                loadState();
                if(quizHistory.length !== 3) throw new Error('length: ' + quizHistory.length);
                if(quizHistory[2] !== '42') throw new Error('item: ' + quizHistory[2]);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_all_four_quiz_types_independent(self):
        """Each quiz type's state is saved/loaded independently."""
        results = _run_js_tests([{
            "name": "independent_types",
            "code": """
                quizScores = {'01': 3};
                reverseScores = {'02': -1};
                mixedScores = {'03': 7};
                conScores = {'S': 2};
                quizHistory = ['01'];
                reverseHistory = ['02'];
                mixedHistory = ['03'];
                conHistory = ['S'];
                saveState();

                quizScores = {}; reverseScores = {}; mixedScores = {}; conScores = {};
                quizHistory = []; reverseHistory = []; mixedHistory = []; conHistory = [];
                loadState();

                if(quizScores['01'] !== 3) throw new Error('quizScores');
                if(reverseScores['02'] !== -1) throw new Error('reverseScores');
                if(mixedScores['03'] !== 7) throw new Error('mixedScores');
                if(conScores['S'] !== 2) throw new Error('conScores');
                if(quizHistory[0] !== '01') throw new Error('quizHistory');
                if(reverseHistory[0] !== '02') throw new Error('reverseHistory');
                if(mixedHistory[0] !== '03') throw new Error('mixedHistory');
                if(conHistory[0] !== 'S') throw new Error('conHistory');
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
                score = {correct: 5, total: 10};
                loadState();
                // score should stay as-is when nothing stored
                if(score.correct !== 5) throw new Error('score changed: ' + score.correct);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_corrupt_json(self):
        """loadState() with invalid JSON doesn't crash."""
        results = _run_js_tests([{
            "name": "corrupt_json",
            "code": """
                localStorage.setItem('quizState', '{broken json!!!');
                score = {correct: 3, total: 5};
                loadState();
                if(score.correct !== 3) throw new Error('score changed on corrupt data');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_partial_data(self):
        """loadState() with partial blob fills in defaults for missing fields."""
        results = _run_js_tests([{
            "name": "partial_data",
            "code": """
                localStorage.setItem('quizState', JSON.stringify({score: {correct:1, total:2}}));
                quizScores = {old: 99};
                loadState();
                if(score.correct !== 1) throw new Error('score not loaded');
                if(Object.keys(quizScores).length !== 0) throw new Error('quizScores not defaulted');
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
                score = {correct: 0, total: 0};
                loadState();
                // Old format should be discarded, score stays at default
                if(score.correct !== 0) throw new Error('old data loaded: ' + score.correct);
                // localStorage should be cleared
                if(localStorage.getItem('quizState') !== null)
                    throw new Error('old data not removed from localStorage');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestSaveCallSites(unittest.TestCase):
    """Verify saveState is called from the right functions by inspecting the JS source."""

    @classmethod
    def setUpClass(cls):
        with open("templates/index.html", encoding="utf-8") as f:
            cls.js = f.read()

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

    def test_checkQuiz_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("checkQuiz"))

    def test_skipQuiz_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("skipQuiz"))

    def test_checkReverse_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("checkReverse"))

    def test_skipReverse_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("skipReverse"))

    def test_checkMixed_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("checkMixed"))

    def test_skipMixed_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("skipMixed"))

    def test_checkCon_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("checkCon"))

    def test_skipCon_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("skipCon"))

    def test_init_calls_loadState(self):
        self.assertIn("loadState()", self._function_body("init"))

    def test_check_functions_push_to_history(self):
        """All check* functions must push to their respective history array."""
        for func, hist in [
            ("checkQuiz", "quizHistory"),
            ("checkReverse", "reverseHistory"),
            ("checkMixed", "mixedHistory"),
            ("checkCon", "conHistory"),
        ]:
            with self.subTest(func=func):
                body = self._function_body(func)
                self.assertIn(f"{hist}.push(", body,
                              f"{func} must push to {hist}")

    def test_skip_functions_push_to_history(self):
        """All skip* functions must push to their respective history array."""
        for func, hist in [
            ("skipQuiz", "quizHistory"),
            ("skipReverse", "reverseHistory"),
            ("skipMixed", "mixedHistory"),
            ("skipCon", "conHistory"),
        ]:
            with self.subTest(func=func):
                body = self._function_body(func)
                self.assertIn(f"{hist}.push(", body,
                              f"{func} must push to {hist}")

    def test_check_functions_modify_scores(self):
        """All check* functions must modify their respective scores object."""
        for func, scores in [
            ("checkQuiz", "quizScores"),
            ("checkReverse", "reverseScores"),
            ("checkMixed", "mixedScores"),
            ("checkCon", "conScores"),
        ]:
            with self.subTest(func=func):
                body = self._function_body(func)
                self.assertIn(f"{scores}[", body,
                              f"{func} must modify {scores}")


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
