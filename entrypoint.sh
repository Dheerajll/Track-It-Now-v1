#!/bin/sh
# entrypoint.sh

# Wait for Postgres
/wait-for-db.sh "db" "5432"

# Wait for Redis
/wait-for-redis.sh "redis" "6379"

# Start FastAPI
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000