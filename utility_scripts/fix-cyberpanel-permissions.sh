#!/bin/bash

# Fix CyberPanel directory permissions for WordPress Docker container
echo "🔧 Fixing CyberPanel directory permissions for WordPress..."

WEBROOT="/home/veriaguide.gr/public_html"
WEB_USER="veriaguide.gr"  # CyberPanel user
DOCKER_USER="www-data"    # WordPress container user

echo "📋 Setting up directory permissions..."

# Ensure directory exists
sudo mkdir -p "$WEBROOT"

# Set ownership to web user and docker group
sudo chown -R $WEB_USER:$WEB_USER "$WEBROOT"

# Set permissions for WordPress
sudo chmod -R 755 "$WEBROOT"
sudo chmod -R 775 "$WEBROOT/wp-content"

# Allow Docker container to write
sudo setfacl -R -m u:33:rwx "$WEBROOT" 2>/dev/null || echo "⚠️  ACL not available, using chmod"
sudo setfacl -R -d -m u:33:rwx "$WEBROOT" 2>/dev/null || echo "⚠️  ACL not available"

# Alternative: Add www-data to web user group (if ACL not available)
if ! command -v setfacl &> /dev/null; then
    echo "📋 Using group permissions instead of ACL..."
    sudo usermod -a -G $WEB_USER www-data 2>/dev/null || echo "⚠️  Could not add www-data to group"
    sudo chmod -R g+w "$WEBROOT/wp-content"
fi

echo "✅ Permissions updated!"
echo ""
echo "📋 Directory structure:"
ls -la "$WEBROOT"
echo ""
echo "📋 Next steps:"
echo "1. Restart Docker containers: docker-compose -f docker-compose.legacy-fullstack.yml down && docker-compose -f docker-compose.legacy-fullstack.yml up -d"
echo "2. Check WordPress installation at: http://veriaguide.gr:8091/wp-admin/"