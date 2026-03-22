export interface AppState {
  wordlist: Record<string, string>;
  defaultWordlist: Record<string, string>;
  customWords: Record<string, string>;
  mapping: Record<string, string>;
  keys: string[];
  score: Score;
  timedQuiz: boolean;
  tutorialSeen: boolean;
  conKeys: string[];
  conMap: Record<string, string>;
  dyslexiaFont: boolean;
  activityLog: Record<string, number>;
}

export interface Score { correct: number; total: number; }

export interface WordQuizItem { digits: string; word: string; mode?: 'forward' | 'reverse'; }
export interface ConsonantQuizItem { key: string; }
export type QuizItem = WordQuizItem | ConsonantQuizItem;

export interface QuizMode<T extends QuizItem = QuizItem> {
  readonly promptId: string;
  readonly inputId: string;
  readonly feedbackId: string;
  readonly submitId: string;
  scores: Record<string, number>;
  history: string[];
  recentGuesses: boolean[];
  current: T | null;
  timer: ReturnType<typeof setTimeout> | null;
  readonly persistScores: string;
  readonly persistHistory: string;
  readonly persistGuesses: string;
  allKeys(): string[];
  pickItem(k: string): T;
  getPrompt(item: T): string;
  getAnswer(item: T): string;
  normalize(raw: string, item?: T): string;
  formatCorrect(item: T): string;
  readonly placeholder: string;
  historyKey(item: T): string;
  startExtra?(item: T, inp: HTMLInputElement): void;
}

export interface AllModes {
  quiz: QuizMode<WordQuizItem>;
  reverse: QuizMode<WordQuizItem>;
  mixed: QuizMode<WordQuizItem>;
  consonant: QuizMode<ConsonantQuizItem>;
}

export interface StateField { key: string; get(): unknown; set(v: unknown): void; localOnly?: boolean; }

export interface ServerState {
  user: string | null;
  updatedAt: string | null;
  score?: Score;
  theme?: string;
  [key: string]: unknown;
}
