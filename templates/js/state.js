/* ================================================================== */
/*  State                                                              */
/* ================================================================== */
var S = {
  wordlist: {},
  defaultWordlist: {},
  customWords: {},
  mapping: {},
  keys: [],
  score: {correct: 0, total: 0},
  conKeys: [],
  conMap: {}
};

/* ================================================================== */
/*  Quiz mode configs                                                  */
/* ================================================================== */
var MODES = {
  quiz: {
    promptId: 'quiz-prompt', inputId: 'quiz-input',
    feedbackId: 'quiz-feedback', submitId: 'quiz-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'quizScores', persistHistory: 'quizHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){ return {digits: k, word: S.wordlist[k]}; },
    getPrompt: function(item){ return item.digits; },
    getAnswer: function(item){ return item.word.toLowerCase(); },
    normalize: function(raw){ return raw.toLowerCase(); },
    formatCorrect: function(item){ return '"' + item.word.toLowerCase() + '"'; },
    placeholder: 'type the noun...',
    historyKey: function(item){ return item.digits; }
  },
  reverse: {
    promptId: 'rev-prompt', inputId: 'rev-input',
    feedbackId: 'rev-feedback', submitId: 'rev-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'reverseScores', persistHistory: 'reverseHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){ return {digits: k, word: S.wordlist[k]}; },
    getPrompt: function(item){ return item.word; },
    getAnswer: function(item){ return item.digits; },
    normalize: function(raw){ return raw.padStart(2, '0'); },
    formatCorrect: function(item){ return item.digits; },
    placeholder: 'type the number...',
    historyKey: function(item){ return item.digits; }
  },
  mixed: {
    promptId: 'mix-prompt', inputId: 'mix-input',
    feedbackId: 'mix-feedback', submitId: 'mix-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'mixedScores', persistHistory: 'mixedHistory',
    allKeys: function(){ return S.keys; },
    pickItem: function(k){
      var mode = Math.random() < 0.5 ? 'forward' : 'reverse';
      return {digits: k, word: S.wordlist[k], mode: mode};
    },
    getPrompt: function(item){ return item.mode === 'forward' ? item.digits : item.word; },
    getAnswer: function(item){ return item.mode === 'forward' ? item.word.toLowerCase() : item.digits; },
    normalize: function(raw, item){ return item.mode === 'forward' ? raw.toLowerCase() : raw.padStart(2, '0'); },
    formatCorrect: function(item){ return item.mode === 'forward' ? '"' + item.word.toLowerCase() + '"' : item.digits; },
    placeholder: 'type your answer...',
    historyKey: function(item){ return item.digits; },
    startExtra: function(item, inp){
      if(item.mode === 'forward'){
        inp.placeholder = 'type the noun...';
        inp.maxLength = 524288;
      } else {
        inp.placeholder = 'type the number...';
        inp.maxLength = '2';
      }
    }
  },
  consonant: {
    promptId: 'con-prompt', inputId: 'con-input',
    feedbackId: 'con-feedback', submitId: 'con-submit',
    scores: {}, history: [], current: null, timer: null,
    persistScores: 'conScores', persistHistory: 'conHistory',
    allKeys: function(){ return S.conKeys; },
    pickItem: function(k){ return {key: k}; },
    getPrompt: function(item){ var d = {C: 'C (hard)', G: 'G (hard)'}; return d[item.key] || item.key; },
    getAnswer: function(item){ return S.conMap[item.key]; },
    normalize: function(raw){ return raw; },
    formatCorrect: function(item){ return S.conMap[item.key]; },
    placeholder: 'type the digit...',
    historyKey: function(item){ return item.key; }
  }
};

/* ================================================================== */
/*  Persistence field manifest                                         */
/* ================================================================== */
var STATE_FIELDS = [
  {key: 'score', get: function(){ return S.score; }, set: function(v){ S.score = v || {correct: 0, total: 0}; }},
  {key: 'customWords', get: function(){ return S.customWords; }, set: function(v){ S.customWords = v || {}; }}
];
Object.keys(MODES).forEach(function(name){
  var m = MODES[name];
  STATE_FIELDS.push(
    {key: m.persistScores, get: function(){ return m.scores; }, set: function(v){ m.scores = v || {}; }},
    {key: m.persistHistory, get: function(){ return m.history; }, set: function(v){ m.history = v || []; }}
  );
});

/* ================================================================== */
/*  Wordlist merge                                                     */
/* ================================================================== */
function rebuildWordlist(){
  S.wordlist = {};
  for(var k in S.defaultWordlist) S.wordlist[k] = S.defaultWordlist[k];
  for(var k in S.customWords) S.wordlist[k] = S.customWords[k];
  S.keys = Object.keys(S.wordlist).sort();
}
