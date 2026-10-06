#!/bin/bash

# Update WordPress Plugins via Host Download (Auto-Discovery)
# Scans for installed plugins and updates them if they exist in the official repo.

CONTAINER_NAME="wp_veriaguide_prod"
WP_DIR="${WP_DOCUMENT_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
PLUGINS_DIR="$WP_DIR/wp-content/plugins"
TEMP_DIR="/tmp/wp-plugins-update-$$"

echo "🔧 WordPress Plugins Update (Auto-Discovery)"
echo "============================================"
echo "Scanning $PLUGINS_DIR for plugins..."
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# 1. Discover Plugins
if [ ! -d "$PLUGINS_DIR" ]; then
    echo "❌ Plugins directory not found: $PLUGINS_DIR"
    exit 1
fi

# Read directories into an array (excluding . and ..)
PLUGINS=()
while IFS= read -r plugin; do
    PLUGINS+=("$plugin")
done < <(find "$PLUGINS_DIR" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)

if [ ${#PLUGINS[@]} -eq 0 ]; then
    echo "⚠️  No plugins found."
    exit 0
fi

echo "found ${#PLUGINS[@]} plugins."
echo ""

echo "1️⃣  Creating temporary directory..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"
echo "   ✅ Working in: $TEMP_DIR"
echo ""

echo "2️⃣  Checking and Downloading updates..."
UPDATED_PLUGINS=()
SKIPPED_PLUGINS=()

for slug in "${PLUGINS[@]}"; do
    echo "   🔎 Checking $slug..."
    
    DOWNLOAD_URL="https://downloads.wordpress.org/plugin/${slug}.zip"
    
    # Check if file exists on remote server (HTTP 200, follows redirects)
    HTTP_CODE=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' -L "$DOWNLOAD_URL")
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "      ✅ Found in official repo. Downloading latest..."
        curl -4 -L -o "${slug}.zip" "$DOWNLOAD_URL" --progress-bar
        
        if [ $? -eq 0 ]; then
            UPDATED_PLUGINS+=("$slug")
        else
            echo "      ❌ Download failed for $slug"
        fi
    else
        echo "      ⚠️  Not found in official repo (Custom/Premium?). SKIPPING."
        SKIPPED_PLUGINS+=("$slug")
    fi
    echo ""
done

if [ ${#UPDATED_PLUGINS[@]} -eq 0 ]; then
    echo "No plugins to update from official repo."
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo "3️⃣  Creating backup of plugins..."
tar -czf "$WP_DIR/../plugins-backup-$(date +%Y%m%d-%H%M%S).tar.gz" "$PLUGINS_DIR" 2>/dev/null
echo "   ✅ Backup created"
echo ""

echo "4️⃣  Installing updates..."
for slug in "${UPDATED_PLUGINS[@]}"; do
    plugin_zip="${slug}.zip"
    if [ -f "$plugin_zip" ]; then
        echo "   📦 Installing $slug..."
        
        # Extract
        unzip -q -o "$plugin_zip"
        
        # Remove old directory
        if [ -d "$PLUGINS_DIR/$slug" ]; then
            rm -rf "$PLUGINS_DIR/$slug"
        fi
        
        # Move new directory
        if [ -d "$slug" ]; then
            cp -r "$slug" "$PLUGINS_DIR/"
            echo "      ✅ Installed"
        else
            echo "      ❌ Extraction seems to have failed for $slug"
        fi
    fi
done
echo ""

echo "5️⃣  Setting correct permissions..."
chown -R 5014:5014 "$PLUGINS_DIR"
find "$PLUGINS_DIR" -type d -exec chmod 755 {} \;
find "$PLUGINS_DIR" -type f -exec chmod 644 {} \;
echo "   ✅ Permissions set"
echo ""

echo "6️⃣  Cleaning up..."
cd /
rm -rf "$TEMP_DIR"
echo "   ✅ Cleanup complete"
echo ""

echo "7️⃣  Restarting WordPress container..."
docker restart "$CONTAINER_NAME"
sleep 3
echo "   ✅ Container restarted"
echo ""

echo "✅ WordPress plugins update process finished!"
echo ""
echo "Summary:"
echo "--------------------------------"
echo "Updated (${#UPDATED_PLUGINS[@]}):"
for slug in "${UPDATED_PLUGINS[@]}"; do
    echo "  - $slug"
done
echo ""
echo "Skipped (Custom/Premium) (${#SKIPPED_PLUGINS[@]}):"
for slug in "${SKIPPED_PLUGINS[@]}"; do
    echo "  - $slug"
done
echo ""
