"""Tests for quiz state persistence via localStorage.

Extracts the JS from index.html, runs it in Node.js with a localStorage
mock and minimal DOM stubs, and verifies saveState/loadState round-trips
correctly.

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
var tests = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
var results = [];
for(var i = 0; i < tests.length; i++){
  try {
    eval(tests[i].code);
    results.push({name: tests[i].name, pass: true});
  } catch(e) {
    results.push({name: tests[i].name, pass: false, error: e.message});
  }
}
process.stdout.write(JSON.stringify(results));
"""


def _extract_js_block():
    """Extract the main <script> block from index.html (the second one)."""
    with open("static/index.html", encoding="utf-8") as f:
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
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as hf:
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
                if(saved.quizPool.length !== 0) throw new Error('quizPool not empty');
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

    def test_pool_persists(self):
        """Quiz pool array survives save/load."""
        results = _run_js_tests([{
            "name": "pool_persists",
            "code": """
                quizPool = ['03','17','42'];
                saveState();
                quizPool = [];
                loadState();
                if(quizPool.length !== 3) throw new Error('length: ' + quizPool.length);
                if(quizPool[2] !== '42') throw new Error('item: ' + quizPool[2]);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_streaks_persist(self):
        """Streak objects survive save/load."""
        results = _run_js_tests([{
            "name": "streaks_persist",
            "code": """
                reverseStreaks = {'05': 2, '11': 1};
                saveState();
                reverseStreaks = {};
                loadState();
                if(reverseStreaks['05'] !== 2) throw new Error('05: ' + reverseStreaks['05']);
                if(reverseStreaks['11'] !== 1) throw new Error('11: ' + reverseStreaks['11']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_mastered_persists(self):
        """Mastered objects survive save/load."""
        results = _run_js_tests([{
            "name": "mastered_persists",
            "code": """
                mixedMastered = {'22': true, '55': true, '99': true};
                saveState();
                mixedMastered = {};
                loadState();
                if(Object.keys(mixedMastered).length !== 3)
                    throw new Error('count: ' + Object.keys(mixedMastered).length);
                if(!mixedMastered['55']) throw new Error('55 not mastered');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_all_three_quiz_types_independent(self):
        """Each quiz type's state is saved/loaded independently."""
        results = _run_js_tests([{
            "name": "independent_types",
            "code": """
                quizPool = ['01'];
                reversePool = ['02'];
                mixedPool = ['03'];
                quizStreaks = {'01': 1};
                reverseStreaks = {'02': 2};
                mixedStreaks = {'03': 3};
                quizMastered = {'10': true};
                reverseMastered = {'20': true};
                mixedMastered = {'30': true};
                saveState();

                quizPool = []; reversePool = []; mixedPool = [];
                quizStreaks = {}; reverseStreaks = {}; mixedStreaks = {};
                quizMastered = {}; reverseMastered = {}; mixedMastered = {};
                loadState();

                if(quizPool[0] !== '01') throw new Error('quizPool');
                if(reversePool[0] !== '02') throw new Error('reversePool');
                if(mixedPool[0] !== '03') throw new Error('mixedPool');
                if(quizStreaks['01'] !== 1) throw new Error('quizStreaks');
                if(reverseStreaks['02'] !== 2) throw new Error('reverseStreaks');
                if(mixedStreaks['03'] !== 3) throw new Error('mixedStreaks');
                if(!quizMastered['10']) throw new Error('quizMastered');
                if(!reverseMastered['20']) throw new Error('reverseMastered');
                if(!mixedMastered['30']) throw new Error('mixedMastered');
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
                quizPool = ['old'];
                loadState();
                if(score.correct !== 1) throw new Error('score not loaded');
                if(quizPool.length !== 0) throw new Error('quizPool not defaulted: ' + quizPool);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestSaveCallSites(unittest.TestCase):
    """Verify saveState is called from the right functions by inspecting the JS source."""

    @classmethod
    def setUpClass(cls):
        with open("static/index.html", encoding="utf-8") as f:
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

    def test_startQuiz_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("startQuiz"))

    def test_startReverse_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("startReverse"))

    def test_startMixed_calls_saveState(self):
        self.assertIn("saveState()", self._function_body("startMixed"))

    def test_init_calls_loadState(self):
        self.assertIn("loadState()", self._function_body("init"))


if __name__ == "__main__":
    unittest.main()
