# Watchlist Data Manager

[![CI](https://github.com/YevhenKoval01/Watchlist-Data-Manager/actions/workflows/ci.yml/badge.svg)](https://github.com/YevhenKoval01/Watchlist-Data-Manager/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-41%20passed-2E7D32)
![Coverage](https://img.shields.io/badge/coverage-75%25%2B-2E7D32)
![License](https://img.shields.io/badge/license-MIT-blue)

A tested command-line application for managing a personal movie watchlist.
It combines validated CRUD operations, flexible discovery tools, useful
statistics, portable exports, and reliable local JSON persistence.

The project began as a single-file university assignment at the
Polish-Japanese Academy of Information Technology (PJATK). It has since been
redesigned as a maintainable Python package with separated responsibilities,
automated tests, and continuous integration.

## Features

- Add, list, edit, and delete movies
- Track `planned` and `watched` statuses with automatic watch timestamps
- Validate titles, years, ratings, statuses, and persisted records
- Search across titles, directors, and genres
- Filter by status, exact genre, and minimum rating
- Sort by title, year, genre, rating, or status
- Recommend a random planned movie, optionally from a selected genre
- Calculate completion, rating, and genre statistics
- Display optional Matplotlib charts
- Export the collection as a UTF-8 tab-separated file
- Save data safely through atomic file replacement
- Read legacy status values from the original Polish dataset

## Demo

```text
===== WATCHLIST DATA MANAGER =====
1. Add a movie
2. List the collection
3. Search
4. Edit a movie
5. Delete a movie
6. Sort and display
7. Export to TSV
8. Show statistics
9. Filter the collection
10. Recommend a planned movie
0. Exit

Choose an option: 10
Preferred genre (optional): Science Fiction
Recommendation: Arrival (2016) - Science Fiction
```

## Technology

- Python 3.10+
- Standard library: `argparse`, `csv`, `dataclasses`, `json`, `pathlib`,
  `statistics`, and `tempfile`
- Matplotlib for optional visualizations
- pytest and pytest-cov
- Ruff
- GitHub Actions
- `pyproject.toml` packaging with a `src/` layout

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/YevhenKoval01/Watchlist-Data-Manager.git
   cd Watchlist-Data-Manager
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   Linux or macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Install the application:

   ```bash
   python -m pip install --upgrade pip
   pip install -e .
   ```

   Include chart support:

   ```bash
   pip install -e ".[charts]"
   ```

## Usage

Start the interactive application:

```bash
watchlist
```

The command creates `watchlist.json` in the current directory when the first
change is saved. This local file is ignored by Git.

Use a custom database:

```bash
watchlist --database path/to/my_movies.json
```

Explore the included example without creating a new database:

```bash
watchlist --database examples/sample_watchlist.json
```

Show command-line help or the installed version:

```bash
watchlist --help
watchlist --version
```

## Data Format

Movies are stored as readable UTF-8 JSON:

```json
[
  {
    "title": "Arrival",
    "director": "Denis Villeneuve",
    "year": 2016,
    "genre": "Science Fiction",
    "status": "watched",
    "rating": 9,
    "description": "A linguist attempts to communicate with alien visitors.",
    "watched_on": "2026-01-10T20:15:00+01:00"
  }
]
```

Every record is validated while loading. Invalid JSON, unsupported statuses,
incorrect field types, and out-of-range values produce clear error messages
instead of silently damaging the collection.

## Architecture

```text
.
|-- .github/workflows/ci.yml       # Automated linting and tests
|-- examples/sample_watchlist.json # Sanitized example collection
|-- src/watchlist_manager/
|   |-- cli.py                     # Interactive terminal interface
|   |-- models.py                  # Domain model and validation rules
|   |-- repository.py              # Atomic JSON persistence
|   |-- service.py                 # CRUD, search, filters, and analytics
|   `-- export.py                  # Tab-separated export
|-- tests/                         # Automated test suite
|-- pyproject.toml                 # Packaging and tool configuration
`-- README.md
```

The CLI depends on `WatchlistService`, while the service communicates with a
small repository interface. This keeps user interaction, business rules, and
file operations independently testable.

## Quality Checks

Install the development dependencies:

```bash
pip install -e ".[dev]"
```

Run the same checks used by CI:

```bash
ruff check .
pytest --cov=watchlist_manager --cov-report=term-missing
python -m compileall -q src tests
```

The suite currently contains 41 tests covering validation, JSON persistence,
CRUD operations, searching, filtering, recommendations, sorting, statistics,
exports, and key CLI workflows. The configured minimum coverage is 75%.

## Project Status

Version `1.1.0` is feature-complete for its educational and portfolio scope.
Possible future improvements include CSV import, tags, and a small web API.

## License

Distributed under the [MIT License](LICENSE).
