/* ================================================================== */
/*  CSRF helper                                                        */
/* ================================================================== */
function getCookie(name){
  var c = document.cookie || '';
  var v = c.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

/* ================================================================== */
/*  Theme toggle                                                       */
/* ================================================================== */
var sunSVG = '<svg viewBox="0 0 24 24"><path d="M12 7a5 5 0 100 10 5 5 0 000-10zm0-3a1 1 0 01-1-1V1a1 1 0 112 0v2a1 1 0 01-1 1zm0 18a1 1 0 01-1-1v-2a1 1 0 112 0v2a1 1 0 01-1 1zm9-9a1 1 0 01-1 1h-2a1 1 0 110-2h2a1 1 0 011 1zM5 12a1 1 0 01-1 1H2a1 1 0 110-2h2a1 1 0 011 1zm13.07-5.66a1 1 0 01-.71-.29l-1.41-1.42a1 1 0 111.41-1.41l1.42 1.41a1 1 0 01-.71 1.71zM7.05 19.07a1 1 0 01-.71-.29l-1.41-1.42a1 1 0 111.41-1.41l1.42 1.41a1 1 0 01-.71 1.71zM19.07 19.07a1 1 0 01-.71-.29 1 1 0 010-1.42l1.42-1.41a1 1 0 111.41 1.41l-1.41 1.42a1 1 0 01-.71.29zM7.05 7.05a1 1 0 01-.71-.29 1 1 0 010-1.42l1.42-1.41a1 1 0 011.41 1.41L7.76 6.76a1 1 0 01-.71.29z"/></svg>';
var moonSVG = '<svg viewBox="0 0 24 24"><path d="M12.3 4.9a7.45 7.45 0 006.8 6.8 7.5 7.5 0 01-9.5 5.8A7.5 7.5 0 0112.3 4.9M12 2a10 10 0 100 20 10 10 0 000-20z"/></svg>';

function toggleTheme(){
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateToggleIcon();
  saveState();
}

function updateToggleIcon(){
  var btn = document.getElementById('theme-toggle');
  var isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  btn.innerHTML = isDark ? sunSVG : moonSVG;
}

var savedTheme = localStorage.getItem('theme');
if(savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);
updateToggleIcon();

/* ================================================================== */
/*  State                                                              */
/* ================================================================== */
var S = {
  wordlist: {},
  defaultWordlist: {},
  customWords: {},
  mapping: {},
  keys: [],
  score: {correct: 0, total: 0},
  conKeys: [],
  conMap: {}
};

/* ================================================================== */
/*  Quiz mode configs                                                  */
/* ================================================================== */
var MODES = {
  quiz: {
    promptId: 'quiz-prompt', inputId: 'quiz-input',
    feedbackId: 'quiz-feedback', submitId: 'quiz-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'quizScores', persistHistory: 'quizHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){ return {digits: k, word: S.wordlist[k]}; },
    getPrompt: function(item){ return item.digits; },
    getAnswer: function(item){ return item.word.toLowerCase(); },
    normalize: function(raw){ return raw.toLowerCase(); },
    formatCorrect: function(item){ return '"' + item.word.toLowerCase() + '"'; },
    placeholder: 'type the noun...',
    historyKey: function(item){ return item.digits; }
  },
  reverse: {
    promptId: 'rev-prompt', inputId: 'rev-input',
    feedbackId: 'rev-feedback', submitId: 'rev-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'reverseScores', persistHistory: 'reverseHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){ return {digits: k, word: S.wordlist[k]}; },
    getPrompt: function(item){ return item.word; },
    getAnswer: function(item){ return item.digits; },
    normalize: function(raw){ return raw.padStart(2, '0'); },
    formatCorrect: function(item){ return item.digits; },
    placeholder: 'type the number...',
    historyKey: function(item){ return item.digits; }
  },
  mixed: {
    promptId: 'mix-prompt', inputId: 'mix-input',
    feedbackId: 'mix-feedback', submitId: 'mix-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'mixedScores', persistHistory: 'mixedHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){
      var mode = Math.random() < 0.5 ? 'forward' : 'reverse';
      return {digits: k, word: S.wordlist[k], mode: mode};
    },
    getPrompt: function(item){ return item.mode === 'forward' ? item.digits : item.word; },
    getAnswer: function(item){ return item.mode === 'forward' ? item.word.toLowerCase() : item.digits; },
    normalize: function(raw, item){ return item.mode === 'forward' ? raw.toLowerCase() : raw.padStart(2, '0'); },
    formatCorrect: function(item){ return item.mode === 'forward' ? '"' + item.word.toLowerCase() + '"' : item.digits; },
    placeholder: 'type your answer...',
    historyKey: function(item){ return item.digits; },
    startExtra: function(item, inp){
      if(item.mode === 'forward'){
        inp.placeholder = 'type the noun...';
        inp.maxLength = 524288;
      } else {
        inp.placeholder = 'type the number...';
        inp.maxLength = '2';
      }
    }
  },
  consonant: {
    promptId: 'con-prompt', inputId: 'con-input',
    feedbackId: 'con-feedback', submitId: 'con-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'conScores', persistHistory: 'conHistory',
    allKeys: function(){ return S.conKeys; },
    pickItem: function(k){ return {key: k}; },
    getPrompt: function(item){ var d = {C: 'C (hard)', G: 'G (hard)'}; return d[item.key] || item.key; },
    getAnswer: function(item){ return S.conMap[item.key]; },
    normalize: function(raw){ return raw; },
    formatCorrect: function(item){ return S.conMap[item.key]; },
    placeholder: 'type the digit...',
    historyKey: function(item){ return item.key; }
  }
};

