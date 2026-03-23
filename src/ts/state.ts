import { AppState, AllModes, WordQuizItem, ConsonantQuizItem, StateField } from './types';

/** Combined-score boundaries for mastery tiers 0-4 (struggling..mastered). */
export const MASTERY_THRESHOLDS = [-3, 0, 3, 8] as const;

/** Display names for ambiguous consonant letters in the consonant quiz prompt. */
const CON_DISPLAY_NAMES: Record<string, string> = { C: 'C (hard)', G: 'G (hard)' };

export const appState: AppState = {
  wordlist: {},
  defaultWordlist: {},
  customWords: {},
  mapping: {},
  keys: [],
  score: { correct: 0, total: 0 },
  timedQuiz: false,
  tutorialSeen: false,
  conKeys: [],
  conMap: {},
  dyslexiaFont: false,
  activityLog: {},
};

export const MODES: AllModes = {
  quiz: {
    promptId: 'quiz-prompt', inputId: 'quiz-input',
    feedbackId: 'quiz-feedback', submitId: 'quiz-submit',
    scores: {}, history: [], recentGuesses: [], current: null, timer: null,
    persistScores: 'quizScores', persistHistory: 'quizHistory', persistGuesses: 'quizGuesses',
    allKeys() { return appState.keys; },
    pickItem(k) { return { digits: k, word: appState.wordlist[k] }; },
    getPrompt(item) { return item.digits; },
    getAnswer(item) { return item.word.toLowerCase(); },
    normalize(raw) { return raw.toLowerCase(); },
    formatCorrect(item) { return `"${item.word.toLowerCase()}"`; },
    placeholder: 'type the noun...',
    historyKey(item) { return item.digits; },
  },
  reverse: {
    promptId: 'rev-prompt', inputId: 'rev-input',
    feedbackId: 'rev-feedback', submitId: 'rev-submit',
    scores: {}, history: [], recentGuesses: [], current: null, timer: null,
    persistScores: 'reverseScores', persistHistory: 'reverseHistory', persistGuesses: 'reverseGuesses',
    allKeys() { return appState.keys; },
    pickItem(k) { return { digits: k, word: appState.wordlist[k] }; },
    getPrompt(item) { return item.word; },
    getAnswer(item) { return item.digits; },
    normalize(raw, item) { return raw.padStart(item?.digits.length ?? 2, '0'); },
    formatCorrect(item) { return item.digits; },
    placeholder: 'type the number...',
    historyKey(item) { return item.digits; },
  },
  mixed: {
    promptId: 'mix-prompt', inputId: 'mix-input',
    feedbackId: 'mix-feedback', submitId: 'mix-submit',
    scores: {}, history: [], recentGuesses: [], current: null, timer: null,
    persistScores: 'mixedScores', persistHistory: 'mixedHistory', persistGuesses: 'mixedGuesses',
    allKeys() { return appState.keys; },
    pickItem(k): WordQuizItem {
      const mode = Math.random() < 0.5 ? 'forward' : 'reverse';
      return { digits: k, word: appState.wordlist[k], mode };
    },
    getPrompt(item) { return item.mode === 'forward' ? item.digits : item.word; },
    getAnswer(item) { return item.mode === 'forward' ? item.word.toLowerCase() : item.digits; },
    normalize(raw, item) { return item?.mode === 'forward' ? raw.toLowerCase() : raw.padStart(item?.digits.length ?? 2, '0'); },
    formatCorrect(item) { return item.mode === 'forward' ? `"${item.word.toLowerCase()}"` : item.digits; },
    placeholder: 'type your answer...',
    historyKey(item) { return item.digits; },
    startExtra(item, inp) {
      if (item.mode === 'forward') {
        inp.placeholder = 'type the noun...';
        inp.maxLength = 524288; // browser default — unconstrained free-text input
      } else {
        inp.placeholder = 'type the number...';
        inp.maxLength = item.digits.length;
      }
    },
  },
  consonant: {
    promptId: 'con-prompt', inputId: 'con-input',
    feedbackId: 'con-feedback', submitId: 'con-submit',
    scores: {}, history: [], recentGuesses: [], current: null, timer: null,
    persistScores: 'conScores', persistHistory: 'conHistory', persistGuesses: 'conGuesses',
    allKeys() { return appState.conKeys; },
    pickItem(k) { return { key: k }; },
    getPrompt(item) { return CON_DISPLAY_NAMES[item.key] ?? item.key; },
    getAnswer(item) { return appState.conMap[item.key]; },
    normalize(raw) { return raw; },
    formatCorrect(item) { return appState.conMap[item.key]; },
    placeholder: 'type the digit...',
    historyKey(item) { return item.key; },
  },
};

export const STATE_FIELDS: StateField[] = [
  { key: 'score', get() { return appState.score; }, set(v) { appState.score = (v as typeof appState.score) ?? { correct: 0, total: 0 }; } },
  { key: 'customWords', get() { return appState.customWords; }, set(v) { appState.customWords = (v as typeof appState.customWords) ?? {}; } },
  { key: 'timedQuiz', get() { return appState.timedQuiz; }, set(v) { appState.timedQuiz = v === true; } },
  { key: 'tutorialSeen', get() { return appState.tutorialSeen; }, set(v) { appState.tutorialSeen = v === true; } },
  { key: 'dyslexiaFont', get() { return appState.dyslexiaFont; }, set(v) { appState.dyslexiaFont = v === true; } },
  { key: 'activityLog', get() { return appState.activityLog; }, set(v) { appState.activityLog = (v as typeof appState.activityLog) ?? {}; } },
];
for (const name of Object.keys(MODES) as (keyof AllModes)[]) {
  const mode = MODES[name];
  STATE_FIELDS.push(
    { key: mode.persistScores, get() { return mode.scores; }, set(v) { mode.scores = (v as typeof mode.scores) ?? {}; } },
    { key: mode.persistHistory, get() { return mode.history; }, set(v) { mode.history = (v as typeof mode.history) ?? []; } },
    { key: mode.persistGuesses, get() { return mode.recentGuesses; }, set(v) { mode.recentGuesses = (v as typeof mode.recentGuesses) ?? []; } },
  );
}

export function logActivity(count = 1): void {
  const today = new Date().toISOString().slice(0, 10);
  appState.activityLog[today] = (appState.activityLog[today] ?? 0) + count;
}

export function rebuildWordlist(): void {
  appState.wordlist = { ...appState.defaultWordlist, ...appState.customWords };
  appState.keys = Object.keys(appState.wordlist).sort();
}
