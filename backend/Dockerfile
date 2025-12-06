# backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install system packages: build tools, mysql client libs, and netcat for readiness checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc pkg-config default-libmysqlclient-dev libmariadb-dev \
    libssl-dev ca-certificates netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# copy and install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project files
COPY . .

EXPOSE 8000

# Wait for DB, then run migrations and start server
CMD ["sh", "-c", "echo 'Waiting for db to be ready...'; until nc -z db 3306; do echo 'waiting for db...'; sleep 1; done; echo 'db is ready — applying migrations'; python manage.py migrate --noinput; echo 'starting server'; python manage.py runserver 0.0.0.0:8000"]