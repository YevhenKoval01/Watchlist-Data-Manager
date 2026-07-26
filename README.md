# Watchlist Data Manager

Watchlist Data Manager is a local command-line application for organizing a
movie collection. It supports validated CRUD operations, text search, sorting,
statistics, TSV export, optional Matplotlib charts, and JSON persistence.

This repository began as a single-file university assignment and is being
refactored into a tested Python package suitable for continued development.

## Current Capabilities

- Add, list, edit, and delete watchlist entries
- Track planned and watched movies with optional ratings
- Search by title, director, or genre
- Sort without changing the stored collection order
- Calculate rating and genre statistics
- Export the collection as a UTF-8 tab-separated file
- Save JSON data through atomic file replacement
- Read legacy Polish status values from the original dataset

## Requirements

- Python 3.10 or newer
- Matplotlib is optional and only required for charts

## Development Setup

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

3. Install the package and development tools:

   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev,charts]"
   ```

## Run the Application

Start with an empty local database:

```bash
watchlist
```

Choose another database file:

```bash
watchlist --database examples/sample_watchlist.json
```

The default `watchlist.json` file contains personal application data and is
ignored by Git.

## Quality Checks

```bash
pytest
ruff check .
python -m compileall -q src tests
```

## Project Structure

```text
.
|-- examples/                    # Sanitized example data
|-- src/watchlist_manager/
|   |-- cli.py                   # Interactive terminal interface
|   |-- models.py                # Domain model and validation
|   |-- repository.py            # Atomic JSON persistence
|   |-- service.py               # CRUD, search, sorting, and statistics
|   `-- export.py                # Tab-separated export
|-- tests/                       # Automated test suite
|-- pyproject.toml               # Packaging and tool configuration
`-- README.md
```

## Refactoring Status

The first refactoring phase establishes the package architecture, validated
domain model, persistence boundary, and automated tests. The next phase will
focus on richer commands, stronger recovery behavior, CI, and final portfolio
documentation.
