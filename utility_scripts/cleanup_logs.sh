#!/bin/bash

# Log Cleanup Script for VeriaGuide
# Removes log files older than 30 days
# Usage: ./cleanup_logs.sh

LOG_DIR="frontend/logs"
RETENTION_DAYS=30

echo "🧹 Cleaning up logs older than $RETENTION_DAYS days..."

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Log directory not found: $LOG_DIR"
    exit 1
fi

# Count files before cleanup
BEFORE=$(find "$LOG_DIR" -type f | wc -l)

# Remove files older than RETENTION_DAYS
find "$LOG_DIR" -type f -mtime +$RETENTION_DAYS -delete

# Count files after cleanup
AFTER=$(find "$LOG_DIR" -type f | wc -l)

REMOVED=$((BEFORE - AFTER))

echo "✅ Cleanup complete!"
echo "   Files before: $BEFORE"
echo "   Files after: $AFTER"
echo "   Files removed: $REMOVED"

# Show current log directory size
SIZE=$(du -sh "$LOG_DIR" | cut -f1)
echo "   Current log directory size: $SIZE"
