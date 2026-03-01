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
- No build step required; open directly in any modern browser or serve
  the static files from any web server.

### 🌀 Nginx
- Configured as a reverse proxy with health checks and round-robin
  load balancing.
- Proxy parameters in `nginx/proxy_params` with sensible defaults.

### 🧠 Infrastructure
- `docker-compose.yml` brings up `nginx`, three backend replicas, and
  `redis` with a single command.

## 🏁 Getting Started

This repository supports traditional local development and can be
hosted on any web server or Python-capable platform.  For offline
experimentation you can still run the original Docker/Nginx
architecture from the `legacy/` directory.

### 🛠 Local Development (Python + Redis)

You can run the API and frontend locally without Docker:

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

Open `public/index.html` in your browser (or serve it with the server of
your choice) and the UI will communicate with
`http://localhost:8000/data`, `/rate-test`, etc.

### 📦 Legacy Docker Architecture

If you still want to explore the original high-scale prototype with
multiple backend containers and Nginx, look in the `legacy/` directory
(where the previous `backend/`, `nginx/` and `docker-compose.yml`
files have been relocated).  That layout is purely for local testing and
is not required for general deployment.

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

The repository is organised to separate the static frontend from the
Python backend while still retaining the original multi‑container
prototype for local experimentation.

- `public/`: Static frontend assets (HTML, JS, CSS) – serve these with
  any web server.
- `api/`: Python backend (FastAPI) exposed under `/api`; contains the
  rate limiter helper.
- `requirements.txt`: Python dependencies for the backend.
- `legacy/`: (optional) holds the previous `backend/`, `nginx/`, and
  `docker-compose.yml` layout used for Docker-based testing.

---
*Built as a prototype for high-scale research and education.*

---
*Built as a prototype for high-scale research and education.*
