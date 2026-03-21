import { AppState, AllModes, WordQuizItem, ConsonantQuizItem, StateField } from './types';

export const S: AppState = {
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
    allKeys() { return S.keys; },
    pickItem(k) { return { digits: k, word: S.wordlist[k] }; },
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
    allKeys() { return S.keys; },
    pickItem(k) { return { digits: k, word: S.wordlist[k] }; },
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
    allKeys() { return S.keys; },
    pickItem(k): WordQuizItem {
      const mode = Math.random() < 0.5 ? 'forward' : 'reverse';
      return { digits: k, word: S.wordlist[k], mode };
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
    allKeys() { return S.conKeys; },
    pickItem(k) { return { key: k }; },
    getPrompt(item) { const d: Record<string, string> = { C: 'C (hard)', G: 'G (hard)' }; return d[item.key] ?? item.key; },
    getAnswer(item) { return S.conMap[item.key]; },
    normalize(raw) { return raw; },
    formatCorrect(item) { return S.conMap[item.key]; },
    placeholder: 'type the digit...',
    historyKey(item) { return item.key; },
  },
};

export const STATE_FIELDS: StateField[] = [
  { key: 'score', get() { return S.score; }, set(v) { S.score = (v as typeof S.score) ?? { correct: 0, total: 0 }; } },
  { key: 'customWords', get() { return S.customWords; }, set(v) { S.customWords = (v as typeof S.customWords) ?? {}; } },
];
for (const name of Object.keys(MODES) as (keyof AllModes)[]) {
  const m = MODES[name];
  STATE_FIELDS.push(
    { key: m.persistScores, get() { return m.scores; }, set(v) { m.scores = (v as typeof m.scores) ?? {}; } },
    { key: m.persistHistory, get() { return m.history; }, set(v) { m.history = (v as typeof m.history) ?? []; } },
  );
}

export function rebuildWordlist(): void {
  S.wordlist = {};
  for (const k of Object.keys(S.defaultWordlist)) S.wordlist[k] = S.defaultWordlist[k];
  for (const k of Object.keys(S.customWords)) S.wordlist[k] = S.customWords[k];
  S.keys = Object.keys(S.wordlist).sort();
}
