#!/bin/bash

# Setup automated backups with cron

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Setup Automated Backups${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
BACKUP_DIR="$SCRIPT_DIR/backups"
RETENTION_DAYS=30
BACKUP_HOUR=2  # 2 AM
BACKUP_MINUTE=0

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create cron job
CRON_JOB="$BACKUP_MINUTE $BACKUP_HOUR * * * cd $SCRIPT_DIR && BACKUP_DIR=$BACKUP_DIR RETENTION_DAYS=$RETENTION_DAYS DB_PASSWORD=\$(grep DB_PASSWORD .env | cut -d= -f2) ./backup.sh >> $BACKUP_DIR/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo -e "${YELLOW}Cron job already exists${NC}"
    echo -e "${YELLOW}Current cron jobs:${NC}"
    crontab -l | grep backup.sh
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Cron job added${NC}"
    echo -e "${YELLOW}Backup scheduled for: $BACKUP_HOUR:$BACKUP_MINUTE daily${NC}"
fi

# Create backup directory structure
mkdir -p "$BACKUP_DIR"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Backup automation setup complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Configuration:${NC}"
echo "Backup directory: $BACKUP_DIR"
echo "Retention: $RETENTION_DAYS days"
echo "Schedule: Daily at $BACKUP_HOUR:$BACKUP_MINUTE"
echo "Log file: $BACKUP_DIR/cron.log"

echo -e "\n${YELLOW}Manual backup:${NC}"
echo "  ./backup.sh"

echo -e "\n${YELLOW}Restore from backup:${NC}"
echo "  ./restore.sh /path/to/backup.tar.gz"

echo -e "\n${YELLOW}View cron jobs:${NC}"
echo "  crontab -l"

echo -e "\n${YELLOW}View backup logs:${NC}"
echo "  tail -f $BACKUP_DIR/cron.log"
