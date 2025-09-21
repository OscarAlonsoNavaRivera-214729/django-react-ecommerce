#!/bin/bash
# =============================================================================
# Stop PostgreSQL Development Database
# =============================================================================

echo "🛑 Stopping PostgreSQL development environment..."

cd "$(dirname "$0")/../docker"
docker compose -f docker-compose.dev.yml down

echo "✅ PostgreSQL stopped successfully"
