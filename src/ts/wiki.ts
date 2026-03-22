import { appState } from './state';
import { MATH_CONSTANTS } from './constants';
import { escapeHTML } from './utils';

interface WikiArticle { title: string; content: string | (() => string); }
interface WikiCategory { name: string; icon: string; articles: WikiArticle[]; }

/** Mnemonics for the digit-consonant mapping, keyed by digit. */
const MAPPING_MNEMONICS: Record<string, string> = {
  '0': '<em>z</em>ero starts with Z',
  '1': 'T/D have one downstroke',
  '2': 'N has two downstrokes',
  '3': 'M has three downstrokes',
  '4': '"fou<em>r</em>" ends in R',
  '5': 'L is the Roman numeral for 50',
  '6': 'J mirrored looks like 6',
  '7': 'K contains two 7-shapes',
  '8': 'Script f looks like 8',
  '9': 'P mirrored looks like 9',
};

/** Build a mapping table from appState.mapping. */
function mappingTable(): string {
  let rows = '';
  for (let d = 0; d <= 9; d++) {
    const sounds = escapeHTML(appState.mapping[String(d)] ?? '');
    const mnemonic = MAPPING_MNEMONICS[String(d)] ?? '';
    rows += `<tr><td><strong>${d}</strong></td><td>${sounds}</td><td>${mnemonic}</td></tr>`;
  }
  return `<table class="ref-table"><thead><tr><th>Digit</th><th>Sounds</th><th>Mnemonic</th></tr></thead><tbody>${rows}</tbody></table>`;
}

/** Build an example list from the user's current wordlist. */
function wordExamples(keys: string[]): string {
  return '<ul>' + keys.filter(k => k.length >= 2).map(k => {
    const word = escapeHTML(appState.wordlist[k] ?? '???');
    const sounds = (appState.mapping[k[0]] ?? '').split(', ')[0];
    const sounds2 = (appState.mapping[k[1]] ?? '').split(', ')[0];
    return `<li><strong>${escapeHTML(k)}</strong> → "${word}" (${escapeHTML(sounds)}=${escapeHTML(k[0])}, ${escapeHTML(sounds2)}=${escapeHTML(k[1])})</li>`;
  }).join('') + '</ul>';
}

/** Render the first word from the wordlist as an inline example. */
function inlineExample(key: string): string {
  if (key.length < 2) return `<em>(invalid key "${escapeHTML(key)}")</em>`;
  const word = escapeHTML(appState.wordlist[key] ?? '???');
  const d0 = key[0], d1 = key[1];
  const s0 = escapeHTML((appState.mapping[d0] ?? '').split(', ')[0]);
  const s1 = escapeHTML((appState.mapping[d1] ?? '').split(', ')[0]);
  return `the word <strong>"${word}"</strong> encodes <strong>${escapeHTML(key)}</strong> because ${s0} = ${escapeHTML(d0)} and ${s1} = ${escapeHTML(d1)}`;
}

/** Curated single-digit nouns: vivid, concrete, easy to visualize. */
const SINGLE_DIGIT_WORDS: Record<string, string> = {
  '0': 'sea', '1': 'tie', '2': 'knee', '3': 'maw', '4': 'aura',
  '5': 'oil', '6': 'shoe', '7': 'cow', '8': 'fur', '9': 'pie',
};

/** Show one curated noun per digit (0–9) with its consonant sounds. */
function singleDigitExamples(): string {
  return '<ul>' + Array.from({ length: 10 }, (_, d) => {
    const word = escapeHTML(SINGLE_DIGIT_WORDS[String(d)] ?? '???');
    const sounds = escapeHTML(appState.mapping[String(d)] ?? '');
    return `<li><strong>${d}</strong> → ${sounds} — "${word}"</li>`;
  }).join('') + '</ul>';
}

/** Build the list of math constant symbols from MATH_CONSTANTS. */
function constantSymbols(): string {
  return MATH_CONSTANTS.map(c => `<strong>${escapeHTML(c.symbol)}</strong>`).join(', ');
}

