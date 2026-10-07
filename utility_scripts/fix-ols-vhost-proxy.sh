#!/bin/bash
# Fix OpenLiteSpeed: WordPress native + Rewrite proxy to FastAPI (with trailing-slash fix).
# Also emits HTTP→HTTPS / www→apex 301 (ACME HTTP-01 excluded) and Authorization passthrough.
#
# Env:
#   OLS_VHOST        vhost.conf path (default: /usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf)
#   OLS_SKIP_VERIFY  if 1, skip lsws restart, curl checks, docker (for tests)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VHOST="${OLS_VHOST:-/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf}"
export OLS_VHOST="$VHOST"

if [[ ! -f "$VHOST" ]]; then
  echo "vhost not found: $VHOST" >&2
  exit 1
fi

BACKUP="${VHOST}.bak.$(date +%Y%m%d_%H%M%S)"
cp "$VHOST" "$BACKUP"
echo "Backup: $BACKUP"

python3 "$SCRIPT_DIR/ols_vhost_rewrite.py"

if [[ "${OLS_SKIP_VERIFY:-0}" == "1" ]]; then
  echo "OLS_SKIP_VERIFY=1: skipped lsws restart and live checks."
  exit 0
fi

/usr/local/lsws/bin/lswsctrl restart
sleep 3

echo ""
echo "=== Verification ==="
curl -s -o /dev/null -w "wp-json root: %{http_code}\n" -k -H "Host: veriaguide.gr" https://127.0.0.1/wp-json/
curl -s -o /dev/null -w "wp-json restaurants: %{http_code}\n" -k -H "Host: veriaguide.gr" "https://127.0.0.1/wp-json/wp/v2/restaurants?per_page=1"
curl -s -k -H "Host: veriaguide.gr" "https://127.0.0.1/wp-json/wp/v2/restaurants?per_page=1" | head -c 80
echo ""
curl -s -o /dev/null -w "wp-login: %{http_code}\n" -k -H "Host: veriaguide.gr" https://127.0.0.1/wp-login.php
curl -s -k -H "Host: veriaguide.gr" https://127.0.0.1/wp-login.php | grep -o "user_login\|wp-login" | head -2
curl -s -o /dev/null -w "homepage: %{http_code}\n" -k -H "Host: veriaguide.gr" https://127.0.0.1/

echo "HTTP apex Location:"
curl -sI http://veriaguide.gr/ | tr -d '\r' | grep -iE '^(HTTP/|Location:)'
echo "HTTP www Location:"
curl -sI http://www.veriaguide.gr/ | tr -d '\r' | grep -iE '^(HTTP/|Location:)'

docker exec veriaguide_redis redis-cli FLUSHALL 2>/dev/null || true
docker restart veriaguide_frontend 2>/dev/null || true
sleep 15
echo "restaurant-listings (proxy): $(curl -sk -H 'Host: veriaguide.gr' https://127.0.0.1/restaurants | grep -c restaurant-listing)"
echo "restaurant-listings (direct): $(curl -sk http://127.0.0.1:8000/restaurants | grep -c restaurant-listing)"
echo "Done."
