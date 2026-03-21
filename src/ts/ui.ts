import { appState, MODES, rebuildWordlist } from './state';
import { getCookie, saveState } from './persistence';
import { startQuiz, startReverse, startMixed, startCon,
         checkQuiz, checkReverse, checkMixed, checkCon } from './quiz';
import { renderProfile } from './profile';

/* --- Autocomplete state --- */
const candidateCache: Record<string, string[]> = {};
let activeDropdown: HTMLElement | null = null;
let activeInput: HTMLInputElement | null = null;
let highlightIdx = -1;

function closeDropdown(): void {
  if (activeDropdown) { activeDropdown.remove(); activeDropdown = null; }
  activeInput = null;
  highlightIdx = -1;
}

async function fetchCandidates(digits: string): Promise<string[]> {
  if (candidateCache[digits]) return candidateCache[digits];
  try {
    const res = await fetch(`/api/candidates/${digits}`);
    if (res.ok) {
      const data: string[] = await res.json();
      candidateCache[digits] = data;
      return data;
    }
  } catch {}
  return [];
}

function showDropdown(inp: HTMLInputElement, items: string[]): void {
  closeDropdown();
  if (!items.length) return;
  activeInput = inp;
  const dd = document.createElement('div');
  dd.className = 'ac-dropdown';
  for (let i = 0; i < items.length; i++) {
    const opt = document.createElement('div');
    opt.className = 'ac-option';
    opt.textContent = items[i];
    opt.addEventListener('mousedown', (e) => {
      e.preventDefault();
      selectCandidate(inp, items[i]);
    });
    dd.appendChild(opt);
  }
  inp.parentElement!.appendChild(dd);
  activeDropdown = dd;
  highlightIdx = -1;
}

function updateHighlight(): void {
  if (!activeDropdown) return;
  const opts = activeDropdown.querySelectorAll('.ac-option');
  opts.forEach((o, i) => o.classList.toggle('ac-highlight', i === highlightIdx));
  if (highlightIdx >= 0 && opts[highlightIdx]) {
    opts[highlightIdx].scrollIntoView({ block: 'nearest' });
  }
}

function selectCandidate(inp: HTMLInputElement, word: string): void {
  inp.value = word;
  const key = inp.getAttribute('data-key')!;
  if (word !== appState.defaultWordlist[key]) {
    appState.customWords[key] = word;
  } else {
    delete appState.customWords[key];
  }
  rebuildWordlist();
  saveState();
  closeDropdown();
  inp.blur();
}

function filterDropdown(inp: HTMLInputElement, all: string[]): void {
  const val = inp.value.trim().toLowerCase();
  const filtered = val ? all.filter(w => w.startsWith(val)) : all;
  showDropdown(inp, filtered);
}

export function renderGrid(): void {
  const grid = document.getElementById('grid')!;
  grid.innerHTML = '';
  for (let i = 0; i < 100; i++) {
    const digits = String(i).padStart(2, '0');
    const word = appState.wordlist[digits] ?? '???';
    const cell = document.createElement('div');
    cell.className = 'grid-cell';
    cell.setAttribute('data-key', digits);
    const isCustom = appState.customWords[digits] ? '<span class="custom-marker">*</span>' : '';
    cell.innerHTML = `<div class="number">${digits}${isCustom}</div>`;
    const inp = document.createElement('input');
    inp.className = 'word-input';
    inp.value = word;
    inp.setAttribute('data-key', digits);
    inp.autocomplete = 'off';

    let currentCandidates: string[] = [];

    inp.addEventListener('focus', async function () {
      const key = this.getAttribute('data-key')!;
      currentCandidates = await fetchCandidates(key);
      filterDropdown(this, currentCandidates);
    });

    inp.addEventListener('keydown', function (e) {
      if (activeDropdown && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        const opts = activeDropdown.querySelectorAll('.ac-option');
        if (e.key === 'ArrowDown') highlightIdx = Math.min(highlightIdx + 1, opts.length - 1);
        else highlightIdx = Math.max(highlightIdx - 1, -1);
        updateHighlight();
        return;
      }
      if (e.key === 'Enter') {
        if (activeDropdown && highlightIdx >= 0) {
          e.preventDefault();
          const opts = activeDropdown.querySelectorAll('.ac-option');
          if (opts[highlightIdx]) selectCandidate(this, opts[highlightIdx].textContent!);
          return;
        }
        this.blur();
        return;
      }
      if (e.key === 'Escape') {
        closeDropdown();
        return;
      }
    });

    inp.addEventListener('input', function () {
      const key = this.getAttribute('data-key')!;
      const val = this.value.trim();
      if (val && /^[a-z]/.test(val) && val !== appState.defaultWordlist[key]) {
        appState.customWords[key] = val;
      } else if (!val || val === appState.defaultWordlist[key]) {
        delete appState.customWords[key];
      }
      rebuildWordlist();
      saveState();
      filterDropdown(this, currentCandidates);
    });

    inp.addEventListener('blur', function () {
      closeDropdown();
      const key = this.getAttribute('data-key')!;
      const val = this.value.trim();
      if (!val || !/^[a-z]/.test(val)) {
        delete appState.customWords[key];
        rebuildWordlist();
        this.value = appState.wordlist[key] ?? '';
        saveState();
      }
      const numEl = this.parentNode!.querySelector('.number')!;
      const marker = numEl.querySelector('.custom-marker');
      if (appState.customWords[key] && !marker) {
        numEl.insertAdjacentHTML('beforeend', '<span class="custom-marker">*</span>');
      } else if (!appState.customWords[key] && marker) {
        marker.remove();
      }
    });

    cell.addEventListener('click', function () { this.querySelector<HTMLInputElement>('.word-input')!.focus(); });
    cell.appendChild(inp);
    grid.appendChild(cell);
  }
}

