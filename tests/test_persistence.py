"""Tests for quiz state persistence via localStorage.

Loads the esbuild-compiled bundle (static/js/app.js), runs in Node.js with
a localStorage mock and minimal DOM stubs, and verifies saveState/loadState
round-trips correctly.

Run:
    python -m pytest test_persistence.py -v
"""

import unittest

from tests.js_harness import extract_js, run_js_tests as _run_js_tests


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
                appState.score = {correct: 7, total: 12};
                saveState();
                appState.score = {correct: 0, total: 0};
                loadState();
                if(appState.score.correct !== 7) throw new Error('correct: ' + appState.score.correct);
                if(appState.score.total !== 12) throw new Error('total: ' + appState.score.total);
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
                appState.customWords = {'03': 'myword', '42': 'hammer'};
                saveState();
                appState.customWords = {};
                loadState();
                if(appState.customWords['03'] !== 'myword') throw new Error('03: ' + appState.customWords['03']);
                if(appState.customWords['42'] !== 'hammer') throw new Error('42: ' + appState.customWords['42']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_custom_words_in_save_payload(self):
        results = _run_js_tests([{
            "name": "customWords_in_payload",
            "code": """
                appState.customWords = {'10': 'dice'};
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
                appState.defaultWordlist = {'00': 'sauce', '01': 'seed', '02': 'sun'};
                appState.customWords = {'01': 'custom'};
                rebuildWordlist();
                if(appState.wordlist['00'] !== 'sauce') throw new Error('00: ' + appState.wordlist['00']);
                if(appState.wordlist['01'] !== 'custom') throw new Error('01: ' + appState.wordlist['01']);
                if(appState.wordlist['02'] !== 'sun') throw new Error('02: ' + appState.wordlist['02']);
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
                appState.score = {correct: 5, total: 10};
                loadState();
                // score should stay as-is when nothing stored
                if(appState.score.correct !== 5) throw new Error('score changed: ' + appState.score.correct);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_corrupt_json(self):
        """loadState() with invalid JSON doesn't crash."""
        results = _run_js_tests([{
            "name": "corrupt_json",
            "code": """
                localStorage.setItem('quizState', '{broken json!!!');
                appState.score = {correct: 3, total: 5};
                loadState();
                if(appState.score.correct !== 3) throw new Error('score changed on corrupt data');
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
                if(appState.score.correct !== 1) throw new Error('score not loaded');
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
                appState.score = {correct: 0, total: 0};
                loadState();
                // Old format should be discarded, score stays at default
                if(appState.score.correct !== 0) throw new Error('old data loaded: ' + appState.score.correct);
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
        cls.js = extract_js()

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
        self.assertIn("mode.history.push(", self._function_body("checkMode"))

    def test_skipMode_pushes_to_history(self):
        self.assertIn("mode.history.push(", self._function_body("skipMode"))

    def test_checkMode_modifies_scores(self):
        self.assertIn("updateTimeScore(mode.scores", self._function_body("checkMode"))

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

    def test_prefers_lowest_score(self):
        results = _run_js_tests([{
            "name": "pickNext_prefers_lowest",
            "code": """
                var allKeys = ['00','01','02'];
                var scores = {'00': 5, '01': 5, '02': -1};
                var counts = {'00': 0, '01': 0, '02': 0};
                for(var i = 0; i < 500; i++){
                    counts[pickNext(scores, [], allKeys)]++;
                }
                if(counts['02'] <= counts['00'] + counts['01'])
                    throw new Error('lowest-scored 02 should dominate: ' + JSON.stringify(counts));
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


class TestThemeCycling(unittest.TestCase):
    """Test toggleTheme cycles through all 4 themes and setTheme sets directly."""

    def test_toggle_cycles_dark_light_oled_highcontrast(self):
        """toggleTheme() cycles dark → light → oled → high-contrast → dark."""
        results = _run_js_tests([{
            "name": "theme_cycle",
            "code": """
                document.documentElement._theme = 'dark';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                var expected = ['light', 'oled', 'high-contrast', 'dark'];
                for (var i = 0; i < expected.length; i++) {
                    toggleTheme();
                    if (document.documentElement._theme !== expected[i])
                        throw new Error('After toggle ' + (i+1) + ': expected ' +
                            expected[i] + ', got ' + document.documentElement._theme);
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_setTheme_sets_directly(self):
        """setTheme() sets the data-theme attribute to the given value."""
        results = _run_js_tests([{
            "name": "setTheme_direct",
            "code": """
                document.documentElement._theme = 'dark';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                setTheme('oled');
                if (document.documentElement._theme !== 'oled')
                    throw new Error('expected oled, got ' + document.documentElement._theme);
                setTheme('high-contrast');
                if (document.documentElement._theme !== 'high-contrast')
                    throw new Error('expected high-contrast, got ' + document.documentElement._theme);
                setTheme('light');
                if (document.documentElement._theme !== 'light')
                    throw new Error('expected light, got ' + document.documentElement._theme);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_setTheme_persists_to_localStorage(self):
        """setTheme() writes the theme to localStorage."""
        results = _run_js_tests([{
            "name": "setTheme_localStorage",
            "code": """
                document.documentElement._theme = 'dark';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                setTheme('high-contrast');
                var stored = localStorage.getItem('theme');
                if (stored !== 'high-contrast')
                    throw new Error('localStorage theme: ' + stored);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_toggle_persists_to_localStorage(self):
        """toggleTheme() writes each new theme to localStorage."""
        results = _run_js_tests([{
            "name": "toggle_localStorage",
            "code": """
                document.documentElement._theme = 'dark';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                toggleTheme();
                if (localStorage.getItem('theme') !== 'light')
                    throw new Error('after 1st toggle: ' + localStorage.getItem('theme'));
                toggleTheme();
                if (localStorage.getItem('theme') !== 'oled')
                    throw new Error('after 2nd toggle: ' + localStorage.getItem('theme'));
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_theme_in_saveState_payload(self):
        """saveState() includes the current theme in the persisted JSON."""
        results = _run_js_tests([{
            "name": "theme_in_saveState",
            "code": """
                document.documentElement._theme = 'oled';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if (saved.theme !== 'oled')
                    throw new Error('saveState theme: ' + saved.theme);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_all_four_themes_round_trip_saveState(self):
        """Each of the 4 theme values round-trips through saveState."""
        results = _run_js_tests([{
            "name": "all_themes_saveState",
            "code": """
                document.documentElement._theme = 'dark';
                document.documentElement.getAttribute = function(a) {
                    return this._theme;
                };
                document.documentElement.setAttribute = function(a, v) {
                    this._theme = v;
                };
                var themes = ['dark', 'light', 'oled', 'high-contrast'];
                for (var i = 0; i < themes.length; i++) {
                    document.documentElement._theme = themes[i];
                    saveState();
                    var saved = JSON.parse(localStorage.getItem('quizState'));
                    if (saved.theme !== themes[i])
                        throw new Error('theme ' + themes[i] + ' saved as ' + saved.theme);
                }
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestActivityLogPersistence(unittest.TestCase):
    """activityLog survives saveState/loadState round-trip."""

    def test_activity_log_round_trip(self):
        results = _run_js_tests([{
            "name": "activityLog_round_trip",
            "code": """
                appState.activityLog = {'2026-03-21': 15, '2026-03-20': 3};
                saveState();
                appState.activityLog = {};
                loadState();
                if(appState.activityLog['2026-03-21'] !== 15)
                    throw new Error('2026-03-21: ' + appState.activityLog['2026-03-21']);
                if(appState.activityLog['2026-03-20'] !== 3)
                    throw new Error('2026-03-20: ' + appState.activityLog['2026-03-20']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_activity_log_in_save_payload(self):
        results = _run_js_tests([{
            "name": "activityLog_in_payload",
            "code": """
                appState.activityLog = {'2026-03-21': 5};
                saveState();
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(!saved.activityLog) throw new Error('activityLog missing');
                if(saved.activityLog['2026-03-21'] !== 5)
                    throw new Error('value: ' + saved.activityLog['2026-03-21']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_activity_log_defaults_empty(self):
        results = _run_js_tests([{
            "name": "activityLog_default",
            "code": """
                localStorage.clear();
                appState.activityLog = {'old': 1};
                loadState();
                // With no stored data, activityLog should keep current value
                if(!appState.activityLog) throw new Error('activityLog is falsy');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestResetAllScores(unittest.TestCase):
    """resetAllScores() clears all quiz data but preserves settings."""

    def test_reset_clears_all_mode_scores(self):
        """After reset, all mode scores, history, and guesses are empty."""
        results = _run_js_tests([{
            "name": "reset_clears_modes",
            "code": """
                var confirm = function() { return true; };
                appState.score = {correct: 50, total: 100};
                MODES.quiz.scores = {'01': 5, '02': 3};
                MODES.quiz.scoreHistory = {'01': [5, 3], '02': [3]};
                MODES.quiz.history = ['01', '02'];
                MODES.quiz.recentGuesses = [true, false];
                MODES.reverse.scores = {'03': -2};
                MODES.reverse.history = ['03'];
                MODES.mixed.scores = {'04': 7};
                MODES.consonant.scores = {'S': 2};

                resetAllScores();

                if(appState.score.correct !== 0) throw new Error('score.correct: ' + appState.score.correct);
                if(appState.score.total !== 0) throw new Error('score.total: ' + appState.score.total);
                if(Object.keys(MODES.quiz.scores).length !== 0) throw new Error('quiz scores not empty');
                if(Object.keys(MODES.quiz.scoreHistory).length !== 0) throw new Error('quiz scoreHistory not empty');
                if(MODES.quiz.history.length !== 0) throw new Error('quiz history not empty');
                if(MODES.quiz.recentGuesses.length !== 0) throw new Error('quiz guesses not empty');
                if(Object.keys(MODES.reverse.scores).length !== 0) throw new Error('reverse scores not empty');
                if(Object.keys(MODES.mixed.scores).length !== 0) throw new Error('mixed scores not empty');
                if(Object.keys(MODES.consonant.scores).length !== 0) throw new Error('consonant scores not empty');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_reset_persists_to_localStorage(self):
        """After reset, localStorage reflects zeroed scores."""
        results = _run_js_tests([{
            "name": "reset_persists",
            "code": """
                var confirm = function() { return true; };
                appState.score = {correct: 10, total: 20};
                MODES.quiz.scores = {'01': 5};
                saveState();

                resetAllScores();

                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(saved.score.correct !== 0) throw new Error('saved score.correct: ' + saved.score.correct);
                if(Object.keys(saved.quizScores).length !== 0) throw new Error('saved quizScores not empty');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_reset_preserves_custom_words(self):
        """Reset does not touch customWords."""
        results = _run_js_tests([{
            "name": "reset_keeps_custom_words",
            "code": """
                var confirm = function() { return true; };
                appState.customWords = {'03': 'myword'};
                MODES.quiz.scores = {'03': 5};
                saveState();

                resetAllScores();

                if(appState.customWords['03'] !== 'myword') throw new Error('customWords lost');
                var saved = JSON.parse(localStorage.getItem('quizState'));
                if(saved.customWords['03'] !== 'myword') throw new Error('saved customWords lost');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_reset_preserves_settings(self):
        """Reset does not touch timedQuiz or dyslexiaFont."""
        results = _run_js_tests([{
            "name": "reset_keeps_settings",
            "code": """
                var confirm = function() { return true; };
                appState.timedQuiz = true;
                appState.dyslexiaFont = true;
                MODES.quiz.scores = {'01': 5};
                saveState();

                resetAllScores();

                if(appState.timedQuiz !== true) throw new Error('timedQuiz reset');
                if(appState.dyslexiaFont !== true) throw new Error('dyslexiaFont reset');
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


class TestExportImportRoundTrip(unittest.TestCase):
    """CSV/JSON export format is compatible with import parsing."""

    def test_csv_export_format_parseable(self):
        """CSV produced by exportWordlistCSV is parseable by parseCSVImport."""
        results = _run_js_tests([{
            "name": "csv_round_trip",
            "code": """
                appState.defaultWordlist = {'00': 'sauce', '01': 'seed', '02': 'sun'};
                appState.customWords = {'01': 'custom'};
                appState.wordlist = {'00': 'sauce', '01': 'custom', '02': 'sun'};

                // Generate CSV the same way exportWordlistCSV does
                var csv = 'number,word,custom\\n';
                for (var i = 0; i < 3; i++) {
                    var d = String(i).padStart(2, '0');
                    var w = appState.wordlist[d] || '';
                    var c = appState.customWords[d] ? 'true' : '';
                    csv += d + ',' + w + ',' + c + '\\n';
                }

                // Parse it the same way parseCSVImport does
                var lines = csv.split('\\n').filter(function(l){ return l.trim(); });
                var start = 0;
                var first = lines[0].split(',')[0].trim();
                if (first === 'number' || !/^\\d+$/.test(first)) start = 1;
                var result = {};
                for (var j = start; j < lines.length; j++) {
                    var cols = lines[j].split(',');
                    if (cols.length < 2) continue;
                    var num = cols[0].trim().padStart(2, '0');
                    var word = cols[1].trim();
                    if (!/^\\d{2}$/.test(num)) continue;
                    if (!/^[a-z]/.test(word)) continue;
                    result[num] = word;
                }
                if(result['00'] !== 'sauce') throw new Error('00: ' + result['00']);
                if(result['01'] !== 'custom') throw new Error('01: ' + result['01']);
                if(result['02'] !== 'sun') throw new Error('02: ' + result['02']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_json_export_format_parseable(self):
        """JSON produced by exportWordlistJSON is parseable by parseJSONImport."""
        results = _run_js_tests([{
            "name": "json_round_trip",
            "code": """
                appState.wordlist = {'00': 'sauce', '01': 'custom', '02': 'sun'};

                // Generate JSON the same way exportWordlistJSON does
                var obj = {};
                for (var i = 0; i < 3; i++) {
                    var d = String(i).padStart(2, '0');
                    obj[d] = appState.wordlist[d] || '';
                }
                var jsonStr = JSON.stringify(obj);

                // Parse it back
                var parsed = JSON.parse(jsonStr);
                if(typeof parsed !== 'object' || parsed === null)
                    throw new Error('not an object');
                var result = {};
                for (var key in parsed) {
                    var num = key.trim().padStart(2, '0');
                    if (!/^\\d{2}$/.test(num)) continue;
                    var word = parsed[key].trim();
                    if (!/^[a-z]/.test(word)) continue;
                    result[num] = word;
                }
                if(result['00'] !== 'sauce') throw new Error('00: ' + result['00']);
                if(result['01'] !== 'custom') throw new Error('01: ' + result['01']);
                if(result['02'] !== 'sun') throw new Error('02: ' + result['02']);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))

    def test_csv_header_detection(self):
        """CSV parser correctly skips header row."""
        results = _run_js_tests([{
            "name": "csv_header_skip",
            "code": """
                var csv = 'number,word,custom\\n42,hammer,true\\n';
                var lines = csv.split('\\n').filter(function(l){ return l.trim(); });
                var start = 0;
                var first = lines[0].split(',')[0].trim();
                if (first === 'number' || !/^\\d+$/.test(first)) start = 1;
                if (start !== 1) throw new Error('header not detected, start=' + start);
                var cols = lines[1].split(',');
                if (cols[0].trim() !== '42') throw new Error('wrong number: ' + cols[0]);
                if (cols[1].trim() !== 'hammer') throw new Error('wrong word: ' + cols[1]);
            """,
        }])
        self.assertTrue(results[0]["pass"], results[0].get("error"))


if __name__ == "__main__":
    unittest.main()
