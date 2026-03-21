import { appState, MODES } from './state';
import { QuizItem, QuizMode } from './types';
import { saveState } from './persistence';
import { updateScore } from './ui';

function pickNext(scores: Record<string, number>, history: string[], allKeys: string[]): string {
  let eligible = allKeys.filter((key) => !history.includes(key));
  if (eligible.length === 0) eligible = allKeys.slice();
  let minScore = Infinity;
  for (const key of eligible) {
    const score = scores[key] ?? 0;
    if (score < minScore) minScore = score;
  }
  const candidates = eligible.filter((key) => (scores[key] ?? 0) === minScore);
  return candidates[Math.floor(Math.random() * candidates.length)];
}

export function startMode<T extends QuizItem>(mode: QuizMode<T>): void {
  if (mode.timer) clearTimeout(mode.timer);
  const pick = pickNext(mode.scores, mode.history, mode.allKeys());
  if (!pick) return;
  const item = mode.pickItem(pick);
  mode.current = item;
  document.getElementById(mode.promptId)!.textContent = mode.getPrompt(item);
  const inp = document.getElementById(mode.inputId) as HTMLInputElement;
  inp.value = '';
  inp.disabled = false;
  inp.placeholder = mode.placeholder;
  (document.getElementById(mode.submitId) as HTMLButtonElement).disabled = false;
  const fb = document.getElementById(mode.feedbackId)!;
  fb.className = 'feedback empty';
  fb.textContent = '';
  if (mode.startExtra) mode.startExtra(item, inp);
  inp.focus();
}

export function checkMode<T extends QuizItem>(mode: QuizMode<T>): void {
  if (!mode.current) return;
  const inp = document.getElementById(mode.inputId) as HTMLInputElement;
  const raw = inp.value.trim();
  if (!raw) return;
  inp.disabled = true;
  (document.getElementById(mode.submitId) as HTMLButtonElement).disabled = true;

  const answer = mode.normalize(raw, mode.current);
  const correct = mode.getAnswer(mode.current);
  const key = mode.historyKey(mode.current);
  appState.score.total++;
  const fb = document.getElementById(mode.feedbackId)!;
  if (answer === correct) {
    appState.score.correct++;
    mode.scores[key] = (mode.scores[key] ?? 0) + 1;
    fb.className = 'feedback correct';
    fb.textContent = 'Correct!';
  } else {
    mode.scores[key] = (mode.scores[key] ?? 0) - 1;
    fb.className = 'feedback incorrect';
    fb.textContent = `Incorrect. Answer: ${mode.formatCorrect(mode.current)}`;
  }
  mode.history.push(key);
  if (mode.history.length > 10) mode.history.shift();
  updateScore();
  saveState();
  mode.timer = setTimeout(() => { startMode(mode); }, 1800);
}

export function skipMode<T extends QuizItem>(mode: QuizMode<T>): void {
  if (mode.current) {
    mode.history.push(mode.historyKey(mode.current));
    if (mode.history.length > 10) mode.history.shift();
    saveState();
  }
  startMode(mode);
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
