# 🐳 Docker Guide for VyvchAI (Hackathon Edition)

This guide explains what Docker is and provides the exact steps to get the AI Tutor running safely and quickly.

## 🤔 What is Docker?

Imagine you want to run a complex app, but it needs:
- Python 3.11 (but you have 3.13)
- A specific database (Postgres)
- A vector database (Qdrant)
- Caching (Redis)

Installing all these manually on Windows is a nightmare and often breaks.

**Docker** solves this by packaging the app and all its dependencies (even the databases!) into "containers".
- **Container**: A lightweight, standalone package that runs the same everywhere.
- **Docker Compose**: A tool that runs multiple containers (App + DB + Redis) together with one command.

---

## 🛠️ Step-by-Step: How to Run the App

Follow these steps exactly to get everything up and running.

### Step 1: Prepare Environment

1.  **Check `.env` file**:
    Make sure you have a `.env` file in the project root (`d:\vivchai\vyvchai\.env`).
    If you don't, copy the example:
    ```powershell
    copy .env.example .env
    ```
    *Open `.env` and ensure your API keys (OpenAI, etc.) are set if needed.*

### Step 2: Build and Start

Open your terminal (PowerShell or Command Prompt) in `d:\vivchai\vyvchai` and run:

```powershell
docker-compose up --build
```

**What this does:**
1.  Downloads the databases (Postgres, Redis, separate from your PC).
2.  Builds your Python app environment (installs all libraries).
3.  Starts everything.

*Note: The first build might take 5-10 minutes. Grab a coffee! ☕*

When you see logs like `Application startup complete`, it's running!

### Step 3: Verify It Works

Open these links in your browser:
- **Main App**: [http://localhost:8000](http://localhost:8000) (Expect "Hello" or API docs)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Tracing UI**: [http://localhost:6006](http://localhost:6006)

---

## 🧪 How to Run Tests

Since this is for a hackathon, we want to make sure the agents are actually working.

### Option 1: Run Test Script (Easiest)
While the app is running in one terminal, open a **new** terminal window and run:

```powershell
# This runs the test script INSIDE the docker container
docker-compose exec ai-tutor python test_agent.py
```

### Option 2: Run Tests Locally (If you have Python installed)
If you have Python configured locally:
```powershell
python test_agent.py
```

---

## 🆘 Troubleshooting (Panic Button)

**"It says port is already allocated"**
- Some other app is using the port.
- Fix: Stop other things or just restart Docker Desktop.

**"I want to valid/reset everything"**
Run this to clean slate (deletes database data!):
```powershell
docker-compose down -v
docker-compose up --build
```
