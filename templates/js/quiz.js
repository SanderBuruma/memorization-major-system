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
