# Use a slim Python image
FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /backend-app

# Install system dependencies (optional: netcat for wait scripts)
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies first to leverage Docker cache
COPY pyproject.toml uv.lock ./


#Install uv to synce all the dependencies
RUN pip install uv

#sync the dependencies

RUN uv sync

# Copy all app code
COPY . .

# Copy entrypoint and wait scripts
COPY entrypoint.sh /entrypoint.sh
COPY wait-for-db.sh /wait-for-db.sh
COPY wait-for-redis.sh /wait-for-redis.sh

# Make scripts executable
RUN chmod +x /entrypoint.sh /wait-for-db.sh /wait-for-redis.sh

# Expose FastAPI port
EXPOSE 8000

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]