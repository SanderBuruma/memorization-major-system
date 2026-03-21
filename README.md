# Major System Trainer

A web app for memorizing the Major System — a mnemonic technique that encodes numbers as consonant sounds, letting you turn any number into memorable words.

Built with Django, TypeScript, and SCSS.

## Features

**Grid** — 10x10 grid (00–99) where you assign a word to each two-digit number. Click any cell to edit. An autocomplete dropdown suggests concrete nouns that match the Major System encoding for that number.

**Quiz modes** — Four timed quiz modes that test your associations in different directions:
- **Quiz** — see a number, type the word
- **Reverse** — see a word, type the number
- **Mixed** — randomly alternates between Quiz and Reverse
- **Consecutive** — numbers in sequence (00, 01, 02, ...)

Each mode tracks per-number scores and history independently. A settings panel controls timer duration.

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
| `/api/wordlist` | GET | Full 00–99 wordlist |
| `/api/mapping` | GET | Major System sound-to-digit mapping |
| `/api/state` | GET/POST | Read/write quiz state (scores, history, theme, settings) |
| `/api/candidates/<digits>` | GET | Concrete noun suggestions for a two-digit number |
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
