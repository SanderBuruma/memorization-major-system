"""Shared Node.js test harness for running JS tests from the esbuild bundle.

Provides a localStorage mock, minimal DOM stubs, and a generic test runner
used by test_persistence.py, test_dyslexia_font.py, and test_tutorial.py.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JS_PATH = str(PROJECT_ROOT / "static" / "js" / "app.js")

# Superset harness: includes body class tracking, window/performance stubs,
# and setInterval/clearInterval needed by various test suites.
NODE_HARNESS = r"""
// -- localStorage mock --
var _store = {};
var localStorage = {
  getItem: function(k){ return _store[k] || null; },
  setItem: function(k,v){ _store[k] = v; },
  removeItem: function(k){ delete _store[k]; },
  clear: function(){ _store = {}; }
};

// -- minimal DOM stubs --
var _bodyClasses = new Set();
var _stubEl = {textContent:'',value:'',innerHTML:'',disabled:false,className:'',
  style:{},
  focus:function(){},appendChild:function(){},addEventListener:function(){},
  classList:{
    add:function(c){ _bodyClasses.add(c); },
    remove:function(c){ _bodyClasses.delete(c); },
    toggle:function(c, force){
      if(force) _bodyClasses.add(c); else _bodyClasses.delete(c);
    },
    contains:function(c){ return _bodyClasses.has(c); }
  },
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
  cookie: '',
  body: _stubEl
};
var window = {};
var performance = {now: function(){return 0;}};
var fetch = function(){ return Promise.resolve({ok:true,json:function(){return Promise.resolve({})}}); };
function clearTimeout(){}
function setTimeout(){ return 0; }
function setInterval(){ return 0; }
function clearInterval(){}

// -- paste the app bundle --
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


def extract_js():
    """Read and unwrap the esbuild IIFE bundle for use in Node test scope."""
    with open(JS_PATH, encoding="utf-8") as f:
        js = f.read()
    js = js.replace('"use strict";\n(() => {\n', "")
    js = js.replace("\n})();\n", "\n")
    js = re.sub(r"Object\.assign\(window,\s*\{[^}]*\}\);", "", js)
    js = re.sub(r"\n\s*init\(\);\n", "\n", js)
    js = js.replace("\nlet ", "\nvar ").replace("\nconst ", "\nvar ")
    return js


def run_js_tests(tests):
    """Run a list of {name, code} JS test snippets in Node and return results."""
    js_code = extract_js()
    harness = NODE_HARNESS.replace("%JSCODE%", js_code)

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
