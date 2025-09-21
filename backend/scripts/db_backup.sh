#!/bin/bash
# =============================================================================
# Backup PostgreSQL Development Database
# =============================================================================

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="ecommerce_backup_${TIMESTAMP}.sql"
BACKUP_DIR="$(dirname "$0")/../docker/backups"

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

echo " Creating database backup..."

cd "$(dirname "$0")/../docker"

docker compose -f docker-compose.dev.yml exec -T db \
    pg_dump -U ecommerce_user -d ecommerce_dev \
    > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo " Backup created successfully: $BACKUP_FILE"
    echo " Location: $BACKUP_DIR/$BACKUP_FILE"
else
    echo " Backup failed"
    exit 1
fi
