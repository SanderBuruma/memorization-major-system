import { appState, MODES, logActivity } from './state';
import { QuizItem, QuizMode } from './types';
import { saveState } from './persistence';
import { updateAccuracy } from './ui';

let countdownInterval: ReturnType<typeof setInterval> | null = null;
let countdownTimeout: ReturnType<typeof setTimeout> | null = null;

const MAX_RECENT_GUESSES = 100;

/* --- Response-time scoring state --- */
let questionStartTime = 0;
let accumulatedElapsed = 0;
let timerPaused = false;
const WRONG_ANSWER_SECONDS = 10;
const SCORE_HISTORY_MAX = 10;
const WEIGHT_DECAY = 0.7;

function resetResponseTimer(): void {
  questionStartTime = performance.now();
  accumulatedElapsed = 0;
  timerPaused = false;
}

function pauseTimer(): void {
  if (timerPaused) return;
  accumulatedElapsed += performance.now() - questionStartTime;
  timerPaused = true;
}

function resumeTimer(): void {
  if (!timerPaused) return;
  questionStartTime = performance.now();
  timerPaused = false;
}

function getElapsedSeconds(): number {
  const running = timerPaused ? 0 : performance.now() - questionStartTime;
  return Math.max(0, (accumulatedElapsed + running) / 1000);
}

/** Piecewise score contribution: +5 at ≤0.5s, 0 at 2s, -5 at ≥10s. */
function timeToContribution(seconds: number): number {
  if (seconds <= 0.5) return 5;
  if (seconds <= 2) return 5 * (2 - seconds) / 1.5;
  if (seconds >= 10) return -5;
  return -5 * (seconds - 2) / 8;
}

function weightedAverage(values: number[]): number {
  let sum = 0, wsum = 0;
  for (let i = values.length - 1, w = 1; i >= 0; i--, w *= WEIGHT_DECAY) {
    sum += values[i] * w;
    wsum += w;
  }
  return sum / wsum;
}

function updateTimeScore(
  scores: Record<string, number>,
  hist: Record<string, number[]>,
  key: string, seconds: number,
): void {
  const arr = hist[key] ?? [];
  arr.push(timeToContribution(seconds));
  if (arr.length > SCORE_HISTORY_MAX) arr.shift();
  hist[key] = arr;
  scores[key] = weightedAverage(arr);
}

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
  const tier = Math.max(1, Math.ceil(score * 1.5));
  return TIME_LIMITS[Math.min(tier - 1, TIME_LIMITS.length - 1)];
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
  updateTimeScore(mode.scores, mode.scoreHistory, key, WRONG_ANSWER_SECONDS);
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
  // Weight selection toward lower-scored items: weight = (maxScore - score + 1)^2
  let maxScore = -Infinity;
  for (const key of eligible) {
    const s = scores[key] ?? 0;
    if (s > maxScore) maxScore = s;
  }
  const weights: number[] = [];
  let totalWeight = 0;
  for (const key of eligible) {
    const w = (maxScore - (scores[key] ?? 0) + 1) ** 2;
    weights.push(w);
    totalWeight += w;
  }
  let r = Math.random() * totalWeight;
  for (let i = 0; i < eligible.length; i++) {
    r -= weights[i];
    if (r <= 0) return eligible[i];
  }
  return eligible[eligible.length - 1];
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
    // Start countdown + response timer after fade-in completes
    setTimeout(() => { maybeStartCountdown(mode); resetResponseTimer(); }, FADE_MS);
  } else {
    // Subsequent questions: fade out, swap content, fade in
    area.classList.add('quiz-fade-out');
    setTimeout(() => {
      applyNextQuestion(mode);
      area.classList.remove('quiz-fade-out');
      // Start countdown + response timer after fade-in completes
      setTimeout(() => { maybeStartCountdown(mode); resetResponseTimer(); }, FADE_MS);
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
    updateTimeScore(mode.scores, mode.scoreHistory, key, getElapsedSeconds());
    fb.className = 'feedback correct';
    fb.textContent = 'Correct!';
  } else {
    updateTimeScore(mode.scores, mode.scoreHistory, key, WRONG_ANSWER_SECONDS);
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
    setTimeout(() => { maybeStartCountdown(mode); resetResponseTimer(); }, FADE_MS);
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

/* Prefix-match timer pausing: 500ms grace window per correct keystroke */
const PAUSE_GRACE_MS = 500;
let pauseGraceTimeout: ReturnType<typeof setTimeout> | null = null;

function handleQuizInput<T extends QuizItem>(mode: QuizMode<T>): void {
  if (!mode.current) return;
  const inp = document.getElementById(mode.inputId) as HTMLInputElement;
  const raw = inp.value.trim().toLowerCase();
  const correct = mode.getAnswer(mode.current).toLowerCase();
  if (raw && correct.startsWith(raw)) {
    pauseTimer();
    if (pauseGraceTimeout) clearTimeout(pauseGraceTimeout);
    pauseGraceTimeout = setTimeout(() => { resumeTimer(); pauseGraceTimeout = null; }, PAUSE_GRACE_MS);
  } else {
    if (pauseGraceTimeout) { clearTimeout(pauseGraceTimeout); pauseGraceTimeout = null; }
    resumeTimer();
  }
}

document.getElementById('quiz-input')!.addEventListener('input', () => handleQuizInput(MODES.quiz));
document.getElementById('rev-input')!.addEventListener('input', () => handleQuizInput(MODES.reverse));
document.getElementById('mix-input')!.addEventListener('input', () => handleQuizInput(MODES.mixed));
document.getElementById('con-input')!.addEventListener('input', () => handleQuizInput(MODES.consonant));