const WIKI_DATA: WikiCategory[] = [
  {
    name: 'Getting Started',
    icon: '🚀',
    articles: [
      {
        title: 'What is the Major System?',
        content: () => `
<p>The <strong>Major System</strong> is a mnemonic technique that converts <strong>numbers into words</strong> by mapping each digit (0–9) to one or more consonant sounds.</p>
<p>Vowels and the sounds <em>W</em>, <em>H</em>, and <em>Y</em> carry no numeric value — they are "free" glue you use to form real words. Only consonant sounds matter, and <strong>spelling is irrelevant</strong>; what counts is how the word <em>sounds</em>.</p>
<p>For example, ${inlineExample('14')}. The vowels are ignored.</p>
<p>By turning abstract numbers into vivid, concrete images, you can memorize long sequences (phone numbers, PINs, dates, constants like π) far more easily than by rote repetition.</p>`,
      },
      {
        title: 'Digit–Consonant Mapping',
        content: () => `
${mappingTable()}
<p>Remember: <strong>sounds, not letters</strong>. Silent letters are ignored entirely, and what matters is pronunciation, not spelling.</p>`,
      },
      {
        title: 'Your First Words',
        content: () => `
<p>Each single digit maps to a consonant sound. Here is one word per digit from your wordlist:</p>
${singleDigitExamples()}
<p>Two-digit numbers combine two consonants into one word:</p>
${wordExamples(['00', '14', '27', '53', '91'])}
<p>The app provides a default word for every pair, but you can <strong>replace any word</strong> with one that is more memorable to you. Concrete, vivid nouns work best — something you can picture clearly.</p>
<p>Tip: start by learning the digit-consonant mapping cold, then the words will follow naturally.</p>`,
      },
    ],
  },
  {
    name: 'The Grid',
    icon: '📋',
    articles: [
      {
        title: 'Using the Grid',
        content: `
<p>The <strong>Grid</strong> view is your home screen. It shows all 110 number-word pairs in the grid: a top row of single-digit words (0–9) followed by a 10×10 block of two-digit pairs (00–99).</p>
<p>Each cell displays the number and the word currently assigned to it. Click any cell to edit its word.</p>
<p>The grid is your reference and workspace — browse it to review your words, or use it to spot gaps in your knowledge.</p>`,
      },
      {
        title: 'Custom Words',
        content: `
<p>Every number comes with a default word, but you can <strong>type your own word</strong> into any cell to override it.</p>
<p>Custom words are marked with an asterisk (<strong>*</strong>) next to the number. They persist across sessions and sync to the server if you're logged in.</p>
<p>When you focus a cell, an <strong>autocomplete dropdown</strong> shows alternative words that correctly encode that number. You can pick from the suggestions or type any word you like (it must start with a lowercase letter).</p>
<p>To revert to the default, simply clear the cell or type the original word back in.</p>`,
      },
      {
        title: 'Mastery Colors',
        content: `
<p>Grid cells are color-coded based on how well you know each number across the quiz modes:</p>
<ul>
  <li><strong style="color:var(--color-mastery-0)">Red</strong> — not yet practiced or very low score</li>
  <li><strong style="color:var(--color-mastery-1)">Orange</strong> — some practice, still shaky</li>
  <li><strong style="color:var(--color-primary)">Blue</strong> — moderate mastery</li>
  <li><strong style="color:var(--color-mastery-3)">Green</strong> — good mastery</li>
  <li><strong style="color:var(--color-mastery-4)">Bright green</strong> — fully mastered</li>
</ul>
<p>Your combined score from the Number→Word, Word→Number, and Mixed quizzes determines each cell's level. Keep quizzing to turn the whole grid green!</p>`,
      },
    ],
  },
  {
    name: 'Quiz Modes',
    icon: '❓',
    articles: [
      {
        title: 'Number → Word',
        content: `
<p>You see a <strong>number</strong> (single- or two-digit) and must type the corresponding word from your wordlist.</p>
<p>The quiz uses <strong>spaced repetition</strong> — numbers you get wrong or skip come back more often, while mastered numbers appear less frequently.</p>
<p>Press <strong>Enter</strong> to submit, or click Skip to reveal the answer and move on.</p>`,
      },
      {
        title: 'Word → Number',
        content: `
<p>The reverse direction: you see a <strong>word</strong> and must type the <strong>number</strong> it encodes (single- or two-digit).</p>
<p>This mode tests whether you can go from an image back to its number — essential for practical use of the Major System.</p>`,
      },
      {
        title: 'Mixed Mode',
        content: `
<p>Randomly alternates between Number→Word and Word→Number within the same session.</p>
<p>Mixed mode is the best test of true fluency: you never know which direction is coming next, so you must know the pairs both ways.</p>`,
      },
      {
        title: 'Sound → Digit',
        content: `
<p>Tests the <strong>fundamental mapping</strong> directly. You see a consonant sound and must type the single digit it represents.</p>
<p>This is the foundation — if you can instantly recall the digit for any consonant sound, word encoding becomes effortless.</p>`,
      },
      {
        title: 'Grid Quiz',
        content: `
<p>A timed challenge: all 110 numbers appear <strong>shuffled</strong> with blank inputs. Fill in as many words as you can, then click <strong>Check All</strong>.</p>
<p>Correct cells turn green, wrong ones turn red with the expected answer shown. A timer tracks how long you take.</p>
<p>This mode is great for measuring overall coverage and speed.</p>`,
      },
    ],
  },
  {
    name: 'Tools',
    icon: '🔧',
    articles: [
      {
        title: 'Reference Table',
        content: `
<p>The <strong>Reference</strong> view shows the complete digit-to-consonant mapping in a simple table.</p>
<p>Use it as a quick lookup while you're still learning the system. Once you have the mapping memorized, you won't need it anymore.</p>`,
      },
      {
        title: 'Translate Tool',
        content: `
<p>The <strong>Translate</strong> view has two converters:</p>
<ul>
  <li><strong>Number → Words</strong>: type any digit string and see the corresponding words from your wordlist, split into two-digit chunks.</li>
  <li><strong>Words → Number</strong>: type words and see the digit string they encode, using phonetic analysis.</li>
</ul>
<p>Use this to encode phone numbers, dates, PINs, or any number you want to memorize.</p>`,
      },
      {
        title: 'Math Constants',
        content: () => `
<p>Above the Number→Words input, you'll find buttons for common mathematical constants: ${constantSymbols()}.</p>
<p>Click one to load its first digits into the translator — a fun way to practice memorizing long constants using the Major System.</p>`,
      },
    ],
  },
  {
    name: 'Profile & Progress',
    icon: '📊',
    articles: [
      {
        title: 'Activity Heatmap',
        content: `
<p>The heatmap shows your <strong>daily practice activity</strong> over time, similar to a GitHub contribution graph.</p>
<p>Each cell represents one day — darker colors mean more quiz questions answered that day. Consistent daily practice builds the strongest recall.</p>`,
      },
      {
        title: 'Mastery Stats',
        content: `
<p>The Profile page shows a <strong>mastery distribution</strong> bar chart — how many of your 110 numbers fall into each mastery level (red through green).</p>
<p>Below that, <strong>coverage percentages</strong> show how many numbers you've practiced at least once in each quiz mode.</p>
<p>Your goal: get all 110 numbers to bright green mastery.</p>`,
      },
      {
        title: 'Score Tracking',
        content: `
<p>Your overall <strong>correct/total</strong> score is tracked across all quiz modes and persisted to the server when logged in.</p>
<p>Each quiz mode also shows a <strong>rolling accuracy</strong> for your last 100 guesses, giving you a real-time sense of your current performance.</p>`,
      },
    ],
  },
  {
    name: 'Settings',
    icon: '⚙️',
    articles: [
      {
        title: 'Themes',
        content: `
<p>Choose from four color themes:</p>
<ul>
  <li><strong>Dark</strong> — default dark theme, easy on the eyes</li>
  <li><strong>Light</strong> — bright background for well-lit environments</li>
  <li><strong>OLED</strong> — pure black background, saves battery on OLED screens</li>
  <li><strong>High Contrast</strong> — meets WCAG AAA accessibility guidelines, yellow text on black</li>
</ul>
<p>You can also toggle themes quickly using the button in the top-right corner of the topbar.</p>`,
      },
      {
        title: 'Timed Quiz',
        content: `
<p>When enabled, quiz questions have a <strong>countdown timer</strong>. If time runs out, the question is automatically skipped.</p>
<p>The timer adapts to mastery: numbers you know well get <strong>less time</strong>, pushing you to respond faster. Numbers you're still learning get a generous window.</p>`,
      },
      {
        title: 'Dyslexia Font',
        content: `
<p>Toggles the entire app to use <strong>OpenDyslexic</strong>, a typeface designed to improve readability for people with dyslexia.</p>
<p>The font uses weighted bottoms and unique letterforms to reduce letter confusion.</p>`,
      },
      {
        title: 'Import & Export Wordlists',
        content: `
<p>You can <strong>export</strong> your current wordlist (including custom overrides) as CSV or JSON for backup or sharing.</p>
<p>To <strong>import</strong>, upload a CSV file with <code>number,word</code> rows, or a JSON file with <code>{"00": "word", ...}</code> format.</p>
<p>Imported words that match the defaults are treated as defaults; different words become custom overrides.</p>`,
      },
    ],
  },
];

