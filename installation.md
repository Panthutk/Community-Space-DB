# Community Space — Installation Guide

This document explains how to install and run the full project (React + Vite frontend, Django backend, MySQL database) using Docker.

---

# Requirements

Install these before starting:

- Docker Desktop

- Add this following file to your local
in backend directory create: `backend/.env` with the following content:

```env
DJANGO_SECRET_KEY=change-me-for-prod
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
MYSQL_DATABASE=mydb
MYSQL_USER=myuser
MYSQL_PASSWORD=mypassword
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

in frontend directory create: `frontend/.env` with the following content:

```env
VITE_BACKEND_URL=http://localhost:8000
```

---

# Running with Docker (recommended)

Start all services:

```powershell
docker compose up --build
```

To access the Django admin interface, create a superuser:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Service URLs:

| Service  | URL                          |
|----------|------------------------------|
| Frontend | <http://localhost:5173>        |
| Backend  | <http://localhost:8000>        |
| API Root | <http://localhost:8000/api/>   |
| Admin    | <http://localhost:8000/admin/> |

Stop services:

```powershell
docker compose down --volumes
```
