# Major System Trainer — Documentation

A Python/Django application for memorizing the [Major System](https://en.wikipedia.org/wiki/Mnemonic_major_system) (00–99) using phoneme-validated concrete noun associations, with a browser-based quiz interface and server-side state persistence.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design, data flow, module boundaries, phoneme mapping |
| [Getting Started](getting-started.md) | Prerequisites, setup, running the app |
| [File Reference](file-reference.md) | Every source file with line counts, function locations |

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8080   # http://localhost:8080
python manage.py test             # run all test suites
```

## How It Works

1. **Generator** pulls all concrete nouns from WordNet, filters by concreteness (must trace to `physical_entity.n.01`)
2. Each noun is encoded via the CMU Pronouncing Dictionary into Major System digits
3. For each number 00–99, the shortest matching noun is selected
4. A test suite validates every association (noun status, encoding, concreteness)
5. A Django app serves the wordlist to a single-page frontend with grid view, four quiz modes (score-based selection with cooldown), and server-side state persistence
6. Frontend is offline-first: loads from localStorage immediately, syncs to server in background
