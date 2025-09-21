#!/bin/bash
# =============================================================================
# Start PostgreSQL Development Database
# =============================================================================

set -e  # Exit on any error

echo "  Starting PostgreSQL development environment..."

# Verificar si Docker esta ejecutandose
if ! docker info > /dev/null 2>&1; then
    echo "  Docker is not running. Please start Docker first."
    exit 1
fi

# Cambiar al directorio correcto
cd "$(dirname "$0")/../docker"

# Iniciar servicios
echo "  Starting PostgreSQL and pgAdmin containers..."
docker compose -f docker-compose.dev.yml up -d

# Esperar a que esté listo
echo "  Waiting for PostgreSQL to be ready..."
timeout 30s bash -c 'until docker compose -f docker-compose.dev.yml exec -T db pg_isready -U ecommerce_user -d ecommerce_dev; do sleep 1; done'

if [ $? -eq 0 ]; then
    echo "  PostgreSQL is ready!"
    echo ""
    echo "  Connection Details:"
    echo "   Host: localhost"
    echo "   Port: 5433"
    echo "   Database: ecommerce_dev"
    echo "   Username: ecommerce_user"
    echo "   Password: dev_password123"
    echo ""
    echo "  pgAdmin available at: http://localhost:5050"
    echo "   Email: admin@ecommerce.local"
    echo "   Password: admin123"
    echo ""
    echo "   Next steps:"
    echo "   cd backend && python manage.py migrate"
else
    echo "Failed to start PostgreSQL"
    exit 1
fi
