# Major System Trainer — Documentation

A Python application for memorizing the [Major System](https://en.wikipedia.org/wiki/Mnemonic_major_system) (00–99) using phoneme-validated concrete noun associations, with a browser-based quiz interface.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design, data flow, module boundaries, phoneme mapping |
| [Getting Started](getting-started.md) | Prerequisites, setup, running the app |
| [File Reference](file-reference.md) | Every source file with line counts, function locations |

## Quick Start

```bash
pip install -r requirements.txt
python server.py          # http://localhost:8080
python -m unittest test_associations   # run validation suite
```

## How It Works

1. **Generator** pulls all concrete nouns from WordNet, filters by concreteness (must trace to `physical_entity.n.01`)
2. Each noun is encoded via the CMU Pronouncing Dictionary into Major System digits
3. For each number 00–99, the shortest matching noun is selected
4. A test suite validates every association (noun status, encoding, concreteness)
5. A lightweight HTTP server serves the wordlist to a single-page frontend with grid view and two quiz modes
