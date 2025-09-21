#!/bin/bash
# =============================================================================
# Reset PostgreSQL Development Database
# =============================================================================

set -e

echo "  Resetting PostgreSQL database..."
echo "  WARNING: This will delete ALL data in the development database!"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$(dirname "$0")/../docker"
    
    echo " Stopping containers..."
    docker compose -f docker-compose.dev.yml down
    
    echo "  Removing data volumes..."
    docker compose -f docker-compose.dev.yml down -v
    
    echo " Starting fresh database..."
    docker compose -f docker-compose.dev.yml up -d db
    
    echo " Waiting for PostgreSQL..."
    timeout 30s bash -c 'until docker compose -f docker-compose.dev.yml exec -T db pg_isready -U ecommerce_user -d ecommerce_dev; do sleep 1; done'
    
    echo " Fresh PostgreSQL database ready!"
    echo " Don't forget to run: python manage.py migrate"
else
    echo " Reset cancelled"
fi
