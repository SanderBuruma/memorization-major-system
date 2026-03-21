import { AppState, AllModes, WordQuizItem, ConsonantQuizItem, StateField } from './types';

export const appState: AppState = {
  wordlist: {},
  defaultWordlist: {},
  customWords: {},
  mapping: {},
  keys: [],
  score: { correct: 0, total: 0 },
  conKeys: [],
  conMap: {},
};

export const MODES: AllModes = {
  quiz: {
    promptId: 'quiz-prompt', inputId: 'quiz-input',
    feedbackId: 'quiz-feedback', submitId: 'quiz-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'quizScores', persistHistory: 'quizHistory',
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
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'reverseScores', persistHistory: 'reverseHistory',
    allKeys() { return appState.keys; },
    pickItem(k) { return { digits: k, word: appState.wordlist[k] }; },
    getPrompt(item) { return item.word; },
    getAnswer(item) { return item.digits; },
    normalize(raw) { return raw.padStart(2, '0'); },
    formatCorrect(item) { return item.digits; },
    placeholder: 'type the number...',
    historyKey(item) { return item.digits; },
  },
  mixed: {
    promptId: 'mix-prompt', inputId: 'mix-input',
    feedbackId: 'mix-feedback', submitId: 'mix-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'mixedScores', persistHistory: 'mixedHistory',
    allKeys() { return appState.keys; },
    pickItem(k): WordQuizItem {
      const mode = Math.random() < 0.5 ? 'forward' : 'reverse';
      return { digits: k, word: appState.wordlist[k], mode };
    },
    getPrompt(item) { return item.mode === 'forward' ? item.digits : item.word; },
    getAnswer(item) { return item.mode === 'forward' ? item.word.toLowerCase() : item.digits; },
    normalize(raw, item) { return item?.mode === 'forward' ? raw.toLowerCase() : raw.padStart(2, '0'); },
    formatCorrect(item) { return item.mode === 'forward' ? `"${item.word.toLowerCase()}"` : item.digits; },
    placeholder: 'type your answer...',
    historyKey(item) { return item.digits; },
    startExtra(item, inp) {
      if (item.mode === 'forward') {
        inp.placeholder = 'type the noun...';
        inp.maxLength = 524288;
      } else {
        inp.placeholder = 'type the number...';
        inp.maxLength = 2;
      }
    },
  },
  consonant: {
    promptId: 'con-prompt', inputId: 'con-input',
    feedbackId: 'con-feedback', submitId: 'con-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'conScores', persistHistory: 'conHistory',
    allKeys() { return appState.conKeys; },
    pickItem(k) { return { key: k }; },
    getPrompt(item) { const d: Record<string, string> = { C: 'C (hard)', G: 'G (hard)' }; return d[item.key] ?? item.key; },
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
];
for (const name of Object.keys(MODES) as (keyof AllModes)[]) {
  const mode = MODES[name];
  STATE_FIELDS.push(
    { key: mode.persistScores, get() { return mode.scores; }, set(v) { mode.scores = (v as typeof mode.scores) ?? {}; } },
    { key: mode.persistHistory, get() { return mode.history; }, set(v) { mode.history = (v as typeof mode.history) ?? []; } },
  );
}

export function rebuildWordlist(): void {
  appState.wordlist = { ...appState.defaultWordlist, ...appState.customWords };
  appState.keys = Object.keys(appState.wordlist).sort();
}