/* ================================================================== */
/*  Persistence field manifest                                         */
/* ================================================================== */
var STATE_FIELDS = [
  {key: 'score', get: function(){ return S.score; }, set: function(v){ S.score = v || {correct: 0, total: 0}; }},
  {key: 'customWords', get: function(){ return S.customWords; }, set: function(v){ S.customWords = v || {}; }}
];
Object.keys(MODES).forEach(function(name){
  var m = MODES[name];
  STATE_FIELDS.push(
    {key: m.persistScores, get: function(){ return m.scores; }, set: function(v){ m.scores = v || {}; }},
    {key: m.persistHistory, get: function(){ return m.history; }, set: function(v){ m.history = v || []; }}
  );
});

/* ================================================================== */
/*  Persistence                                                        */
/* ================================================================== */
var _syncTimer = null;
function saveState(){
  var state = {};
  STATE_FIELDS.forEach(function(f){ state[f.key] = f.get(); });
  state.theme = document.documentElement.getAttribute('data-theme') || 'dark';
  localStorage.setItem('quizState', JSON.stringify(state));
  clearTimeout(_syncTimer);
  _syncTimer = setTimeout(function(){
    fetch('/api/state', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
      body: JSON.stringify(state)
    }).catch(function(){});
  }, 1000);
  updateMasteryColors();
}

function loadState(){
  try {
    var s = JSON.parse(localStorage.getItem('quizState'));
    if(!s) return;
    if(s.quizPool || s.quizMastered){
      localStorage.removeItem('quizState');
      return;
    }
    STATE_FIELDS.forEach(function(f){ f.set(s[f.key]); });
  } catch(e){}
}

function applyState(s){
  STATE_FIELDS.forEach(function(f){ f.set(s[f.key]); });
  rebuildWordlist();
  saveState();
  updateScore();
  renderGrid();
}

/* ================================================================== */
/*  Auth UI                                                            */
/* ================================================================== */
function updateAuthUI(username){
  var el = document.getElementById('auth-status');
  if(!el) return;
  if(username){
    el.innerHTML = '<button class="arrow-pill arrow-pill-left" style="font-weight:700;color:var(--text-primary);font-size:1em;font-family:inherit;cursor:pointer" onclick="showSection(\'profile\')">' + username + '</button> <form method="post" action="/logout/" style="display:inline"><input type="hidden" name="csrfmiddlewaretoken" value="' + getCookie('csrftoken') + '"><button type="submit" class="auth-link">logout</button></form>';
  } else {
    el.innerHTML = '<a href="/login/" class="auth-link">login</a>';
  }
}

/* ================================================================== */
/*  Init                                                               */
/* ================================================================== */
function buildConMap(){
  S.conKeys = []; S.conMap = {};
  for(var digit in S.mapping){
    S.mapping[digit].split(', ').forEach(function(c){
      S.conKeys.push(c);
      S.conMap[c] = digit;
    });
  }
}

