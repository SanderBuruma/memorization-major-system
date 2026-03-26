# Major System Trainer

A web app for memorizing the Major System — a mnemonic technique that encodes numbers as consonant sounds, letting you turn any number into memorable words.

Built with Django, TypeScript, and SCSS.

## Features

**Grid** — A row of single-digit words (0–9) plus a 10x10 grid (00–99), giving 110 number-word pairs. Click any cell to edit. An autocomplete dropdown suggests concrete nouns that match the Major System encoding for that number.

**Quiz modes** — Four timed quiz modes that test your associations in different directions:
- **Quiz** — see a number, type the word
- **Reverse** — see a word, type the number
- **Mixed** — randomly alternates between Quiz and Reverse
- **Consonant** — see a consonant sound, type the digit

Each mode scores based on **response time**: fast answers (under 2 seconds) earn positive scores, slow answers earn negative ones. Scores are a weighted running average of your last 10 answers per number, with recent answers weighing more. The timer pauses while you're actively typing the correct answer, so only thinking time counts. A settings panel adds an optional countdown timer that adapts to mastery.

**Translate** — Convert numbers to words using your grid associations. Also supports reverse translation: paste words or sentences to see the Major System digit encoding for each word.

**Reference** — Shows the Major System sound-to-digit mapping table.

**Profile** — View your quiz statistics and score history per mode.

**Themes** — Four themes: dark (default), light, OLED, and high-contrast. Toggle via the top bar icon or the settings panel dropdown.

**Accessibility** — ARIA labels and roles throughout. OpenDyslexic font toggle in settings.

**Onboarding tutorial** — A 5-step interactive walkthrough shown automatically to new users. Can be replayed from settings.

**Accounts** — Register/login to sync state across devices. Anonymous users get IP-based state that merges into their account on registration.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/wordlist` | GET | Full 0–9 and 00–99 wordlist (110 entries) |
| `/api/mapping` | GET | Major System sound-to-digit mapping |
| `/api/state` | GET/POST | Read/write quiz state (scores, history, theme, settings) |
| `/api/candidates/<digits>` | GET | Concrete noun suggestions for a one- or two-digit number |
| `/api/encode` | POST | Encode words to Major System digits. Body: `{"text": "..."}` |

## Development

```bash
npm install
npm run build        # Build JS + CSS
npm run check        # TypeScript type-check
python manage.py runserver
```

## Deployment

Push to `master` triggers CI/CD (GitHub Actions: test, deploy to VPS).
