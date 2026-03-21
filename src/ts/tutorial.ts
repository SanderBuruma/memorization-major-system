import { appState } from './state';
import { saveState } from './persistence';
import { escapeHTML } from './utils';

const TUTORIAL_TOTAL = 5;
let tutorialStep = 0;
let tutorialExamples: { word: string; digits: string }[] = [];
let tutorialQuizWords: { word: string; digits: string }[] = [];

const DIGRAPHS = ['th', 'sh', 'ch', 'zh', 'ng'];
const IGNORED_LETTERS = new Set('aeiouwhy'.split(''));

/** Build a breakdown string like "S = <strong>0</strong>, T = <strong>1</strong>" from a word and its known digits. */
function wordBreakdown(word: string, digits: string): string {
  const parts: string[] = [];
  let di = 0;
  const w = word.toLowerCase();
  let i = 0;
  while (i < w.length && di < digits.length) {
    if (i + 1 < w.length) {
      const pair = w.slice(i, i + 2);
      if (DIGRAPHS.includes(pair)) {
        parts.push(`${pair[0].toUpperCase()}${pair[1]} = <strong>${digits[di++]}</strong>`);
        i += 2;
        continue;
      }
    }
    const ch = w[i];
    if (IGNORED_LETTERS.has(ch)) { i++; continue; }
    // doubled consonant = one sound
    if (i + 1 < w.length && w[i + 1] === ch) i++;
    parts.push(`${ch.toUpperCase()} = <strong>${digits[di++]}</strong>`);
    i++;
  }
  return parts.join(', ');
}

/** Pick `count` random wordlist entries, excluding digits already in `exclude`. */
function pickRandomWords(count: number, exclude: Set<string> = new Set()): { word: string; digits: string }[] {
  const available = appState.keys.filter(k => !exclude.has(k));
  const shuffled = available.sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count).map(d => ({ word: appState.wordlist[d], digits: d }));
}

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
  next.textContent = tutorialStep === TUTORIAL_TOTAL - 1 ? 'Start practicing' : 'Next';
}

function renderTutorialExamples(): void {
  const container = document.getElementById('tutorial-examples');
  if (!container) return;
  container.innerHTML = '';
  for (const ex of tutorialExamples) {
    const row = document.createElement('div');
    row.className = 'tutorial-example-row';
    row.innerHTML = `
      <span class="tutorial-word">${escapeHTML(ex.word)}</span>
      <span class="tutorial-arrow">&rarr;</span>
      <span class="tutorial-breakdown">${wordBreakdown(ex.word, ex.digits)}</span>
      <span class="tutorial-arrow">&rarr;</span>
      <span class="tutorial-result">${escapeHTML(ex.digits)}</span>
    `;
    container.appendChild(row);
  }
}

function renderTutorialQuiz(): void {
  const container = document.getElementById('tutorial-quiz')!;
  container.innerHTML = '';
  for (const q of tutorialQuizWords) {
    const row = document.createElement('div');
    row.className = 'tutorial-quiz-item';
    row.innerHTML = `<span class="tutorial-quiz-word">${escapeHTML(q.word)}</span>`;
    const inp = document.createElement('input');
    inp.maxLength = 2;
    inp.placeholder = '??';
    const result = document.createElement('span');
    result.className = 'tutorial-quiz-result';
    inp.addEventListener('input', () => {
      const val = inp.value.trim();
      if (val.length === 2) {
        if (val === q.digits) {
          result.textContent = 'Correct!';
          result.className = 'tutorial-quiz-result correct';
        } else {
          result.textContent = `Not quite — it's ${q.digits}`;
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

function showTutorialStep(): void {
  document.querySelectorAll('.tutorial-step').forEach((el) => el.classList.remove('active'));
  const step = document.querySelector(`.tutorial-step[data-step="${tutorialStep}"]`);
  if (step) step.classList.add('active');
  renderTutorialDots();
  updateTutorialNav();
  if (tutorialStep === 2) renderTutorialExamples();
  if (tutorialStep === 3) renderTutorialQuiz();
}

export function startTutorial(): void {
  tutorialStep = 0;
  tutorialExamples = pickRandomWords(3);
  const usedDigits = new Set(tutorialExamples.map(e => e.digits));
  tutorialQuizWords = pickRandomWords(3, usedDigits);
  showTutorialStep();
}

export function nextTutorialStep(): void {
  if (tutorialStep < TUTORIAL_TOTAL - 1) {
    tutorialStep++;
    showTutorialStep();
  } else {
    appState.tutorialSeen = true;
    saveState();
    // Use window global to avoid circular dependency with ui.ts
    (window as any).showSection('grid');
  }
}

export function prevTutorialStep(): void {
  if (tutorialStep > 0) {
    tutorialStep--;
    showTutorialStep();
  }
}