async function init(){
  var cachedWl = localStorage.getItem('wordlist');
  var cachedMap = localStorage.getItem('mapping');
  if(cachedWl && cachedMap){
    S.defaultWordlist = JSON.parse(cachedWl);
    S.mapping = JSON.parse(cachedMap);
  }

  loadState();
  rebuildWordlist();
  buildConMap();
  renderGrid();
  renderRef();
  updateScore();
  updateMasteryColors();

  try {
    var results = await Promise.all([
      fetch('/api/wordlist'), fetch('/api/mapping'), fetch('/api/state')
    ]);
    var wlRes = results[0], mapRes = results[1], stateRes = results[2];
    if(wlRes.ok){
      S.defaultWordlist = await wlRes.json();
      localStorage.setItem('wordlist', JSON.stringify(S.defaultWordlist));
      rebuildWordlist();
    }
    if(mapRes.ok){
      S.mapping = await mapRes.json();
      localStorage.setItem('mapping', JSON.stringify(S.mapping));
      buildConMap();
    }
    if(stateRes.ok){
      var serverState = await stateRes.json();
      if(serverState.user || (serverState.score && serverState.score.total > S.score.total)){
        applyState(serverState);
      }
      updateAuthUI(serverState.user);
      if(serverState.theme && !localStorage.getItem('theme')){
        document.documentElement.setAttribute('data-theme', serverState.theme);
        localStorage.setItem('theme', serverState.theme);
        updateToggleIcon();
      }
    }
    renderGrid();
    renderRef();
    updateMasteryColors();
  } catch(e){}
}

/* ================================================================== */
/*  Wordlist merge                                                     */
/* ================================================================== */
function rebuildWordlist(){
  S.wordlist = {};
  for(var k in S.defaultWordlist) S.wordlist[k] = S.defaultWordlist[k];
  for(var k in S.customWords) S.wordlist[k] = S.customWords[k];
  S.keys = Object.keys(S.wordlist).sort();
}

/* ================================================================== */
/*  Grid                                                               */
/* ================================================================== */
function renderGrid(){
  var g = document.getElementById('grid');
  g.innerHTML = '';
  for(var i = 0; i < 100; i++){
    var d = String(i).padStart(2, '0');
    var w = S.wordlist[d] || '???';
    var c = document.createElement('div');
    c.className = 'grid-cell';
    c.setAttribute('data-key', d);
    var isCustom = S.customWords[d] ? '<span class="custom-marker">*</span>' : '';
    c.innerHTML = '<div class="number">' + d + isCustom + '</div>';
    var inp = document.createElement('input');
    inp.className = 'word-input';
    inp.value = w;
    inp.setAttribute('data-key', d);
    inp.addEventListener('keydown', function(e){
      if(e.key === 'Enter') this.blur();
    });
    inp.addEventListener('input', function(){
      var key = this.getAttribute('data-key');
      var val = this.value.trim();
      if(val && /^[a-z]/.test(val) && val !== S.defaultWordlist[key]){
        S.customWords[key] = val;
      } else if(!val || val === S.defaultWordlist[key]){
        delete S.customWords[key];
      }
      rebuildWordlist();
      saveState();
    });
    inp.addEventListener('blur', function(){
      var key = this.getAttribute('data-key');
      var val = this.value.trim();
      if(!val || !/^[a-z]/.test(val)){
        delete S.customWords[key];
        rebuildWordlist();
        this.value = S.wordlist[key] || '';
        saveState();
      }
      var numEl = this.parentNode.querySelector('.number');
      var marker = numEl.querySelector('.custom-marker');
      if(S.customWords[key] && !marker){
        numEl.insertAdjacentHTML('beforeend', '<span class="custom-marker">*</span>');
      } else if(!S.customWords[key] && marker){
        marker.remove();
      }
    });
    c.addEventListener('click', function(){ this.querySelector('.word-input').focus(); });
    c.appendChild(inp);
    g.appendChild(c);
  }
}

