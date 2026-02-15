#!/bin/bash

# Update WordPress Themes via Host Download (Auto-Discovery)
# Scans for installed themes and updates them if they exist in the official repo.

CONTAINER_NAME="wp_veriaguide_prod"
WP_DIR="$WP_DOCUMENT_ROOT"
THEMES_DIR="$WP_DIR/wp-content/themes"
TEMP_DIR="/tmp/wp-themes-update-$$"

echo "🔧 WordPress Themes Update (Auto-Discovery)"
echo "============================================"
echo "Scanning $THEMES_DIR for themes..."
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# 1. Discover Themes
if [ ! -d "$THEMES_DIR" ]; then
    echo "❌ Themes directory not found: $THEMES_DIR"
    exit 1
fi

# Read directories into an array
THEMES=()
while IFS= read -r theme; do
    THEMES+=("$theme")
done < <(find "$THEMES_DIR" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)

if [ ${#THEMES[@]} -eq 0 ]; then
    echo "⚠️  No themes found."
    exit 0
fi

echo "found ${#THEMES[@]} themes."
echo ""

echo "1️⃣  Creating temporary directory..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"
echo "   ✅ Working in: $TEMP_DIR"
echo ""

echo "2️⃣  Checking and Downloading updates..."
UPDATED_THEMES=()
SKIPPED_THEMES=()

for slug in "${THEMES[@]}"; do
    echo "   🔎 Checking $slug..."
    
    DOWNLOAD_URL="https://downloads.wordpress.org/theme/${slug}.zip"
    
    # Check if file exists on remote server (HTTP 200, follows redirects)
    HTTP_CODE=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' -L "$DOWNLOAD_URL")
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "      ✅ Found in official repo. Downloading latest..."
        curl -4 -L -o "${slug}.zip" "$DOWNLOAD_URL" --progress-bar
        
        if [ $? -eq 0 ]; then
            UPDATED_THEMES+=("$slug")
        else
            echo "      ❌ Download failed for $slug"
        fi
    else
        echo "      ⚠️  Not found in official repo (Custom/Premium?). SKIPPING."
        SKIPPED_THEMES+=("$slug")
    fi
    echo ""
done

if [ ${#UPDATED_THEMES[@]} -eq 0 ]; then
    echo "No themes to update from official repo."
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo "3️⃣  Creating backup of themes..."
tar -czf "$WP_DIR/../themes-backup-$(date +%Y%m%d-%H%M%S).tar.gz" "$THEMES_DIR" 2>/dev/null
echo "   ✅ Backup created"
echo ""

echo "4️⃣  Installing updates..."
for slug in "${UPDATED_THEMES[@]}"; do
    theme_zip="${slug}.zip"
    if [ -f "$theme_zip" ]; then
        echo "   🎨 Installing $slug..."
        
        # Extract
        unzip -q -o "$theme_zip"
        
        # Remove old directory
        if [ -d "$THEMES_DIR/$slug" ]; then
            rm -rf "$THEMES_DIR/$slug"
        fi
        
        # Move new directory
        if [ -d "$slug" ]; then
            cp -r "$slug" "$THEMES_DIR/"
            echo "      ✅ Installed"
        else
            echo "      ❌ Extraction seems to have failed for $slug"
        fi
    fi
done
echo ""

echo "5️⃣  Setting correct permissions..."
chown -R 5014:5014 "$THEMES_DIR"
find "$THEMES_DIR" -type d -exec chmod 755 {} \;
find "$THEMES_DIR" -type f -exec chmod 644 {} \;
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

echo "✅ WordPress themes update process finished!"
echo ""
echo "Summary:"
echo "--------------------------------"
echo "Updated (${#UPDATED_THEMES[@]}):"
for slug in "${UPDATED_THEMES[@]}"; do
    echo "  - $slug"
done
echo ""
echo "Skipped (Custom/Premium) (${#SKIPPED_THEMES[@]}):"
for slug in "${SKIPPED_THEMES[@]}"; do
    echo "  - $slug"
done
echo ""
