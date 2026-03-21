import { appState, MODES, MASTERY_THRESHOLDS, rebuildWordlist, logActivity } from './state';
import { getCookie, saveState } from './persistence';
import { startQuiz, startReverse, startMixed, startCon,
         checkQuiz, checkReverse, checkMixed, checkCon } from './quiz';
import { renderProfile } from './profile';
import { startTutorial } from './tutorial';
import { escapeHTML } from './utils';
import { QuizItem, QuizMode } from './types';
import { MATH_CONSTANTS } from './constants';

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

/** Update the custom-word asterisk marker next to the digit label. */
function updateCustomMarker(inp: HTMLInputElement, key: string): void {
  const numEl = inp.parentNode!.querySelector('.number')!;
  const marker = numEl.querySelector('.custom-marker');
  if (appState.customWords[key] && !marker) {
    numEl.insertAdjacentHTML('beforeend', '<span class="custom-marker">*</span>');
  } else if (!appState.customWords[key] && marker) {
    marker.remove();
  }
}

/** Attach focus, keydown, input, and blur listeners to a grid cell input. */
function setupGridCellInput(inp: HTMLInputElement): void {
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
    updateCustomMarker(this, key);
  });
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
    setupGridCellInput(inp);
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
    tr.innerHTML = `<td><strong>${digit}</strong></td><td>${escapeHTML(appState.mapping[String(digit)] ?? '')}</td>`;
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
      chip.innerHTML = `<div class="number">${escapeHTML(chunk)}</div><div class="word">${escapeHTML(word)}</div>`;
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
        chip.innerHTML = `<div class="word">${escapeHTML(item.word)}</div><div class="number">${escapeHTML(item.digits ?? '?')}</div>`;
        out.appendChild(chip);
      }
    } catch {}
  }, 300);
});

/* Constant buttons for Translate */
export function renderConstantButtons(): void {
  const container = document.getElementById('constant-buttons');
  if (!container) return;
  const input = document.getElementById('translate-input') as HTMLInputElement;
  for (const { symbol, name, digits } of MATH_CONSTANTS) {
    const btn = document.createElement('button');
    btn.className = 'constant-btn';
    btn.textContent = symbol;
    btn.title = name;
    btn.addEventListener('click', () => {
      input.value = digits;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    container.appendChild(btn);
  }
}

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

  logActivity(cells.length);

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
  const fb = document.getElementById('import-feedback');
  if (fb) fb.textContent = '';
}

function showImportFeedback(msg: string, isError: boolean): void {
  const fb = document.getElementById('import-feedback');
  if (!fb) return;
  fb.textContent = msg;
  fb.style.color = isError ? 'var(--color-error, #e74c3c)' : 'var(--color-success, #2ecc71)';
}

function applyImportedWords(imported: Record<string, string>): void {
  let total = 0;
  let custom = 0;
  for (const [num, word] of Object.entries(imported)) {
    total++;
    if (word === appState.defaultWordlist[num]) {
      delete appState.customWords[num];
    } else {
      appState.customWords[num] = word;
      custom++;
    }
  }
  rebuildWordlist();
  renderGrid();
  updateMasteryColors();
  saveState();
  showImportFeedback(`Imported ${total} words (${custom} custom)`, false);
}

function parseCSVImport(text: string): Record<string, string> | string {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (!lines.length) return 'CSV file is empty';
  let start = 0;
  const first = lines[0].split(',')[0].trim();
  if (first === 'number' || !/^\d+$/.test(first)) start = 1;
  const result: Record<string, string> = {};
  const errors: string[] = [];
  for (let i = start; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (cols.length < 2) { errors.push(`Line ${i + 1}: not enough columns`); continue; }
    const num = cols[0].trim().padStart(2, '0');
    const word = cols[1].trim();
    if (!/^\d{2}$/.test(num) || parseInt(num) > 99) { errors.push(`Line ${i + 1}: invalid number "${cols[0].trim()}"`); continue; }
    if (!/^[a-z]/.test(word)) { errors.push(`Line ${i + 1}: word "${word}" must start with a lowercase letter`); continue; }
    result[num] = word;
  }
  if (errors.length && !Object.keys(result).length) return errors.join('; ');
  if (errors.length) return errors.join('; ');
  return result;
}

function parseJSONImport(text: string): Record<string, string> | string {
  let data: unknown;
  try { data = JSON.parse(text); } catch { return 'Invalid JSON file'; }
  if (typeof data !== 'object' || data === null || Array.isArray(data)) return 'JSON must be an object like {"00": "word", ...}';
  const obj = data as Record<string, unknown>;
  const result: Record<string, string> = {};
  const errors: string[] = [];
  for (const [key, val] of Object.entries(obj)) {
    const num = key.trim().padStart(2, '0');
    if (!/^\d{2}$/.test(num) || parseInt(num) > 99) { errors.push(`Invalid number "${key}"`); continue; }
    if (typeof val !== 'string') { errors.push(`Value for "${key}" is not a string`); continue; }
    const word = val.trim();
    if (!/^[a-z]/.test(word)) { errors.push(`Word "${word}" for ${key} must start with a lowercase letter`); continue; }
    result[num] = word;
  }
  if (errors.length && !Object.keys(result).length) return errors.join('; ');
  if (errors.length) return errors.join('; ');
  return result;
}

function handleFileImport(inputId: string, parser: (text: string) => Record<string, string> | string): void {
  const input = document.getElementById(inputId) as HTMLInputElement;
  input.value = '';
  input.onchange = () => {
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result as string;
      const result = parser(text);
      if (typeof result === 'string') {
        showImportFeedback(result, true);
      } else if (!Object.keys(result).length) {
        showImportFeedback('No valid entries found in file', true);
      } else {
        applyImportedWords(result);
      }
    };
    reader.onerror = () => showImportFeedback('Failed to read file', true);
    reader.readAsText(file);
  };
  input.click();
}

