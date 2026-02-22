#!/bin/sh
# wait-for-db.sh

host="$1"
port="${2:-5432}"

echo "Waiting for Postgres at $host:$port..."

while ! nc -z "$host" "$port"; do
  sleep 2
done

echo "Postgres is ready!"