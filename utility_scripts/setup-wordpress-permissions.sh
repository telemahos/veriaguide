#!/bin/bash

# Setup WordPress Permissions - Run this ONCE after deployment
# This ensures WordPress can update itself without permission issues

WP_DIR="${WP_DOCUMENT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

echo "🔧 Setting up WordPress Permissions"
echo "===================================="
echo ""

if [ ! -d "$WP_DIR" ]; then
    echo "❌ WordPress directory not found: $WP_DIR"
    exit 1
fi

# Detect the correct user/group
CURRENT_USER=$(ls -ld "$WP_DIR" | awk '{print $3}')
CURRENT_GROUP=$(ls -ld "$WP_DIR" | awk '{print $4}')

echo "Detected user: $CURRENT_USER"
echo "Detected group: $CURRENT_GROUP"
echo ""

echo "1️⃣  Fixing ownership..."
sudo chown -R $CURRENT_USER:$CURRENT_GROUP "$WP_DIR"
echo "   ✅ Changed ownership to $CURRENT_USER:$CURRENT_GROUP"
echo ""

echo "2️⃣  Setting directory permissions..."
sudo find "$WP_DIR" -type d -exec chmod 755 {} \;
echo "   ✅ Set directories to 755"
echo ""

echo "3️⃣  Setting file permissions..."
sudo find "$WP_DIR" -type f -exec chmod 644 {} \;
echo "   ✅ Set files to 644"
echo ""

echo "4️⃣  Making wp-content writable..."
sudo chmod -R 775 "$WP_DIR/wp-content"
echo "   ✅ Set wp-content to 775"
echo ""

echo "5️⃣  Verifying permissions..."
echo "   WordPress directory owner:"
ls -ld "$WP_DIR" | awk '{print "   " $3 ":" $4}'
echo ""
echo "   wp-content permissions:"
ls -ld "$WP_DIR/wp-content" | awk '{print "   " $1}'
echo ""

echo "✅ WordPress permissions setup complete!"
echo ""
echo "Now restart the WordPress container:"
echo "   docker compose -f docker-compose.legacy-fullstack.yml restart wordpress"
echo ""
