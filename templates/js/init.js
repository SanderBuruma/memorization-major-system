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
/*  Boot                                                               */
/* ================================================================== */
init();
