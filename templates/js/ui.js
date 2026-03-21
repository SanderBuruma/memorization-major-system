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