/* ================================================================== */
/*  Reference table                                                    */
/* ================================================================== */
function renderRef(){
  var b = document.getElementById('ref-body');
  b.innerHTML = '';
  for(var d = 0; d <= 9; d++){
    var tr = document.createElement('tr');
    tr.innerHTML = '<td><strong>' + d + '</strong></td><td>' + S.mapping[String(d)] + '</td>';
    b.appendChild(tr);
  }
}

/* ================================================================== */
/*  Section switching                                                  */
/* ================================================================== */
var quizSections = ['quiz', 'reverse', 'mixed', 'consonant'];

function showSection(name){
  document.querySelectorAll('.section').forEach(function(s){ s.classList.remove('active'); });
  document.getElementById('section-' + name).classList.add('active');
  document.querySelectorAll('.topbar-nav button').forEach(function(b){ b.classList.remove('active'); });
  var isQuiz = quizSections.indexOf(name) !== -1;
  if(isQuiz){
    document.querySelector('.topbar-nav [data-section="quiz-nav"]').classList.add('active');
    document.getElementById('subnav').classList.add('visible');
  } else {
    var navBtn = document.querySelector('.topbar-nav [data-section="' + name + '"]');
    if(navBtn) navBtn.classList.add('active');
    document.getElementById('subnav').classList.remove('visible');
  }
  document.querySelectorAll('.subnav button').forEach(function(b){ b.classList.remove('active'); });
  var sub = document.querySelector('.subnav [data-section="' + name + '"]');
  if(sub) sub.classList.add('active');
  if(name === 'quiz') startQuiz();
  if(name === 'reverse') startReverse();
  if(name === 'mixed') startMixed();
  if(name === 'consonant') startCon();
  if(name === 'profile') renderProfile();
}

function showQuizNav(){
  var sub = document.getElementById('subnav');
  if(sub.classList.contains('visible')){
    var active = sub.querySelector('button.active');
    if(active) showSection(active.getAttribute('data-section'));
    else showSection('quiz');
  } else {
    showSection('quiz');
  }
}

/* ================================================================== */
/*  Pick next word (score-based with cooldown)                         */
/* ================================================================== */
function pickNext(scores, history, allKeys){
  var eligible = allKeys.filter(function(k){ return history.indexOf(k) === -1; });
  if(eligible.length === 0) eligible = allKeys.slice();
  var minScore = Infinity;
  for(var i = 0; i < eligible.length; i++){
    var s = scores[eligible[i]] || 0;
    if(s < minScore) minScore = s;
  }
  var candidates = eligible.filter(function(k){ return (scores[k] || 0) === minScore; });
  return candidates[Math.floor(Math.random() * candidates.length)];
}

/* ================================================================== */
/*  Generic quiz engine                                                */
/* ================================================================== */
function startMode(m){
  clearTimeout(m.timer);
  var pick = pickNext(m.scores, m.history, m.allKeys());
  if(!pick) return;
  var item = m.pickItem(pick);
  m.current = item;
  document.getElementById(m.promptId).textContent = m.getPrompt(item);
  var inp = document.getElementById(m.inputId);
  inp.value = '';
  inp.disabled = false;
  inp.placeholder = m.placeholder;
  document.getElementById(m.submitId).disabled = false;
  document.getElementById(m.feedbackId).className = 'feedback empty';
  document.getElementById(m.feedbackId).textContent = '';
  if(m.startExtra) m.startExtra(item, inp);
  inp.focus();
}

function checkMode(m){
  if(!m.current) return;
  var inp = document.getElementById(m.inputId);
  var raw = inp.value.trim();
  if(!raw) return;
  inp.disabled = true;
  document.getElementById(m.submitId).disabled = true;

  var answer = m.normalize(raw, m.current);
  var correct = m.getAnswer(m.current);
  var key = m.historyKey(m.current);
  S.score.total++;
  var fb = document.getElementById(m.feedbackId);
  if(answer === correct){
    S.score.correct++;
    m.scores[key] = (m.scores[key] || 0) + 1;
    fb.className = 'feedback correct';
    fb.textContent = 'Correct!';
  } else {
    m.scores[key] = (m.scores[key] || 0) - 1;
    fb.className = 'feedback incorrect';
    fb.textContent = 'Incorrect. Answer: ' + m.formatCorrect(m.current);
  }
  m.history.push(key);
  if(m.history.length > 10) m.history.shift();
  updateScore();
  saveState();
  m.timer = setTimeout(function(){ startMode(m); }, 1800);
}

