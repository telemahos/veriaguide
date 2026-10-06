#!/bin/bash
# Deploy trailing-slash fix: FastAPI + OLS vhost + Redis flush
# Run locally after SSH is configured.
#
# Env: SSH_HOST (alias or user@host), WP_DOCUMENT_ROOT (server path)
set -e

VPS="${SSH_HOST:?Set SSH_HOST to your SSH alias or user@host}"
REMOTE_DIR="${WP_DOCUMENT_ROOT:?Set WP_DOCUMENT_ROOT to the server document root}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 1. Upload frontend + OLS fix script ==="
rsync -avz --delete \
    --exclude '__pycache__' --exclude '*.pyc' --exclude '.pytest_cache' \
    --exclude 'logs/*.log*' \
    -e ssh \
    "$REPO_ROOT/frontend/" "$VPS:$REMOTE_DIR/frontend/"

scp \
    "$SCRIPT_DIR/fix-ols-vhost-proxy.sh" \
    "$VPS:$REMOTE_DIR/fix-ols-vhost-proxy.sh"

echo ""
echo "=== 2. Rebuild FastAPI (redirect_slashes=False) ==="
ssh "$VPS" "cd $REMOTE_DIR && docker compose -f docker-compose.vps.yml build --no-cache frontend && docker compose -f docker-compose.vps.yml up -d frontend"

echo ""
echo "=== 3. Apply OLS trailing-slash fix + verify ==="
ssh "$VPS" "bash $REMOTE_DIR/fix-ols-vhost-proxy.sh"

echo ""
echo "=== Done. Test in browser: ==="
echo "  https://veriaguide.gr/restaurants"
echo "  https://veriaguide.gr/cafes"
echo "  https://veriaguide.gr/wp-admin"
