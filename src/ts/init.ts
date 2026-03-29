import { appState, rebuildWordlist } from './state';
import { getCookie, loadState, applyState, saveState } from './persistence';
import { toggleTheme, setTheme, updateToggleIcon } from './theme';
import { checkQuiz, skipQuiz, checkReverse, skipReverse,
         checkMixed, skipMixed, checkCon, skipCon } from './quiz';
import { renderGrid, renderRef, renderConstantButtons, showSection, showQuizNav, updateMasteryColors, startGridQuiz, checkGridQuiz, toggleTimedQuiz, toggleDyslexiaFont, exportWordlistCSV, exportWordlistJSON, importCSV, importJSON, resetAllScores, setGridScoreMode } from './ui';
import { renderWiki, showWikiCategory, showWikiArticle } from './wiki';
import { nextTutorialStep, prevTutorialStep } from './tutorial';
import { ServerState } from './types';
import { escapeHTML } from './utils';

function updateAuthUI(username: string | null): void {
  const el = document.getElementById('auth-status');
  if (!el) return;
  if (username) {
    const safe = escapeHTML(username);
    const token = escapeHTML(getCookie('csrftoken'));
    el.innerHTML = `<button class="arrow-pill arrow-pill-left" style="font-weight:700;color:var(--text-primary);font-size:1em;font-family:inherit;cursor:pointer" onclick="showSection('profile')">${safe}</button> <form method="post" action="/logout/" style="display:inline"><input type="hidden" name="csrfmiddlewaretoken" value="${token}"><button type="submit" class="auth-link">logout</button></form>`;
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
  if (appState.dyslexiaFont) document.body.classList.add('dyslexia-font');
  rebuildWordlist();
  buildConMap();
  updateToggleIcon();
  const themeSelect = document.getElementById('setting-theme') as HTMLSelectElement | null;
  if (themeSelect) themeSelect.value = document.documentElement.getAttribute('data-theme') ?? 'dark';
  renderGrid();
  renderRef();
  renderConstantButtons();
  const gridModeSelect = document.getElementById('grid-score-mode') as HTMLSelectElement | null;
  if (gridModeSelect) gridModeSelect.value = appState.gridScoreMode;
  updateMasteryColors();
  if (!appState.tutorialSeen) showSection('tutorial');
  else {
    const hash = location.hash.slice(1);
    if (hash && document.getElementById(`section-${hash}`)) showSection(hash, false);
  }

  window.addEventListener('popstate', () => {
    const hash = location.hash.slice(1);
    if (hash && document.getElementById(`section-${hash}`)) showSection(hash, false);
  });

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
  showSection, showQuizNav, toggleTheme, setTheme,
  checkQuiz, skipQuiz, checkReverse, skipReverse,
  checkMixed, skipMixed, checkCon, skipCon,
  startGridQuiz, checkGridQuiz, toggleTimedQuiz, toggleDyslexiaFont,
  nextTutorialStep, prevTutorialStep,
  exportWordlistCSV, exportWordlistJSON,
  importCSV, importJSON,
  renderWiki, showWikiCategory, showWikiArticle,
  resetAllScores,
  setGridScoreMode,
});

/* Boot */
init();