function skipMode(m){
  if(m.current){
    m.history.push(m.historyKey(m.current));
    if(m.history.length > 10) m.history.shift();
    saveState();
  }
  startMode(m);
}

/* Thin wrappers for HTML onclick handlers */
function startQuiz(){ startMode(MODES.quiz); }
function checkQuiz(){ checkMode(MODES.quiz); }
function skipQuiz(){ skipMode(MODES.quiz); }
function startReverse(){ startMode(MODES.reverse); }
function checkReverse(){ checkMode(MODES.reverse); }
function skipReverse(){ skipMode(MODES.reverse); }
function startMixed(){ startMode(MODES.mixed); }
function checkMixed(){ checkMode(MODES.mixed); }
function skipMixed(){ skipMode(MODES.mixed); }
function startCon(){ startMode(MODES.consonant); }
function checkCon(){ checkMode(MODES.consonant); }
function skipCon(){ skipMode(MODES.consonant); }

/* ================================================================== */
/*  Score                                                              */
/* ================================================================== */
function updateScore(){
  var pct = S.score.total > 0 ? Math.round(S.score.correct / S.score.total * 100) : 0;
  document.getElementById('score-text').textContent =
    S.score.correct + ' / ' + S.score.total + ' (' + pct + '%)';
}

/* ================================================================== */
/*  Keyboard: Enter = submit                                           */
/* ================================================================== */
document.getElementById('quiz-input').addEventListener('keydown', function(e){
  if(e.key === 'Enter') checkQuiz();
});
document.getElementById('rev-input').addEventListener('keydown', function(e){
  if(e.key === 'Enter') checkReverse();
});
document.getElementById('mix-input').addEventListener('keydown', function(e){
  if(e.key === 'Enter') checkMixed();
});
document.getElementById('con-input').addEventListener('keydown', function(e){
  if(e.key === 'Enter') checkCon();
});

/* ================================================================== */
/*  Translate: number string -> nouns                                  */
/* ================================================================== */
document.getElementById('translate-input').addEventListener('input', function(){
  var raw = this.value.replace(/[^0-9]/g, '');
  var out = document.getElementById('translate-output');
  out.innerHTML = '';
  if(!raw) return;
  for(var i = 0; i < raw.length; i += 2){
    var chunk = raw.substr(i, 2);
    var chip = document.createElement('div');
    if(chunk.length === 2){
      var w = S.wordlist[chunk] || '???';
      chip.className = 'translate-chip';
      chip.innerHTML = '<div class="number">' + chunk + '</div><div class="word">' + w + '</div>';
    } else {
      chip.className = 'translate-chip odd';
      chip.textContent = chunk + '?';
    }
    out.appendChild(chip);
  }
});

/* ================================================================== */
/*  Mastery colors                                                     */
/* ================================================================== */
function updateMasteryColors(){
  if(!S.keys.length) return;
  var cells = document.querySelectorAll('.grid-cell');
  cells.forEach(function(cell){
    var key = cell.getAttribute('data-key');
    if(!key) return;
    var total = (MODES.quiz.scores[key] || 0) + (MODES.reverse.scores[key] || 0) + (MODES.mixed.scores[key] || 0);
    var cls;
    if(total <= -3) cls = 'mastery-0';
    else if(total < 0) cls = 'mastery-1';
    else if(total <= 3) cls = 'mastery-2';
    else if(total <= 8) cls = 'mastery-3';
    else cls = 'mastery-4';
    cell.className = cell.className.replace(/mastery-\d/g, '').trim() + ' ' + cls;
  });
}

