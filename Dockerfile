# Use Python 3.11 slim image (faster than 3.13 for ML workloads)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install Python dependencies with Docker build cache
# This will cache pip packages between builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -e .

# Copy source code (changes frequently, so put after dependencies)
COPY src/ ./src/
COPY main.py create_dummy_data.py test_agent.py run_agent_test.py ./
COPY alembic/ ./alembic/
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_PATH=/app/data

# Expose port for FastAPI
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "main.py"]
