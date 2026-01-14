# Base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
# Added arize-phoenix and opentelemetry-exporter-otlp for tracing
RUN pip install pandas pyarrow langgraph fastapi scikit-learn langchain langchain-google-genai arize-phoenix opentelemetry-exporter-otlp

# Copy application code
COPY ./src/app /app

# Set the environment variable for the data path
ENV DATA_PATH=/app/data

# The command to run the application will be in docker-compose.yml
# For example: CMD ["python", "main.py"]
