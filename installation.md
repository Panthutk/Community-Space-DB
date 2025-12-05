# Community Space — Installation Guide

This document explains how to install and run the full project (React + Vite frontend, Django backend, MySQL database) using Docker or manual setup.

---

# Requirements

Install these before starting:

- Docker Desktop (latest)
- Node.js 18+ (only for manual frontend)
- Python 3.12+ (only for manual backend)

---

# Running with Docker (recommended)

Start all services:

```powershell

docker compose up --build
```

Service URLs:

| Service  | URL                          |
|----------|------------------------------|
| Frontend | <http://localhost:5173>        |
| Backend  | <http://localhost:8000>        |
| API Root | <http://localhost:8000/api/>   |
| Items    | <http://localhost:8000/api/items/> |

Stop services:

```powershell
docker compose down --volumes
```