/* ================================================================== */
/*  Profile stats                                                      */
/* ================================================================== */
function renderProfile(){
  var el = document.getElementById('profile-content');
  var allKeys = S.keys.length ? S.keys : [];
  var combined = allKeys.map(function(k){
    return (MODES.quiz.scores[k] || 0) + (MODES.reverse.scores[k] || 0) + (MODES.mixed.scores[k] || 0);
  });
  var n = allKeys.length || 1;
  var qCov = Math.round(allKeys.filter(function(k){ return MODES.quiz.scores[k] !== undefined; }).length / n * 100);
  var rCov = Math.round(allKeys.filter(function(k){ return MODES.reverse.scores[k] !== undefined; }).length / n * 100);
  var mCov = Math.round(allKeys.filter(function(k){ return MODES.mixed.scores[k] !== undefined; }).length / n * 100);
  var cAtt = S.conKeys.filter(function(k){ return MODES.consonant.scores[k] !== undefined; }).length;
  var cCov = S.conKeys.length ? Math.round(cAtt / S.conKeys.length * 100) : 0;
  var mast = [0, 0, 0, 0, 0];
  combined.forEach(function(s){
    if(s <= -3) mast[0]++;
    else if(s < 0) mast[1]++;
    else if(s <= 3) mast[2]++;
    else if(s <= 8) mast[3]++;
    else mast[4]++;
  });
  var sorted = combined.slice().sort(function(a, b){ return a - b; });
  var sMin = sorted[0] || 0, sMax = sorted[sorted.length - 1] || 0;
  var sMean = combined.length ? (combined.reduce(function(a, b){ return a + b; }, 0) / combined.length).toFixed(1) : 0;
  var sMed = 0;
  if(sorted.length){
    var mid = Math.floor(sorted.length / 2);
    sMed = sorted.length % 2 ? sorted[mid] : ((sorted[mid - 1] + sorted[mid]) / 2);
  }
  var cScores = S.conKeys.map(function(k){ return MODES.consonant.scores[k] || 0; }).sort(function(a, b){ return a - b; });
  var cMed = 0;
  if(cScores.length){
    var cm = Math.floor(cScores.length / 2);
    cMed = cScores.length % 2 ? cScores[cm] : ((cScores[cm - 1] + cScores[cm]) / 2);
  }
  var pct = S.score.total > 0 ? (S.score.correct / S.score.total * 100).toFixed(1) : 0;
  var labels = ['Struggling', 'Weak', 'Learning', 'Good', 'Mastered'];
  var mastMax = Math.max.apply(null, mast) || 1;
  var html = '<div class="card"><h2>Overall</h2>'
    + '<div class="stat-row"><span class="label">Total attempts</span><span class="value">' + S.score.total + '</span></div>'
    + '<div class="stat-row"><span class="label">Accuracy</span><span class="value">' + pct + '%</span></div>'
    + '</div>'
    + '<div class="card"><h2>Coverage by mode</h2><div class="cov-grid">'
    + '<div class="cov-item"><div class="cov-pct">' + qCov + '%</div><div class="cov-label"># &rarr; Word</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + rCov + '%</div><div class="cov-label">Word &rarr; #</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + mCov + '%</div><div class="cov-label">Mixed</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + cCov + '%</div><div class="cov-label">Sound &rarr; #</div></div>'
    + '</div></div>'
    + '<div class="card"><h2>Mastery distribution</h2>';
  for(var i = 0; i < 5; i++){
    var w = Math.round(mast[i] / mastMax * 100);
    html += '<div class="bar-row m' + i + '"><span class="bar-label">' + labels[i] + '</span>'
      + '<div class="bar-track"><div class="bar-fill" style="width:' + w + '%"></div></div>'
      + '<span class="bar-count">' + mast[i] + '</span></div>';
  }
  html += '</div>'
    + '<div class="card"><h2>Combined score</h2>'
    + '<div class="stat-row"><span class="label">Median</span><span class="value">' + sMed + '</span></div>'
    + '<div class="stat-row"><span class="label">Mean</span><span class="value">' + sMean + '</span></div>'
    + '<div class="stat-row"><span class="label">Min</span><span class="value">' + sMin + '</span></div>'
    + '<div class="stat-row"><span class="label">Max</span><span class="value">' + sMax + '</span></div>'
    + '</div>'
    + '<div class="card"><h2>Consonant sounds</h2>'
    + '<div class="stat-row"><span class="label">Coverage</span><span class="value">' + cCov + '%</span></div>'
    + '<div class="stat-row"><span class="label">Median score</span><span class="value">' + cMed + '</span></div>'
    + '</div>';
  el.innerHTML = html;
}

/* ================================================================== */
/*  Boot                                                               */
/* ================================================================== */
init();
