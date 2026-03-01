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
- Static HTML/JS dashboard located at `frontend/index.html`.
- Allows manually sending requests and displays cache and rate limit
  feedback.
- No build step required; open directly in any modern browser.

### 🌀 Nginx
- Configured as a reverse proxy with health checks and round-robin
  load balancing.
- Proxy parameters in `nginx/proxy_params` with sensible defaults.

### 🧠 Infrastructure
- `docker-compose.yml` brings up `nginx`, three backend replicas, and
  `redis` with a single command.

## 🏁 Getting Started

### Prerequisites
- Docker Desktop (for containerized mode) **or** Python 3.11+ for
  local development.

### Running with Docker (recommended)
1.  Clone the repository:
    ```bash
    git clone https://github.com/Shwetabh9163/Prototype.git
    cd Prototype
    ```
2.  Build and start everything:
    ```bash
    docker-compose up --build
    ```
3.  Open `frontend/index.html` in your browser or visit
    `http://localhost:8080/api/v1/data/user123` to hit the API.

### Running Locally in a Virtual Environment
1.  Navigate to the backend directory and create a venv:
    ```bash
    cd backend
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Start Redis (e.g. `docker run -p 6379:6379 redis:7` or a local
    install).
4.  Run the app:
    ```bash
    uvicorn app:app --reload --port 8000
    ```
5.  Access the API at `http://localhost:8000/api/v1/data/user123` and
    open the frontend by loading `frontend/index.html` in your browser.

## Cleaning Up & Development Notes

- The `backend/__pycache__` directory is generated at runtime and is
  ignored by the provided `.gitignore`.
- Use a Python virtual environment (`python -m venv venv`) when
  running locally to keep dependencies isolated.

## 📂 Project Structure

- `backend/`: FastAPI code, Dockerfile, rate limiter
- `frontend/`: Static dashboard UI
- `nginx/`: Load balancer configuration
- `docker-compose.yml`: Orchestration

---
*Built as a prototype for high-scale research and education.*
