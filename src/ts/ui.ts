import { appState, MODES, rebuildWordlist } from './state';
import { saveState } from './persistence';
import { startQuiz, startReverse, startMixed, startCon,
         checkQuiz, checkReverse, checkMixed, checkCon } from './quiz';
import { renderProfile } from './profile';

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
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') this.blur();
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
    });
    inp.addEventListener('blur', function () {
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

const quizSections = ['quiz', 'reverse', 'mixed', 'consonant'];

export function showSection(name: string): void {
  document.querySelectorAll('.section').forEach((section) => { section.classList.remove('active'); });
  document.getElementById(`section-${name}`)!.classList.add('active');
  document.querySelectorAll('.topbar-nav button').forEach((btn) => { btn.classList.remove('active'); });
  const isQuiz = quizSections.indexOf(name) !== -1;
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
  if (name === 'quiz') startQuiz();
  if (name === 'reverse') startReverse();
  if (name === 'mixed') startMixed();
  if (name === 'consonant') startCon();
  if (name === 'profile') renderProfile();
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
    const chunk = raw.substr(i, 2);
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

export function updateMasteryColors(): void {
  if (!appState.keys.length) return;
  const cells = document.querySelectorAll('.grid-cell');
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
