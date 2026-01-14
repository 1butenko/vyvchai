@echo off
REM Fast Docker Build Script for VyvchAI (Windows)
REM This script optimizes the build process for faster iterations

echo 🚀 Starting optimized VyvchAI Docker build...

REM Enable Docker BuildKit for faster builds
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

REM Build with parallel processing and cache mounts
echo 📦 Building Docker images with optimizations...
docker-compose build --parallel --progress=plain

echo ✅ Build complete! Starting services...
docker-compose up -d

echo 🔍 Checking service health...
timeout /t 10 /nobreak >nul

REM Check if services are healthy
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo 🎉 All services are running!
    echo.
    echo 📋 Access your services:
    echo   • FastAPI: http://localhost:8000
    echo   • API Docs: http://localhost:8000/docs
    echo   • Phoenix: http://localhost:6006
    echo   • Qdrant: http://localhost:6333/dashboard
    echo.
    echo 🧪 Run tests:
    echo   docker-compose exec ai-tutor python test_agent.py
) else (
    echo ❌ Some services failed to start. Check logs:
    echo   docker-compose logs
)

pause