FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy project files
COPY src/ /app/src/
COPY pyproject.toml /app/
COPY run_scraper.py /app/

# Install uv
RUN pip install uv --no-cache-dir

# Install dependencies using uv
RUN uv sync --no-dev

# Create data directory
RUN mkdir -p /app/data

# Run the scraper (default: multiprocessing mode)
CMD ["uv", "run", "python", "-m", "src.scrapers", "--mode", "multiprocessing", "--output-dir", "/app/data"]