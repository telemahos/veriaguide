#!/bin/bash

# Setup Cron Job for Automatic Log Cleanup
# Runs log cleanup every day at 3 AM
# Usage: ./setup-log-cleanup-cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_logs.sh"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Make cleanup script executable
chmod +x "$CLEANUP_SCRIPT"

# Create cron job entry
CRON_ENTRY="0 3 * * * cd $PROJECT_DIR && $CLEANUP_SCRIPT >> /var/log/veriaguide_cleanup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cleanup_logs.sh"; then
    echo "⚠️  Cron job already exists"
    echo "Current cron jobs:"
    crontab -l | grep cleanup_logs.sh
    exit 0
fi

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job setup complete!"
echo "   Script: $CLEANUP_SCRIPT"
echo "   Schedule: Daily at 3:00 AM"
echo "   Log file: /var/log/veriaguide_cleanup.log"
echo ""
echo "To verify the cron job:"
echo "   crontab -l | grep cleanup_logs.sh"
echo ""
echo "To remove the cron job:"
echo "   crontab -e  # and delete the line"
