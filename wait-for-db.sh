#!/bin/bash

POSTGRES_USER=$1
POSTGRES_DB=$2

resolve_container_by_service() {
  svc_name="$1"
  cid=$(docker compose ps -q "$svc_name" 2>/dev/null | head -n 1)
  if [ -z "$cid" ]; then
    cid=$(docker ps -q --filter "label=com.docker.compose.service=$svc_name" | head -n 1)
  fi
  echo "$cid"
}

echo "Waiting for database to be ready..."
DB_CID=$(resolve_container_by_service db)
if [ -z "$DB_CID" ]; then DB_CID=postgres_db; fi
until docker exec "$DB_CID" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  echo "Database is unavailable - sleeping"
  sleep 2
done
echo "Database is up and running!"

echo "Waiting for FastAPI backend to be ready..."
BACKEND_CID=$(resolve_container_by_service backend)
if [ -z "$BACKEND_CID" ]; then BACKEND_CID=fastapi_backend; fi
until docker exec "$BACKEND_CID" curl -fsS http://localhost:8000/health >/dev/null 2>&1; do
  echo "FastAPI backend is unavailable - sleeping"
  sleep 2
done
echo "FastAPI backend is up and running!"
echo "All services are ready!"