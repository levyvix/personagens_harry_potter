# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraping project that extracts Harry Potter character data from the Portuguese Harry Potter Wiki (harrypotter.fandom.com/pt-br). The project scrapes character information from all 7 book pages and saves the data to both CSV and DuckDB formats.

## Project Structure

```
personagens_harry_potter/
├── src/
│   ├── __init__.py
│   └── scrapers/
│       ├── __init__.py
│       ├── __main__.py              # CLI entry point
│       ├── wiki_caller_sync.py      # Sequential scraper (BeautifulSoup)
│       ├── wiki_caller_multiprocessing.py  # Parallel scraper (pathos)
│       └── wiki_caller_async.py     # Async scraper (aiohttp)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_wiki_caller.py
├── data/                            # Output directory (gitignored)
│   └── .gitkeep
├── run_scraper.py                   # Convenience runner script
├── pyproject.toml                   # Project metadata & dependencies
├── Dockerfile
└── README.md
```

## Dependencies

This project uses `uv` for dependency management. Install dependencies with:

```bash
uv sync
```

Key dependencies (defined in `pyproject.toml`):
- **BeautifulSoup4**: Used in `wiki_caller_sync.py` for HTML parsing (slower)
- **selectolax**: Used in multiprocessing and async versions for faster HTML parsing
- **pathos**: Multiprocessing library for parallel execution
- **aiohttp**: Async HTTP requests
- **dlt**: Data loading tool for DuckDB integration
- **DuckDB**: Database storage
- **pandas**: Data manipulation and CSV export

## Running the Scripts

### Option 1: Using the CLI (recommended)

```bash
# Run with default settings (multiprocessing mode)
uv run python -m src.scrapers

# Specify scraping mode
uv run python -m src.scrapers --mode sync            # Sequential (slower)
uv run python -m src.scrapers --mode multiprocessing # Parallel (~6 seconds)
uv run python -m src.scrapers --mode async           # Async (aiohttp)

# Specify output directory
uv run python -m src.scrapers --output-dir ./my_data
```

### Option 2: Using the convenience script

```bash
uv run python run_scraper.py --mode multiprocessing
```

### Option 3: Running modules directly

```bash
uv run python src/scrapers/wiki_caller_sync.py
uv run python src/scrapers/wiki_caller_multiprocessing.py  # ⚠️ Uses all CPU cores
uv run python src/scrapers/wiki_caller_async.py
```

All scripts output to `data/` directory:
- `personagens.csv` - CSV file with character data (semicolon-separated)
- `personagens_harry_potter.duckdb` - DuckDB database with `harry_potter.personagens` table

## Docker

Build and run with Docker:

```bash
docker build -t personagens_harry_potter .
docker run -it --rm -v $(pwd)/data:/app/data personagens_harry_potter

# Change scraping mode
docker run -it --rm personagens_harry_potter uv run python -m src.scrapers --mode async
```

## Architecture

### WikiCaller Class

All three scripts implement a `WikiCaller` class with similar structure but different execution strategies:

**Core workflow:**
1. `get_data()` / `get_book_data()`: Fetches character links from all 7 book pages
2. `verify_links()` / `verify_href()`: Filters links to only include characters with biographical information
3. `get_char_data()`: Extracts detailed character info from each verified character page
4. `save_to_csv()` / `save_dataframe()`: Exports to CSV
5. `save_data_to_duckdb()`: Loads data into DuckDB using dlt pipeline

**Character verification:**
Characters are included only if their wiki page contains either:
- A "Nascimento" (birth) banner (`have_banner()`)
- "Informações biográficas" section (`have_informacoes_bibliograficas()`)

This filters out non-character pages like locations, spells, etc.

**Data handling:**
- Response caching is implemented in all versions to avoid duplicate requests
- Character data is extracted from wiki infoboxes using CSS selectors
- Duplicate characters are removed based on "Nome" field
- "Joanne Rowling" (the author) is explicitly filtered out
- Accents are removed from column names for consistency

### Implementation Differences

- **get_data.py**: Sequential requests with BeautifulSoup, simple and reliable
- **get_data_multiprocessing.py**: Uses `pathos.multiprocessing.ProcessingPool` and selectolax for speed
- **get_data_async.py**: Uses `asyncio` and `aiohttp` with async/await pattern

## Testing

pytest is configured with `pythonpath = src` in `pytest.ini`, but there are currently no test files in the repository.

## Data Cleaning Notes

The README notes that data still needs cleaning and treatment before use in production projects. Consider implementing validation for:
- Character name normalization
- Handling missing/incomplete biographical data
- Deduplication beyond just the "Nome" field