function resolveContent(content: string | (() => string)): string {
  return typeof content === 'function' ? content() : content;
}

export function renderWiki(): void {
  renderWikiCategories();
}

function renderWikiCategories(): void {
  const el = document.getElementById('wiki-content')!;
  el.innerHTML = '<h2 class="wiki-title">Wiki</h2>' +
    '<div class="wiki-cards">' +
    WIKI_DATA.map((cat, i) =>
      `<button class="wiki-card" onclick="showWikiCategory(${i})">` +
      `<span class="wiki-card-icon">${cat.icon}</span>` +
      `<span class="wiki-card-name">${cat.name}</span>` +
      `<span class="wiki-card-count">${cat.articles.length} article${cat.articles.length !== 1 ? 's' : ''}</span>` +
      `</button>`
    ).join('') +
    '</div>';
}

export function showWikiCategory(index: number): void {
  if (index < 0 || index >= WIKI_DATA.length) return;
  const cat = WIKI_DATA[index];
  const el = document.getElementById('wiki-content')!;
  el.innerHTML =
    `<nav class="wiki-breadcrumb">` +
    `<button onclick="renderWiki()">Wiki</button> <span class="wiki-sep">/</span> <span>${cat.name}</span>` +
    `</nav>` +
    `<h2 class="wiki-title">${cat.icon} ${cat.name}</h2>` +
    '<div class="wiki-article-list">' +
    cat.articles.map((a, i) =>
      `<button class="wiki-article-item" onclick="showWikiArticle(${index},${i})">` +
      `<span class="wiki-article-title">${a.title}</span>` +
      `<span class="wiki-article-arrow">›</span>` +
      `</button>`
    ).join('') +
    '</div>';
}

