/* ================================================================== */
/*  CSRF helper                                                        */
/* ================================================================== */
function getCookie(name){
  var c = document.cookie || '';
  var v = c.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

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