export function renderRef(): void {
  const tableBody = document.getElementById('ref-body')!;
  tableBody.innerHTML = '';
  for (let digit = 0; digit <= 9; digit++) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><strong>${digit}</strong></td><td>${appState.mapping[String(digit)]}</td>`;
    tableBody.appendChild(tr);
  }
}

const quizSections = ['quiz', 'reverse', 'mixed', 'consonant', 'gridquiz'];

export function showSection(name: string): void {
  if (gqTimerInterval) { clearInterval(gqTimerInterval); gqTimerInterval = null; }
  document.querySelectorAll('.section').forEach((section) => { section.classList.remove('active'); });
  document.getElementById(`section-${name}`)!.classList.add('active');
  document.querySelectorAll('.topbar-nav button').forEach((btn) => { btn.classList.remove('active'); });
  const isQuiz = quizSections.includes(name);
  if (isQuiz) {
    document.querySelector('.topbar-nav [data-section="quiz-nav"]')!.classList.add('active');
    document.getElementById('subnav')!.classList.add('visible');
  } else {
    const navBtn = document.querySelector(`.topbar-nav [data-section="${name}"]`);
    if (navBtn) navBtn.classList.add('active');
    document.getElementById('subnav')!.classList.remove('visible');
  }
  document.querySelectorAll('.subnav button').forEach((btn) => { btn.classList.remove('active'); });
  const sub = document.querySelector(`.subnav [data-section="${name}"]`);
  if (sub) sub.classList.add('active');
  const sectionStarters: Record<string, () => void> = {
    quiz: startQuiz, reverse: startReverse, mixed: startMixed,
    consonant: startCon, gridquiz: startGridQuiz, profile: renderProfile, settings: renderSettings,
    tutorial: startTutorial,
  };
  sectionStarters[name]?.();
}

export function showQuizNav(): void {
  const sub = document.getElementById('subnav')!;
  if (sub.classList.contains('visible')) {
    const active = sub.querySelector('button.active');
    if (active) showSection(active.getAttribute('data-section')!);
    else showSection('quiz');
  } else {
    showSection('quiz');
  }
}

export function updateScore(): void {
  const pct = appState.score.total > 0 ? Math.round(appState.score.correct / appState.score.total * 100) : 0;
  document.getElementById('score-text')!.textContent =
    `${appState.score.correct} / ${appState.score.total} (${pct}%)`;
}

/* Keyboard: Enter = submit */
document.getElementById('quiz-input')!.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') checkQuiz();
});
document.getElementById('rev-input')!.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') checkReverse();
});
document.getElementById('mix-input')!.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') checkMixed();
});
document.getElementById('con-input')!.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') checkCon();
});

/* Translate: number string -> nouns */
document.getElementById('translate-input')!.addEventListener('input', function () {
  const raw = (this as HTMLInputElement).value.replace(/[^0-9]/g, '');
  const out = document.getElementById('translate-output')!;
  out.innerHTML = '';
  if (!raw) return;
  for (let i = 0; i < raw.length; i += 2) {
    const chunk = raw.substring(i, i + 2);
    const chip = document.createElement('div');
    if (chunk.length === 2) {
      const word = appState.wordlist[chunk] ?? '???';
      chip.className = 'translate-chip';
      chip.innerHTML = `<div class="number">${chunk}</div><div class="word">${word}</div>`;
    } else {
      chip.className = 'translate-chip odd';
      chip.textContent = `${chunk}?`;
    }
    out.appendChild(chip);
  }
});

/* Reverse translate: words -> digit string */
let _rtTimer: ReturnType<typeof setTimeout> | null = null;
document.getElementById('reverse-translate-input')!.addEventListener('input', function () {
  const text = (this as HTMLInputElement).value.trim();
  const out = document.getElementById('reverse-translate-output')!;
  if (!text) { out.innerHTML = ''; return; }
  if (_rtTimer) clearTimeout(_rtTimer);
  _rtTimer = setTimeout(async () => {
    try {
      const res = await fetch('/api/encode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) return;
      const items: { word: string; digits: string | null }[] = await res.json();
      out.innerHTML = '';
      for (const item of items) {
        const chip = document.createElement('div');
        chip.className = item.digits ? 'translate-chip' : 'translate-chip no-encode';
        chip.innerHTML = `<div class="word">${item.word}</div><div class="number">${item.digits ?? '?'}</div>`;
        out.appendChild(chip);
      }
    } catch {}
  }, 300);
});

/* Grid Quiz */
let gqTimerInterval: ReturnType<typeof setInterval> | null = null;
let gqStartTime = 0;

function formatTime(ms: number): string {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export function startGridQuiz(): void {
  if (gqTimerInterval) clearInterval(gqTimerInterval);
  const grid = document.getElementById('gridquiz-grid')!;
  const result = document.getElementById('gridquiz-result')!;
  const timerEl = document.getElementById('gridquiz-timer')!;
  result.textContent = '';

  // Fisher-Yates shuffle
  const shuffled = [...appState.keys];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  grid.innerHTML = '';
  for (const digits of shuffled) {
    const cell = document.createElement('div');
    cell.className = 'grid-cell';
    cell.setAttribute('data-key', digits);
    cell.innerHTML = `<div class="number">${digits}</div>`;
    const inp = document.createElement('input');
    inp.className = 'word-input';
    inp.setAttribute('data-key', digits);
    inp.autocomplete = 'off';
    inp.spellcheck = false;
    cell.appendChild(inp);
    cell.addEventListener('click', function () { this.querySelector<HTMLInputElement>('.word-input')!.focus(); });
    grid.appendChild(cell);
  }

  gqStartTime = performance.now();
  timerEl.textContent = '0m 0s';
  gqTimerInterval = setInterval(() => {
    timerEl.textContent = formatTime(performance.now() - gqStartTime);
  }, 1000);
}

export function checkGridQuiz(): void {
  if (gqTimerInterval) { clearInterval(gqTimerInterval); gqTimerInterval = null; }
  const cells = document.querySelectorAll('#gridquiz-grid .grid-cell');
  if (!cells.length) return;
  const elapsed = formatTime(performance.now() - gqStartTime);
  document.getElementById('gridquiz-timer')!.textContent = elapsed;

  let correct = 0;
  cells.forEach((cell) => {
    const key = cell.getAttribute('data-key')!;
    const inp = cell.querySelector<HTMLInputElement>('.word-input')!;
    const val = inp.value.trim().toLowerCase();
    const expected = (appState.wordlist[key] ?? '').toLowerCase();
    cell.classList.remove('gq-correct', 'gq-wrong', 'gq-skipped');
    const existing = cell.querySelector('.gq-answer');
    if (existing) existing.remove();

    if (val === expected) {
      cell.classList.add('gq-correct');
      correct++;
    } else {
      cell.classList.add(val ? 'gq-wrong' : 'gq-skipped');
      const ans = document.createElement('div');
      ans.className = 'gq-answer';
      ans.textContent = expected;
      cell.appendChild(ans);
    }
  });

  document.getElementById('gridquiz-result')!.textContent =
    `${correct}/${cells.length} correct — ${elapsed}`;

  cells.forEach((cell) => {
    const inp = cell.querySelector<HTMLInputElement>('.word-input');
    if (inp) inp.disabled = true;
  });
  document.getElementById('gridquiz-check')!.setAttribute('disabled', '');
}

export function toggleTimedQuiz(enabled: boolean): void {
  appState.timedQuiz = enabled;
  saveState();
}

export function toggleDyslexiaFont(enabled: boolean): void {
  appState.dyslexiaFont = enabled;
  document.body.classList.toggle('dyslexia-font', enabled);
  saveState();
}

function renderSettings(): void {
  (document.getElementById('setting-timed') as HTMLInputElement).checked = appState.timedQuiz;
  (document.getElementById('setting-dyslexia') as HTMLInputElement).checked = appState.dyslexiaFont;
}

/* Tutorial */
const TUTORIAL_TOTAL = 5;
let tutorialStep = 0;

const TUTORIAL_QUESTIONS = [
  { word: 'nail', answer: '25' },
  { word: 'bear', answer: '94' },
  { word: 'comb', answer: '73' },
];

function renderTutorialDots(): void {
  const dots = document.getElementById('tutorial-dots')!;
  dots.innerHTML = '';
  for (let i = 0; i < TUTORIAL_TOTAL; i++) {
    const dot = document.createElement('span');
    dot.className = 'tutorial-dot' + (i === tutorialStep ? ' active' : '');
    dots.appendChild(dot);
  }
}

function updateTutorialNav(): void {
  const prev = document.getElementById('tutorial-prev')!;
  const next = document.getElementById('tutorial-next')!;
  prev.style.visibility = tutorialStep === 0 ? 'hidden' : 'visible';
  if (tutorialStep === TUTORIAL_TOTAL - 1) {
    next.textContent = 'Start practicing';
  } else {
    next.textContent = 'Next';
  }
}

function showTutorialStep(): void {
  document.querySelectorAll('.tutorial-step').forEach((el) => el.classList.remove('active'));
  const step = document.querySelector(`.tutorial-step[data-step="${tutorialStep}"]`);
  if (step) step.classList.add('active');
  renderTutorialDots();
  updateTutorialNav();
  if (tutorialStep === 3) renderTutorialQuiz();
}

function renderTutorialQuiz(): void {
  const container = document.getElementById('tutorial-quiz')!;
  container.innerHTML = '';
  for (const q of TUTORIAL_QUESTIONS) {
    const row = document.createElement('div');
    row.className = 'tutorial-quiz-item';
    row.innerHTML = `<span class="tutorial-quiz-word">${q.word}</span>`;
    const inp = document.createElement('input');
    inp.maxLength = 2;
    inp.placeholder = '??';
    const result = document.createElement('span');
    result.className = 'tutorial-quiz-result';
    inp.addEventListener('input', () => {
      const val = inp.value.trim();
      if (val.length === 2) {
        if (val === q.answer) {
          result.textContent = 'Correct!';
          result.className = 'tutorial-quiz-result correct';
        } else {
          result.textContent = `Not quite — it's ${q.answer}`;
          result.className = 'tutorial-quiz-result incorrect';
        }
      } else {
        result.textContent = '';
        result.className = 'tutorial-quiz-result';
      }
    });
    row.appendChild(inp);
    row.appendChild(result);
    container.appendChild(row);
  }
}

export function startTutorial(): void {
  tutorialStep = 0;
  showTutorialStep();
}

export function nextTutorialStep(): void {
  if (tutorialStep < TUTORIAL_TOTAL - 1) {
    tutorialStep++;
    showTutorialStep();
  } else {
    appState.tutorialSeen = true;
    saveState();
    showSection('grid');
  }
}

export function prevTutorialStep(): void {
  if (tutorialStep > 0) {
    tutorialStep--;
    showTutorialStep();
  }
}

export function updateMasteryColors(): void {
  if (!appState.keys.length) return;
  const cells = document.querySelectorAll('#grid .grid-cell');
  cells.forEach((cell) => {
    const key = cell.getAttribute('data-key');
    if (!key) return;
    const total = (MODES.quiz.scores[key] ?? 0) + (MODES.reverse.scores[key] ?? 0) + (MODES.mixed.scores[key] ?? 0);
    let cls: string;
    if (total <= -3) cls = 'mastery-0';
    else if (total < 0) cls = 'mastery-1';
    else if (total <= 3) cls = 'mastery-2';
    else if (total <= 8) cls = 'mastery-3';
    else cls = 'mastery-4';
    cell.className = cell.className.replace(/mastery-\d/g, '').trim() + ' ' + cls;
  });
}
