#!/bin/bash
# Fix OpenLiteSpeed: WordPress native + Rewrite proxy to FastAPI (with trailing-slash fix)
set -e

VHOST="/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf"
BACKUP="${VHOST}.bak.$(date +%Y%m%d_%H%M%S)"
cp "$VHOST" "$BACKUP"
echo "Backup: $BACKUP"

python3 << 'PY'
from pathlib import Path
import re

vhost = Path("/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf")
text = vhost.read_text()

# Remove all proxy extprocessors and duplicate rewrite blocks from prior fix attempts
text = re.sub(r'\nextprocessor frontend_proxy \{.*?\}\n', '\n', text, flags=re.S)
text = re.sub(r'\nextprocessor 127\.0\.0\.1:8000 \{.*?\}\n', '\n', text, flags=re.S)
text = re.sub(r'\ncontext /[^\n]*\{.*?(?=\ncontext |\nvhssl)', '\n', text, flags=re.S)
text = re.sub(r'\nrewrite\s*\{.*?\n\}\n', '\n', text, flags=re.S)

rewrite_block = '''
rewrite  {
 enable                  1
  autoLoadHtaccess        1
  rules <<<END_rules
RewriteEngine On

# Fix wp-login trailing slash redirect loop
RewriteRule ^wp-login\\.php/$ /wp-login.php [R=301,L]

# WordPress paths stay on OpenLiteSpeed/PHP
RewriteCond %{REQUEST_URI} ^/wp-admin [OR]
RewriteCond %{REQUEST_URI} ^/wp-json [OR]
RewriteCond %{REQUEST_URI} ^/wp-login\\.php [OR]
RewriteCond %{REQUEST_URI} ^/wp-content [OR]
RewriteCond %{REQUEST_URI} ^/wp-includes
RewriteRule ^ - [L]

# FastAPI frontend proxy
RewriteRule ^static/(.*)$ http://127.0.0.1:8000/static/$1 [P,L]
# Strip trailing slash before proxying (prevents WordPress .htaccess from catching /restaurants/)
RewriteRule ^(.+)/$ http://127.0.0.1:8000/$1 [P,L]
RewriteRule ^(.*)$ http://127.0.0.1:8000/$1 [P,L]
END_rules
}

extprocessor 127.0.0.1:8000 {
  type                    proxy
  address                 http://127.0.0.1:8000
  maxConns                100
  pcKeepAliveTimeout      60
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}

'''

text = text.replace('module cache {', rewrite_block + 'module cache {')
vhost.write_text(text)
print("vhost.conf updated (rewrite-based proxy with trailing-slash fix)")
PY

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

docker exec veriaguide_redis redis-cli FLUSHALL 2>/dev/null || true
docker restart veriaguide_frontend 2>/dev/null || true
sleep 15
echo "restaurant-listings (proxy): $(curl -sk -H 'Host: veriaguide.gr' https://127.0.0.1/restaurants | grep -c restaurant-listing)"
echo "restaurant-listings (direct): $(curl -sk http://127.0.0.1:8000/restaurants | grep -c restaurant-listing)"
echo "Done."
