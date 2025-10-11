# Personagens de Harry Potter

Web Scraping de personagens da série Harry Potter.

## Como foi feito?

Utilizando bibliotecas como BeautifulSoup e selectolax, foi feito um web scraping no site [Harry Potter Wiki](https://harrypotter.fandom.com/pt-br/wiki/P%C3%A1gina_Principal) para obter os nomes dos personagens da série.

Foi criado um script que faz a requisição para cada página dos 7 livros. Cada página contém um resumo dos acontecimentos e dos personagens que aparecem em cada cena/capítulo.

O script obtém o nome do personagem e o hyperlink para a página do personagem. Com esses dados, é possível fazer um web scraping na página do personagem para obter mais informações sobre ele (data de nascimento, espécie, gênero, etc.).

## Estrutura do Projeto

```
personagens_harry_potter/
├── src/
│   └── scrapers/           # Módulos de scraping
│       ├── base.py                          # Classe base com código compartilhado
│       ├── wiki_caller_sync.py              # Versão sequencial (BeautifulSoup)
│       ├── wiki_caller_multiprocessing.py   # Versão paralela (pathos)
│       └── wiki_caller_async.py             # Versão assíncrona (aiohttp)
├── tests/                  # Testes unitários
├── data/                   # Dados de saída (CSV e DuckDB)
└── pyproject.toml          # Dependências e configurações
```

## Como executar?

### Instalação

Clone o repositório e instale as dependências usando `uv`:

```bash
git clone https://github.com/levyvix/personagens_harry_potter.git
cd personagens_harry_potter
uv sync
```

### Executando o Scraper

#### Opção 1: Interface CLI (recomendado)

```bash
# Modo padrão (multiprocessamento - ~6 segundos)
uv run python -m src.scrapers

# Modo sequencial (mais lento, mas mais seguro)
uv run python -m src.scrapers --mode sync

# Modo assíncrono
uv run python -m src.scrapers --mode async

# Especificar diretório de saída
uv run python -m src.scrapers --output-dir ./meus_dados
```

#### Opção 2: Script de conveniência

```bash
uv run python run_scraper.py --mode multiprocessing
```

#### Opção 3: Executar módulos diretamente

```bash
# Versão sequencial (BeautifulSoup)
uv run python src/scrapers/wiki_caller_sync.py

# Versão com multiprocessamento (~6 segundos)
uv run python src/scrapers/wiki_caller_multiprocessing.py

# Versão assíncrona
uv run python src/scrapers/wiki_caller_async.py
```

> ⚠️ **CUIDADO:** A versão com multiprocessamento utiliza todos os núcleos do seu processador. Se você tiver um processador com muitos núcleos, pode ser que o site bloqueie o seu IP por fazer muitas requisições em um curto espaço de tempo.

### Arquivos de Saída

Os dados são salvos no diretório `data/`:
- `personagens.csv` - Arquivo CSV com os dados dos personagens (separado por ponto-e-vírgula)
- `personagens_harry_potter.duckdb` - Banco de dados DuckDB com os mesmos dados

Lembre-se que os dados ainda precisam ser limpos e tratados para serem utilizados em um projeto de produção.

## Docker

Este repositório também possui um Dockerfile que pode ser utilizado para executar o script em um container Docker.

Para construir a imagem, execute o seguinte comando:

```bash
docker build -t personagens_harry_potter .
```

Para executar o script dentro do container (com volume para salvar os dados):

```bash
docker run -it --rm -v $(pwd)/data:/app/data personagens_harry_potter
```

Para executar com um modo específico:

```bash
docker run -it --rm personagens_harry_potter uv run python -m src.scrapers --mode async
```

## Testes

Execute os testes com pytest:

```bash
uv run pytest
```

## Arquitetura

### Classe Base (`BaseWikiCaller`)

Todas as três implementações herdam de uma classe base que centraliza:
- URLs dos 7 livros da série Harry Potter
- Configuração de logging
- Remoção de acentos para normalização de dados
- Limpeza de dados (remoção de duplicatas e filtros)
- Salvamento em CSV e DuckDB

### Implementações Específicas

Cada implementação (`WikiCallerSync`, `WikiCallerMultiprocessing`, `WikiCallerAsync`) foca apenas em sua estratégia de execução:
- **Sync**: Requisições sequenciais simples e confiáveis
- **Multiprocessing**: Processamento paralelo para máxima velocidade (~6 segundos)
- **Async**: Requisições assíncronas com `aiohttp` e `asyncio`

### Fluxo de Dados

1. **Coleta de Links**: Extrai links de personagens das páginas dos 7 livros
2. **Verificação**: Filtra apenas personagens com informações biográficas
3. **Extração de Dados**: Coleta dados detalhados de cada personagem verificado
4. **Limpeza**: Remove duplicatas e entradas inválidas (ex: autora)
5. **Salvamento**: Exporta para CSV e carrega no DuckDB

## Tecnologias Utilizadas

- **Python 3.11+**
- **BeautifulSoup4** - Parsing HTML (versão sequencial)
- **selectolax** - Parsing HTML rápido (versões paralela e assíncrona)
- **pathos** - Multiprocessamento
- **aiohttp** - Requisições HTTP assíncronas
- **DuckDB** - Banco de dados analítico
- **dlt** - Pipeline de dados para DuckDB
- **pandas** - Manipulação de dados
- **uv** - Gerenciador de pacotes Python
- **pytest** - Framework de testes
