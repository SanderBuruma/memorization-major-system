import { appState, rebuildWordlist } from './state';
import { getCookie, loadState, applyState, saveState } from './persistence';
import { toggleTheme, updateToggleIcon } from './theme';
import { startQuiz, checkQuiz, skipQuiz, startReverse, checkReverse, skipReverse,
         startMixed, checkMixed, skipMixed, startCon, checkCon, skipCon } from './quiz';
import { renderGrid, renderRef, showSection, showQuizNav, updateScore, updateMasteryColors, startGridQuiz, checkGridQuiz } from './ui';
import { renderProfile } from './profile';
import { ServerState } from './types';

function updateAuthUI(username: string | null): void {
  const el = document.getElementById('auth-status');
  if (!el) return;
  if (username) {
    el.innerHTML = `<button class="arrow-pill arrow-pill-left" style="font-weight:700;color:var(--text-primary);font-size:1em;font-family:inherit;cursor:pointer" onclick="showSection('profile')">${username}</button> <form method="post" action="/logout/" style="display:inline"><input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}"><button type="submit" class="auth-link">logout</button></form>`;
  } else {
    el.innerHTML = '<a href="/login/" class="auth-link">login</a>';
  }
}

function buildConMap(): void {
  appState.conKeys = [];
  appState.conMap = {};
  for (const digit of Object.keys(appState.mapping)) {
    appState.mapping[digit].split(', ').forEach((consonant) => {
      appState.conKeys.push(consonant);
      appState.conMap[consonant] = digit;
    });
  }
}

async function init(): Promise<void> {
  const cachedWl = localStorage.getItem('wordlist');
  const cachedMap = localStorage.getItem('mapping');
  if (cachedWl && cachedMap) {
    appState.defaultWordlist = JSON.parse(cachedWl);
    appState.mapping = JSON.parse(cachedMap);
  }

  loadState();
  rebuildWordlist();
  buildConMap();
  renderGrid();
  renderRef();
  updateScore();
  updateMasteryColors();

  try {
    const results = await Promise.all([
      fetch('/api/wordlist'), fetch('/api/mapping'), fetch('/api/state'),
    ]);
    const [wlRes, mapRes, stateRes] = results;
    if (wlRes.ok) {
      appState.defaultWordlist = await wlRes.json();
      localStorage.setItem('wordlist', JSON.stringify(appState.defaultWordlist));
      rebuildWordlist();
    }
    if (mapRes.ok) {
      appState.mapping = await mapRes.json();
      localStorage.setItem('mapping', JSON.stringify(appState.mapping));
      buildConMap();
    }
    if (stateRes.ok) {
      const serverState: ServerState = await stateRes.json();
      if (serverState.user || (serverState.score && serverState.score.total > appState.score.total)) {
        applyState(serverState as unknown as Record<string, unknown>);
      }
      updateAuthUI(serverState.user);
      if (serverState.theme && !localStorage.getItem('theme')) {
        document.documentElement.setAttribute('data-theme', serverState.theme);
        localStorage.setItem('theme', serverState.theme);
        updateToggleIcon();
      }
    }
    renderGrid();
    renderRef();
    updateMasteryColors();
  } catch {}
}

/* Expose globals for HTML onclick handlers */
Object.assign(window, {
  showSection, showQuizNav, toggleTheme,
  checkQuiz, skipQuiz, checkReverse, skipReverse,
  checkMixed, skipMixed, checkCon, skipCon,
  startGridQuiz, checkGridQuiz,
});

/* Boot */
init();
