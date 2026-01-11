#!/bin/bash

# VeriaGuide Restore Script
# Restores from backup

set -e

# Configuration
BACKUP_FILE="${1:-.}"
DB_CONTAINER="${DB_CONTAINER:-veriaguide_wp_db}"
DB_NAME="${DB_NAME:-veriaguide_db}"
DB_USER="${DB_USER:-wp_kostass}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}VeriaGuide Restore Script${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Validate backup file
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    echo -e "${YELLOW}Usage: ./restore.sh /path/to/backup.tar.gz${NC}"
    exit 1
fi

echo -e "${YELLOW}Backup file: $BACKUP_FILE${NC}"
echo -e "${YELLOW}Size: $(du -h "$BACKUP_FILE" | cut -f1)${NC}\n"

# Confirm restore
read -p "Are you sure you want to restore from this backup? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${YELLOW}Extracting backup...${NC}"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Step 1: Restore database
echo -e "${YELLOW}Step 1: Restoring database...${NC}"

DB_BACKUP=$(find "$TEMP_DIR" -name "db_backup_*.sql" | head -1)

if [ -z "$DB_BACKUP" ]; then
    echo -e "${RED}Error: Database backup not found in archive${NC}"
    exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}Error: DB_PASSWORD not set${NC}"
    exit 1
fi

docker exec -i "$DB_CONTAINER" mysql \
    -u "$DB_USER" \
    -p"$DB_PASSWORD" \
    "$DB_NAME" < "$DB_BACKUP"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database restored${NC}"
else
    echo -e "${RED}✗ Database restore failed${NC}"
    exit 1
fi

# Step 2: Restore uploads
echo -e "${YELLOW}Step 2: Restoring uploads...${NC}"

UPLOADS_BACKUP=$(find "$TEMP_DIR" -name "uploads_backup_*.tar.gz" | head -1)

if [ -n "$UPLOADS_BACKUP" ]; then
    # Backup current uploads
    if [ -d "wp-content/uploads" ]; then
        mv wp-content/uploads wp-content/uploads.backup
    fi
    
    # Restore uploads
    tar -xzf "$UPLOADS_BACKUP" -C .
    echo -e "${GREEN}✓ Uploads restored${NC}"
else
    echo -e "${YELLOW}⚠ No uploads backup found${NC}"
fi

# Step 3: Restore configuration
echo -e "${YELLOW}Step 3: Restoring configuration...${NC}"

CONFIG_BACKUP=$(find "$TEMP_DIR" -name "config_backup_*.tar.gz" | head -1)

if [ -n "$CONFIG_BACKUP" ]; then
    # Backup current config
    mkdir -p backups/config_backup
    cp .env backups/config_backup/ 2>/dev/null || true
    cp docker-compose.yml backups/config_backup/ 2>/dev/null || true
    
    # Restore config
    tar -xzf "$CONFIG_BACKUP" -C .
    echo -e "${GREEN}✓ Configuration restored${NC}"
else
    echo -e "${YELLOW}⚠ No configuration backup found${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Restore completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify the restored data"
echo "2. Restart the application: docker-compose restart"
echo "3. Check logs: docker logs veriaguide_frontend"
echo ""
echo -e "${YELLOW}Backup of current config saved to: backups/config_backup/${NC}"
