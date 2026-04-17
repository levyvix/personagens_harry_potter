# Personagens Harry Potter


Scraper simples em Python para coletar dados de personagens do Harry Potter Wiki (pt-br) e salvar em CSV e DuckDB.

## Requisitos

- Python 3.11+
- `uv`

## Instalação

```bash
git clone https://github.com/levyvix/personagens_harry_potter.git
cd personagens_harry_potter
uv sync
```

## Uso

```bash
# padrão: multiprocessing
uv run python -m src.scrapers

# modos disponíveis
uv run python -m src.scrapers --mode sync
uv run python -m src.scrapers --mode multiprocessing
uv run python -m src.scrapers --mode async
```

Atalho:

```bash
uv run python run_scraper.py --mode async
```

## Saída

Arquivos gerados na raiz do projeto:

- `personagens.csv`
- `personagens_harry_potter.duckdb`

## Testes e lint

```bash
uv run pytest
uv run ruff check .
```

## Estrutura

- `src/scrapers/base.py`: lógica compartilhada
- `src/scrapers/wiki_caller_sync.py`: versão sequencial
- `src/scrapers/wiki_caller_multiprocessing.py`: versão paralela
- `src/scrapers/wiki_caller_async.py`: versão assíncrona
- `tests/`: testes