export function importCSV(): void {
  handleFileImport('import-csv-input', parseCSVImport);
}

export function importJSON(): void {
  handleFileImport('import-json-input', parseJSONImport);
}

export function exportWordlistCSV(): void {
  let csv = 'number,word,custom\n';
  for (let i = 0; i < 100; i++) {
    const digits = String(i).padStart(2, '0');
    const word = appState.wordlist[digits] ?? '';
    const isCustom = appState.customWords[digits] ? 'true' : '';
    csv += `${digits},${word},${isCustom}\n`;
  }
  downloadFile(csv, 'major-system-wordlist.csv', 'text/csv');
}

export function exportWordlistJSON(): void {
  const obj: Record<string, string> = {};
  for (let i = 0; i < 100; i++) {
    const digits = String(i).padStart(2, '0');
    obj[digits] = appState.wordlist[digits] ?? '';
  }
  downloadFile(JSON.stringify(obj, null, 2), 'major-system-wordlist.json', 'application/json');
}

function downloadFile(content: string, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** Update the accuracy footer for a quiz mode based on its last 100 guesses. */
export function updateAccuracy<T extends QuizItem>(mode: QuizMode<T>): void {
  const fb = document.getElementById(mode.feedbackId);
  if (!fb) return;
  const area = fb.closest('.quiz-area');
  if (!area) return;
  let el = area.querySelector('.quiz-accuracy') as HTMLElement | null;
  if (!el) {
    el = document.createElement('div');
    el.className = 'quiz-accuracy';
    area.appendChild(el);
  }
  const guesses = mode.recentGuesses;
  if (guesses.length === 0) { el.textContent = ''; return; }
  const correct = guesses.filter(Boolean).length;
  const pct = Math.round(correct / guesses.length * 100);
  el.textContent = `Last ${guesses.length}: ${correct}/${guesses.length} (${pct}%)`;
}

export function updateMasteryColors(): void {
  if (!appState.keys.length) return;
  const cells = document.querySelectorAll('#grid .grid-cell');
  cells.forEach((cell) => {
    const key = cell.getAttribute('data-key');
    if (!key) return;
    const total = (MODES.quiz.scores[key] ?? 0) + (MODES.reverse.scores[key] ?? 0) + (MODES.mixed.scores[key] ?? 0);
    const [t0, t1, t2, t3] = MASTERY_THRESHOLDS;
    let cls: string;
    if (total <= t0) cls = 'mastery-0';
    else if (total < t1) cls = 'mastery-1';
    else if (total <= t2) cls = 'mastery-2';
    else if (total <= t3) cls = 'mastery-3';
    else cls = 'mastery-4';
    cell.className = cell.className.replace(/mastery-\d/g, '').trim() + ' ' + cls;
  });
}
