import { S, MODES } from './state';
import { QuizItem, QuizMode } from './types';
import { saveState } from './persistence';
import { updateScore } from './ui';

function pickNext(scores: Record<string, number>, history: string[], allKeys: string[]): string {
  let eligible = allKeys.filter((k) => history.indexOf(k) === -1);
  if (eligible.length === 0) eligible = allKeys.slice();
  let minScore = Infinity;
  for (const k of eligible) {
    const s = scores[k] ?? 0;
    if (s < minScore) minScore = s;
  }
  const candidates = eligible.filter((k) => (scores[k] ?? 0) === minScore);
  return candidates[Math.floor(Math.random() * candidates.length)];
}

export function startMode<T extends QuizItem>(m: QuizMode<T>): void {
  if (m.timer) clearTimeout(m.timer);
  const pick = pickNext(m.scores, m.history, m.allKeys());
  if (!pick) return;
  const item = m.pickItem(pick);
  m.current = item;
  document.getElementById(m.promptId)!.textContent = m.getPrompt(item);
  const inp = document.getElementById(m.inputId) as HTMLInputElement;
  inp.value = '';
  inp.disabled = false;
  inp.placeholder = m.placeholder;
  (document.getElementById(m.submitId) as HTMLButtonElement).disabled = false;
  const fb = document.getElementById(m.feedbackId)!;
  fb.className = 'feedback empty';
  fb.textContent = '';
  if (m.startExtra) m.startExtra(item, inp);
  inp.focus();
}

export function checkMode<T extends QuizItem>(m: QuizMode<T>): void {
  if (!m.current) return;
  const inp = document.getElementById(m.inputId) as HTMLInputElement;
  const raw = inp.value.trim();
  if (!raw) return;
  inp.disabled = true;
  (document.getElementById(m.submitId) as HTMLButtonElement).disabled = true;

  const answer = m.normalize(raw, m.current);
  const correct = m.getAnswer(m.current);
  const key = m.historyKey(m.current);
  S.score.total++;
  const fb = document.getElementById(m.feedbackId)!;
  if (answer === correct) {
    S.score.correct++;
    m.scores[key] = (m.scores[key] ?? 0) + 1;
    fb.className = 'feedback correct';
    fb.textContent = 'Correct!';
  } else {
    m.scores[key] = (m.scores[key] ?? 0) - 1;
    fb.className = 'feedback incorrect';
    fb.textContent = `Incorrect. Answer: ${m.formatCorrect(m.current)}`;
  }
  m.history.push(key);
  if (m.history.length > 10) m.history.shift();
  updateScore();
  saveState();
  m.timer = setTimeout(() => { startMode(m); }, 1800);
}

export function skipMode<T extends QuizItem>(m: QuizMode<T>): void {
  if (m.current) {
    m.history.push(m.historyKey(m.current));
    if (m.history.length > 10) m.history.shift();
    saveState();
  }
  startMode(m);
}

/* Thin wrappers for HTML onclick handlers */
export function startQuiz() { startMode(MODES.quiz); }
export function checkQuiz() { checkMode(MODES.quiz); }
export function skipQuiz() { skipMode(MODES.quiz); }
export function startReverse() { startMode(MODES.reverse); }
export function checkReverse() { checkMode(MODES.reverse); }
export function skipReverse() { skipMode(MODES.reverse); }
export function startMixed() { startMode(MODES.mixed); }
export function checkMixed() { checkMode(MODES.mixed); }
export function skipMixed() { skipMode(MODES.mixed); }
export function startCon() { startMode(MODES.consonant); }
export function checkCon() { checkMode(MODES.consonant); }
export function skipCon() { skipMode(MODES.consonant); }
