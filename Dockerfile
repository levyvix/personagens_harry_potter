FROM python:3.11-slim

# Set the working directory
WORKDIR /app

COPY get_data_multiprocessing.py requirements.txt /app/

# Install the dependencies
RUN python3 -m pip install -r requirements.txt --no-cache-dir

# Run the container
CMD ["python3", "get_data_multiprocessing.py"]