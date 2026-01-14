# VyvchAI Multi-Agent Tutor System - Docker Setup Guide

This guide will help you run the VyvchAI multi-agent AI tutor system in Docker and test its functionality.

## 🏗️ Architecture Overview

The system consists of:
- **FastAPI Application**: REST API for the tutor system
- **Multi-Agent System**: Supervisor + Specialist agents (Content, Solver, Grader, Analyst)
- **LapaLLM Integration**: Primary LLM with OpenAI-compatible API
- **Vector Database**: Qdrant for RAG functionality
- **Cache**: Redis for semantic caching
- **Tracing**: Phoenix UI for observability

## 📋 Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- Internet connection for pulling images

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (at minimum, keep LapaLLM as-is)
nano .env
```

### 2. Build and Run

```bash
# Standard build (recommended for first time)
docker-compose up --build

# Fast build with PyTorch pre-installed (much faster!)
docker-compose -f docker-compose.yml -f docker-compose.fast.yml up --build

# Or run in background
docker-compose up --build -d
```

### 3. Check Services Status

```bash
# Check if all containers are running
docker-compose ps

# View logs
docker-compose logs ai-tutor
```

### 4. Test the System

```bash
# Run the test script
python test_agent.py
```

## 🔍 Service Endpoints

Once running, access these services:

- **FastAPI Application**: http://localhost:8000
  - Health check: `GET /`
  - API docs: http://localhost:8000/docs

- **Phoenix Tracing UI**: http://localhost:6006

- **Qdrant Dashboard**: http://localhost:6333/dashboard

- **Redis**: localhost:6379

- **PostgreSQL**: localhost:5432

## 🧪 Testing the Agent System

### Option 1: Direct Agent Test

```bash
# Run the test script
python test_agent.py
```

### Option 2: Manual API Testing

```bash
# Test FastAPI health
curl http://localhost:8000/

# Test agent execution (if you add agent endpoints)
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant",
    "user_query": "Поясни квадратні рівняння",
    "student_profile": {"grade": 8, "subject": "algebra"}
  }'
```

### Option 3: Interactive Testing

```bash
# Enter the running container
docker-compose exec ai-tutor bash

# Run Python tests inside container
python -c "
from src.llm.lapa_client import LapaLLMClient
from src.agent.supervisor import SupervisorAgent
print('✅ All imports successful')
"
```

## ⚡ Build Optimization

### Why Builds Are Slow

The first build can take **10-20 minutes** because it needs to:
- Download the Python base image (~200MB)
- Install system dependencies (gcc, g++)
- Download and install **heavy ML packages**:
  - PyTorch (~2GB)
  - Transformers (~1GB)
  - Other dependencies (~500MB)

### Speed Up Builds

#### Option 1: Use Fast Dockerfile (Recommended)
```bash
# Uses PyTorch base image - 3x faster builds!
docker-compose -f docker-compose.yml -f docker-compose.fast.yml up --build
```

#### Option 2: Build Caching Tips
```bash
# Don't rebuild if only code changes
docker-compose up  # No --build flag

# Clear cache only when dependencies change
docker system prune -a

# Use buildkit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build
```

#### Option 3: Development Mode
```bash
# Mount code as volume - instant code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Build Time Comparison

| Method | First Build | Subsequent Builds | Use Case |
|--------|-------------|-------------------|----------|
| Standard | 15-20 min | 2-3 min | Production |
| Fast Dockerfile | 5-8 min | 1-2 min | Development/Testing |
| Dev Mode | 15-20 min | < 30 sec | Active Development |

## 🐛 Troubleshooting

### Common Issues

**1. Port conflicts**
```bash
# Check what's using ports
netstat -tulpn | grep :8000
# Stop conflicting services or change ports in docker-compose.yml
```

**2. Memory issues**
```bash
# Increase Docker memory limit to 4GB+
# Docker Desktop: Settings > Resources > Memory
```

**3. Build failures**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**4. Database connection issues**
```bash
# Check database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up db -d
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs ai-tutor

# Follow logs in real-time
docker-compose logs -f ai-tutor

# Check container resource usage
docker stats
```

## 📊 Monitoring

### Phoenix Tracing
1. Open http://localhost:6006
2. Run agent tests to see traces
3. Analyze performance and errors

### Application Metrics
- Prometheus metrics available at `:8001/metrics` (if enabled)
- Check logs for structured telemetry data

## 🔄 Development Workflow

### Making Code Changes

```bash
# Stop containers
docker-compose down

# Make your changes...

# Rebuild and restart
docker-compose up --build
```

### Adding Dependencies

1. Update `pyproject.toml`
2. Rebuild the Docker image:
```bash
docker-compose build --no-cache ai-tutor
```

### Database Migrations

```bash
# Run Alembic migrations in container
docker-compose exec ai-tutor alembic upgrade head
```

## 🏃 Performance Optimization

### For Production

1. **Use production Docker images**
2. **Configure proper resource limits**
3. **Set up reverse proxy (nginx)**
4. **Enable SSL/TLS**
5. **Configure logging to external service**

### Scaling

```yaml
# docker-compose.prod.yml
services:
  ai-tutor:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## 📝 Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LAPA_LLM_BASE_URL` | LapaLLM API endpoint | `http://146.59.127.106:4000` |
| `LAPA_LLM_MODEL` | Primary model name | `lapa` |
| `OPENAI_API_KEY` | Fallback OpenAI key | - |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:password@db:5432/vyvchai` |
| `QDRANT_URL` | Vector database URL | `http://qdrant:6333` |
| `REDIS_URL` | Cache URL | `redis://redis:6379` |

## 🎯 Next Steps

1. **Test all agent specializations**
2. **Integrate with your frontend**
3. **Set up CI/CD pipeline**
4. **Configure monitoring and alerting**
5. **Performance testing and optimization**

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs`
3. Verify environment variables
4. Test individual components

The system is designed to be resilient with automatic fallbacks and comprehensive error handling.