export function showWikiArticle(catIndex: number, artIndex: number): void {
  if (catIndex < 0 || catIndex >= WIKI_DATA.length) return;
  const cat = WIKI_DATA[catIndex];
  if (artIndex < 0 || artIndex >= cat.articles.length) return;
  const art = cat.articles[artIndex];
  const el = document.getElementById('wiki-content')!;

  const prevIdx = artIndex > 0 ? artIndex - 1 : null;
  const nextIdx = artIndex < cat.articles.length - 1 ? artIndex + 1 : null;

  el.innerHTML =
    `<nav class="wiki-breadcrumb">` +
    `<button onclick="renderWiki()">Wiki</button> <span class="wiki-sep">/</span> ` +
    `<button onclick="showWikiCategory(${catIndex})">${cat.name}</button> <span class="wiki-sep">/</span> ` +
    `<span>${art.title}</span>` +
    `</nav>` +
    `<article class="wiki-article">` +
    `<h2>${art.title}</h2>` +
    resolveContent(art.content) +
    `</article>` +
    `<div class="wiki-article-nav">` +
    (prevIdx !== null
      ? `<button class="wiki-nav-btn" onclick="showWikiArticle(${catIndex},${prevIdx})">← ${cat.articles[prevIdx].title}</button>`
      : '<span></span>') +
    (nextIdx !== null
      ? `<button class="wiki-nav-btn" onclick="showWikiArticle(${catIndex},${nextIdx})">${cat.articles[nextIdx].title} →</button>`
      : '<span></span>') +
    '</div>';
}
