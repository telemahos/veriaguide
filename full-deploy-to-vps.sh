#!/bin/bash

# Full Deployment Script - Upload everything to VPS and setup
# Run this from your LOCAL machine

set -e

# Configuration
VPS_USER="root"
VPS_HOST="***REMOVED***"
VPS_PORT="22"
VPS_DIR="$WP_DOCUMENT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "=================================================="
echo "VeriaGuide Full Deployment to VPS"
echo "=================================================="
echo

print_status "Step 1: Creating temporary staging directory on VPS..."
ssh SSH_HOST "mkdir -p ~/veriaguide_deploy_tmp"

print_status "Step 2: Uploading all project files..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    --exclude 'mysql-data' \
    --exclude '.DS_Store' \
    --exclude '.env' \
    --exclude 'frontend/logs/*.log*' \
    -e "ssh" \
    ./ SSH_HOST:~/veriaguide_deploy_tmp/

print_status "Step 3: Moving files to production directory..."
ssh SSH_HOST << 'ENDSSH'
    rm -rf $WP_DOCUMENT_ROOT/frontend
    rm -rf $WP_DOCUMENT_ROOT/data
    rm -f $WP_DOCUMENT_ROOT/docker-compose.prod.yml
    rm -f $WP_DOCUMENT_ROOT/*.sh
    
    cp -r ~/veriaguide_deploy_tmp/* $WP_DOCUMENT_ROOT/
    chown -R root:root $WP_DOCUMENT_ROOT
    
    rm -rf ~/veriaguide_deploy_tmp
ENDSSH

print_status "Step 4: Files uploaded successfully!"
echo
print_warning "Next steps - Files are ready on VPS at: $VPS_DIR"
echo
print_status "Done! 🚀"
