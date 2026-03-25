# Technology Stack

**Analysis Date:** 2026-03-25

## Languages

**Primary:**
- Python 3.13 - Django backend, word list generation, phoneme encoding logic
- TypeScript 5.7.0 - Frontend application logic, quiz engine, state management
- HTML/CSS - Template rendering, styling

**Secondary:**
- JavaScript/ES2020 - Frontend execution (TypeScript compiled to IIFE bundle)
- SCSS 1.98.0 - Stylesheet preprocessing, theme variables, responsive design

## Runtime

**Environment:**
- Python 3.13 (development) / Python 3.12+ (production via venv)
- Node.js 22 (development for build tools)
- Gunicorn (production WSGI application server)

**Package Manager:**
- pip (Python)
- npm (JavaScript/TypeScript)
- Lockfiles: `requirements.txt`, `package-lock.json` (both present)

## Frameworks

**Core:**
- Django 5.1+ - Web framework, ORM, authentication, static files management
- esbuild 0.25.12 - TypeScript bundler (IIFE format, single-file output)
- Sass 1.98.0 - CSS preprocessing, theme variables via custom properties

**Testing:**
- Django TestCase (built-in) - Python backend testing
- `unittest` module (implicit via Django TestCase)

**Build/Dev:**
- esbuild - Fast TypeScript/JavaScript bundler
- TypeScript compiler - Type checking via `tsc --noEmit`
- Sass CLI - CSS compilation with compression, no source maps

## Key Dependencies

**Critical:**
- cmudict >= 1.0.0 - CMU Pronouncing Dictionary for phoneme-based word encoding
- nltk >= 3.8 - Natural Language Toolkit for WordNet corpus (concrete noun filtering)
- mpmath >= 1.3 - Arbitrary-precision arithmetic (used in pi-digits reference data)
- setuptools - Python package management

**Infrastructure:**
- gunicorn - WSGI HTTP server for production deployment
- Django 5.1+ contrib.staticfiles - Static file collection and manifest-based cache busting via `ManifestStaticFilesStorage`

## Configuration

**Environment:**
- `DJANGO_SECRET_KEY` - Django secret (required for production)
- `DJANGO_DEBUG` - Debug mode flag (defaults to '0')
- `DJANGO_ALLOWED_HOSTS` - Comma-separated list of allowed hosts (defaults to 'localhost,127.0.0.1')
- Application uses `.env` file pattern (file paths noted but not read per security protocol)

**Build:**
- `tsconfig.json` - TypeScript configuration (strict mode, ES2020 target, bundler module resolution)
- esbuild produces single IIFE bundle: `static/js/app.js` (not committed; built via CI)
- Sass produces single compressed output: `static/css/app.css` (not committed; built via CI)

## Platform Requirements

**Development:**
- Python 3.13 with venv support
- Node.js 22 with npm
- Bash (for build scripts)

**Production:**
- Linux-compatible server with Python 3.12+ runtime
- HTTP server capable of serving static files (Gunicorn + Nginx reverse proxy typical)
- SQLite3 database (or PostgreSQL with minimal changes to `settings.py`)
- Memory for NLTK/WordNet corpus caching (~150MB once loaded)

## Build Pipeline

**JavaScript/TypeScript:**
```bash
npm run build:js    # esbuild bundle to static/js/app.js
npm run check       # tsc --noEmit (type check) + full build
```

**CSS:**
```bash
npm run build:css   # sass compilation to static/css/app.css
npm run build       # Both JS and CSS build steps
```

**Python:**
```bash
python manage.py test          # Django test runner (CI)
python manage.py collectstatic # Hash all static files for cache-busting
```

**CI/CD:**
- GitHub Actions (`.github/workflows/deploy.yml`)
- Triggers on push to `master` branch (skips on .md file changes)
- Runs: Node 22 type check + npm build → Python 3.13 tests → SSH deploy via VPS

---

*Stack analysis: 2026-03-25*
