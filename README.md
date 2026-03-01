# High-Scale Traffic Management Prototype

A lightweight prototype demonstrating key techniques used in highly scalable web systems:

- **Load balancing** of HTTP requests across multiple application servers.
- **Distributed caching** with Redis to reduce latency and backend load.
- **Sliding-window, per-IP rate limiting** enforced across a cluster.
- **Simple frontend dashboard** for traffic generation and visualization.

## What This Application Does

This project simulates a high-scale environment by combining a Python
FastAPI backend, an Nginx load balancer, and Redis for shared state. It
lets you observe cache hits/misses, rate limiting behavior, and how a
reverse proxy distributes traffic.

## 🚀 Architecture Overview

- **Nginx**: Reverse proxy and Layer 7 load balancer distributing traffic
  across three identical backend instances.
- **FastAPI (Python)**: Backend servers exposing a single endpoint with
  simulated database latency, caching, and rate limiting logic.
- **Redis**: Central store for both the shared cache and rate limiting
  counters.
- **Docker & Compose**: Orchestrates the full stack for a repeatable
  deployment.

## 🛠️ Features by Component

### 🔧 Backend (FastAPI)
- Endpoint `/api/v1/data/{user}` with artificial delay to mimic a
  database call.
- Redis-based caching layer to demonstrate hit/miss behavior.
- Sliding-window rate limiter implemented in `rate_limit.py`.
- Configured to run under Uvicorn; a `Dockerfile` is provided.

### 🌐 Frontend
- Static HTML/JS dashboard located at `public/index.html` (previously
  `frontend/index.html` in the legacy layout).
- Allows manually sending requests and displays cache and rate limit
  feedback.
- No build step required; open directly in any modern browser or let
  Vercel serve it for you.

### 🌀 Nginx
- Configured as a reverse proxy with health checks and round-robin
  load balancing.
- Proxy parameters in `nginx/proxy_params` with sensible defaults.

### 🧠 Infrastructure
- `docker-compose.yml` brings up `nginx`, three backend replicas, and
  `redis` with a single command.

## 🏁 Getting Started

This repository now supports both a **Vercel deployment** and
traditional local development.  The Vercel setup hosts the frontend as a
static site (from `public/`) and exposes the backend as a Python
serverless API under the `/api` path.  For offline experimentation you
can still run the original Docker/Nginx architecture from the
`legacy/` directory.

### 🚀 Deploying on Vercel

1.  Push the current branch to GitHub if you haven't already:
    ```bash
    git push origin main
    ```
2.  In the Vercel dashboard, import the project from GitHub.  No build
    command is required; Vercel will use `vercel.json` to configure the
    build:

    - Static files served from `public/`
    - Python API routed through `api/index.py`

3.  Set the following **Environment Variables** in your Vercel project
   settings:

    | Name       | Description                          |
    |------------|--------------------------------------|
    | `REDIS_URL`| (optional) URL of a Redis instance; e.g. Upstash. |
    | `CACHE_TTL`| TTL in seconds for cached entries (default 30). |
    | `RATE_LIMIT` | Requests per window (default 10).   |
    | `RATE_WINDOW`| Window length in seconds (default 60). |

   If you omit `REDIS_URL` the backend will still run, but caching and
   rate limiting will be disabled.

4.  Deploy.  The frontend will be available at
    `https://<your-project>.vercel.app/` and the API at
    `https://<your-project>.vercel.app/api`.

   The dashboard uses a relative base (`/api`), so it will automatically
   talk to the correct endpoint once deployed.

### 🛠 Local Development (Python + Redis)

You can also run the API and frontend locally without Docker:

```bash
# create a virtual environment
python -m venv venv
# activate it
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
# optionally run Redis locally (e.g. `docker run -p 6379:6379 redis:7`)

# start the API (port 8000 is default)
uvicorn api.index:app --reload --port 8000
```

Open `public/index.html` in your browser and the UI will communicate with
`http://localhost:8000/data`, `/rate-test`, etc.

### 📦 Legacy Docker Architecture

If you still want to explore the original high-scale prototype with
multiple backend containers and Nginx, look in the `legacy/` directory
(where the previous `backend/`, `nginx/` and `docker-compose.yml`
files have been relocated).  That layout is **not required** for
Vercel deployments.

## Cleaning Up & Development Notes

- The `backend/__pycache__` directory is generated at runtime and is
  ignored by the provided `.gitignore`.
- Use a Python virtual environment (`python -m venv venv`) when
  running locally to keep dependencies isolated.

## 📂 Project Structure

The repository is organised to work cleanly on Vercel while still
retaining the original prototype for local experimentation.

- `public/`: Static frontend assets (HTML, JS, CSS) – Vercel serves this
  at the site root.
- `api/`: Python backend (FastAPI) which is exposed under `/api` by
  Vercel; contains the rate limiter helper.
- `requirements.txt`: Python dependencies for the serverless API.
- `vercel.json`: Vercel configuration (builds and routes).
- `legacy/`: (optional) holds the previous `backend/`, `nginx/`, and
  `docker-compose.yml` layout used for Docker-based testing.

---
*Built as a prototype for high-scale research and education.*

---
*Built as a prototype for high-scale research and education.*
