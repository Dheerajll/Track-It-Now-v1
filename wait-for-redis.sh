#!/bin/sh
# wait-for-redis.sh

host="$1"
port="${2:-6379}"

echo "Waiting for Redis at $host:$port..."

while ! nc -z "$host" "$port"; do
  sleep 1
done

echo "Redis is ready!"