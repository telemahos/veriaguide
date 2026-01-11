#!/bin/bash

# VeriaGuide Backup Script
# Backs up database, uploads, and configuration

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-.}/backups"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_CONTAINER="${DB_CONTAINER:-veriaguide_wp_db}"
DB_NAME="${DB_NAME:-veriaguide_db}"
DB_USER="${DB_USER:-wp_kostass}"
DB_PASSWORD="${DB_PASSWORD:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/veriaguide_backup_$TIMESTAMP.tar.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}VeriaGuide Backup Script${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Step 1: Backup Database
echo -e "${YELLOW}Step 1: Backing up database...${NC}"

DB_BACKUP="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}Error: DB_PASSWORD not set${NC}"
    exit 1
fi

docker exec "$DB_CONTAINER" mysqldump \
    -u "$DB_USER" \
    -p"$DB_PASSWORD" \
    "$DB_NAME" > "$DB_BACKUP"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database backed up${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

# Step 2: Backup WordPress uploads
echo -e "${YELLOW}Step 2: Backing up WordPress uploads...${NC}"

UPLOADS_BACKUP="$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz"

if [ -d "wp-content/uploads" ]; then
    tar -czf "$UPLOADS_BACKUP" wp-content/uploads/ 2>/dev/null
    echo -e "${GREEN}✓ Uploads backed up${NC}"
else
    echo -e "${YELLOW}⚠ No uploads directory found${NC}"
fi

# Step 3: Backup configuration
echo -e "${YELLOW}Step 3: Backing up configuration...${NC}"

CONFIG_BACKUP="$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"

tar -czf "$CONFIG_BACKUP" \
    .env \
    docker-compose.yml \
    frontend/app/config/ \
    2>/dev/null

echo -e "${GREEN}✓ Configuration backed up${NC}"

# Step 4: Create final backup archive
echo -e "${YELLOW}Step 4: Creating final backup archive...${NC}"

tar -czf "$BACKUP_FILE" \
    "$DB_BACKUP" \
    "$UPLOADS_BACKUP" \
    "$CONFIG_BACKUP" \
    2>/dev/null

# Clean up temporary files
rm -f "$DB_BACKUP" "$UPLOADS_BACKUP" "$CONFIG_BACKUP"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"

# Step 5: Cleanup old backups
echo -e "${YELLOW}Step 5: Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"

find "$BACKUP_DIR" -name "veriaguide_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

REMAINING=$(ls -1 "$BACKUP_DIR"/veriaguide_backup_*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Cleanup complete ($REMAINING backups retained)${NC}"

# Step 6: List recent backups
echo -e "\n${YELLOW}Recent backups:${NC}"
ls -lh "$BACKUP_DIR"/veriaguide_backup_*.tar.gz 2>/dev/null | tail -5

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Optional: Upload to remote storage
if [ -n "$BACKUP_REMOTE_URL" ]; then
    echo -e "${YELLOW}Uploading to remote storage...${NC}"
    curl -X POST -F "file=@$BACKUP_FILE" "$BACKUP_REMOTE_URL"
    echo -e "${GREEN}✓ Remote upload complete${NC}"
fi
