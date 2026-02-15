#!/bin/bash

# Update WordPress via Host Download
# Downloads WordPress on the host machine, then copies to container

CONTAINER_NAME="wp_veriaguide_prod"
WP_DIR="$WP_DOCUMENT_ROOT"
DOWNLOAD_URL="https://wordpress.org/latest.zip"
TEMP_DIR="/tmp/wp-update-$$"

echo "🔧 WordPress Update via Host Download (LATEST)"
echo "=============================================="
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

echo "1️⃣  Creating temporary directory..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"
echo "   ✅ Working in: $TEMP_DIR"
echo ""

echo "2️⃣  Downloading latest WordPress..."
curl -4 -L -o wordpress.zip "$DOWNLOAD_URL" --progress-bar
if [ $? -ne 0 ]; then
    echo "   ❌ Download failed on host"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "   ✅ Downloaded: $(ls -lh wordpress.zip | awk '{print $5}')"
echo ""

echo "3️⃣  Extracting WordPress..."
unzip -q wordpress.zip
if [ $? -ne 0 ]; then
    echo "   ❌ Extraction failed"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo "   ✅ Extracted"
echo ""

echo "4️⃣  Creating backup..."
tar -czf "$WP_DIR/../wordpress-backup-$(date +%Y%m%d-%H%M%S).tar.gz" \
    --exclude="$WP_DIR/wp-content" \
    --exclude="$WP_DIR/wp-config.php" \
    "$WP_DIR" 2>/dev/null
echo "   ✅ Backup created"
echo ""

echo "5️⃣  Updating WordPress files..."
echo "   Copying new files (excluding wp-content and wp-config.php)..."
rsync -av --exclude='wp-content' --exclude='wp-config.php' wordpress/ "$WP_DIR/"
echo "   ✅ Files updated"
echo ""

echo "6️⃣  Setting correct permissions..."
chown -R 5014:5014 "$WP_DIR"
find "$WP_DIR" -type d -exec chmod 755 {} \;
find "$WP_DIR" -type f -exec chmod 644 {} \;
chmod -R 775 "$WP_DIR/wp-content"
echo "   ✅ Permissions set"
echo ""

echo "7️⃣  Cleaning up..."
cd /
rm -rf "$TEMP_DIR"
echo "   ✅ Cleanup complete"
echo ""

echo "8️⃣  Verifying WordPress version..."
grep "wp_version = " "$WP_DIR/wp-includes/version.php" | head -1
echo ""

echo "9️⃣  Restarting WordPress container..."
docker restart "$CONTAINER_NAME"
sleep 3
echo "   ✅ Container restarted"
echo ""

echo "✅ WordPress successfully updated!"
echo ""
echo "Next steps:"
echo "1. Go to: https://veriaguide.gr/wp-admin"
echo "2. You may see a 'Database Update Required' message"
echo "3. Click 'Update WordPress Database' if prompted"
echo "4. Clear your browser cache and test the site"
echo ""
