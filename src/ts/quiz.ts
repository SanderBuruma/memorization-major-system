import { appState, MODES, logActivity } from './state';
import { QuizItem, QuizMode } from './types';
import { saveState } from './persistence';
import { updateAccuracy } from './ui';

let countdownInterval: ReturnType<typeof setInterval> | null = null;
let countdownTimeout: ReturnType<typeof setTimeout> | null = null;

const MAX_RECENT_GUESSES = 100;

function recordGuess<T extends QuizItem>(mode: QuizMode<T>, correct: boolean): void {
  mode.recentGuesses.push(correct);
  if (mode.recentGuesses.length > MAX_RECENT_GUESSES) mode.recentGuesses.shift();
}

/** Countdown seconds by mastery score: score 1 = 15s, score 2 = 10s, ...; scores above 7 use 3s. */
const TIME_LIMITS = [15, 10, 6, 5, 4, 4, 3];

/** Delay (ms) before auto-advancing to the next question after answer feedback. */
const NEXT_QUESTION_DELAY_MS = 1800;

/** Duration (ms) for question fade-out / fade-in transitions. */
const FADE_MS = 200;

function getQuizArea<T extends QuizItem>(mode: QuizMode<T>): HTMLElement {
  return document.getElementById(mode.promptId)!.parentElement!;
}

function getTimeLimit(score: number): number {
  if (score <= 0) return 0;
  return TIME_LIMITS[Math.min(score - 1, TIME_LIMITS.length - 1)];
}

function clearCountdown(): void {
  if (countdownInterval) { clearInterval(countdownInterval); countdownInterval = null; }
  if (countdownTimeout) { clearTimeout(countdownTimeout); countdownTimeout = null; }
  document.querySelectorAll('.quiz-countdown').forEach(el => {
    el.textContent = '';
    el.classList.remove('urgent');
    (el as HTMLElement).style.display = 'none';
  });
}

function startCountdown<T extends QuizItem>(mode: QuizMode<T>, seconds: number): void {
  clearCountdown();
  const prompt = document.getElementById(mode.promptId)!;
  const quizArea = prompt.parentElement!;
  let cd = quizArea.querySelector('.quiz-countdown') as HTMLElement | null;
  if (!cd) {
    cd = document.createElement('div');
    cd.className = 'quiz-countdown';
    prompt.insertAdjacentElement('afterend', cd);
  }
  let remaining = seconds;
  cd.textContent = `${remaining}s`;
  cd.classList.remove('urgent');
  cd.style.display = '';

  countdownInterval = setInterval(() => {
    remaining--;
    cd!.textContent = `${remaining}s`;
    if (remaining <= 3) cd!.classList.add('urgent');
  }, 1000);

  countdownTimeout = setTimeout(() => { timeoutMode(mode); }, seconds * 1000);
}

function timeoutMode<T extends QuizItem>(mode: QuizMode<T>): void {
  clearCountdown();
  if (!mode.current) return;
  const inp = document.getElementById(mode.inputId) as HTMLInputElement;
  inp.disabled = true;
  (document.getElementById(mode.submitId) as HTMLButtonElement).disabled = true;

  const key = mode.historyKey(mode.current);
  mode.scores[key] = (mode.scores[key] ?? 0) - 1;
  appState.score.total++;
  logActivity();

  const fb = document.getElementById(mode.feedbackId)!;
  fb.className = 'feedback incorrect';
  fb.textContent = `Time's up! Answer: ${mode.formatCorrect(mode.current)}`;

  recordGuess(mode, false);
  mode.history.push(key);
  if (mode.history.length > 10) mode.history.shift();
  updateAccuracy(mode);
  saveState();
  mode.timer = setTimeout(() => { startMode(mode); }, NEXT_QUESTION_DELAY_MS);
}

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

/** Populate quiz DOM with new question content (no countdown — caller handles timing). */
function applyNextQuestion<T extends QuizItem>(mode: QuizMode<T>): void {
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
  clearCountdown();
  if (mode.startExtra) mode.startExtra(item, inp);
  inp.focus();
}

/** Start the timed countdown for the current question if applicable. */
function maybeStartCountdown<T extends QuizItem>(mode: QuizMode<T>): void {
  if (!mode.current) return;
  const key = mode.historyKey(mode.current);
  const score = mode.scores[key] ?? 0;
  const limit = appState.timedQuiz ? getTimeLimit(score) : 0;
  if (limit > 0) startCountdown(mode, limit);
}

export function startMode<T extends QuizItem>(mode: QuizMode<T>): void {
  if (mode.timer) clearTimeout(mode.timer);
  const area = getQuizArea(mode);
  const isFirstQuestion = mode.current === null;

  if (isFirstQuestion) {
    // First question: no fade-out, just set content then fade in
    area.classList.add('quiz-fade-out');
    applyNextQuestion(mode);
    // Force reflow so the opacity:0 applies before we remove the class
    void area.offsetHeight;
    area.classList.remove('quiz-fade-out');
    // Start countdown after fade-in completes
    setTimeout(() => { maybeStartCountdown(mode); }, FADE_MS);
  } else {
    // Subsequent questions: fade out, swap content, fade in
    area.classList.add('quiz-fade-out');
    setTimeout(() => {
      applyNextQuestion(mode);
      area.classList.remove('quiz-fade-out');
      // Start countdown after fade-in completes
      setTimeout(() => { maybeStartCountdown(mode); }, FADE_MS);
    }, FADE_MS);
  }
}

export function checkMode<T extends QuizItem>(mode: QuizMode<T>): void {
  clearCountdown();
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
  logActivity();
  const fb = document.getElementById(mode.feedbackId)!;
  const isCorrect = answer === correct;
  if (isCorrect) {
    appState.score.correct++;
    mode.scores[key] = (mode.scores[key] ?? 0) + 1;
    fb.className = 'feedback correct';
    fb.textContent = 'Correct!';
  } else {
    mode.scores[key] = (mode.scores[key] ?? 0) - 1;
    fb.className = 'feedback incorrect';
    fb.textContent = `Incorrect. Answer: ${mode.formatCorrect(mode.current)}`;
  }
  recordGuess(mode, isCorrect);
  mode.history.push(key);
  if (mode.history.length > 10) mode.history.shift();
  updateAccuracy(mode);
  saveState();
  mode.timer = setTimeout(() => { startMode(mode); }, NEXT_QUESTION_DELAY_MS);
}

export function skipMode<T extends QuizItem>(mode: QuizMode<T>): void {
  clearCountdown();
  if (mode.timer) clearTimeout(mode.timer);
  if (mode.current) {
    mode.history.push(mode.historyKey(mode.current));
    if (mode.history.length > 10) mode.history.shift();
    saveState();
  }
  const area = getQuizArea(mode);
  area.classList.add('quiz-fade-out');
  setTimeout(() => {
    applyNextQuestion(mode);
    area.classList.remove('quiz-fade-out');
    setTimeout(() => { maybeStartCountdown(mode); }, FADE_MS);
  }, FADE_MS);
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
