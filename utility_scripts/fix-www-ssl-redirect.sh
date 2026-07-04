#!/bin/bash
# Extend SSL for www + redirect www.veriaguide.gr -> veriaguide.gr (run on VPS as root)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 1. Re-issue SSL (apex + www) ==="
bash "${SCRIPT_DIR}/issue-letsencrypt-ssl.sh"

VHOST="/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf"
BACKUP="${VHOST}.bak.www.$(date +%Y%m%d_%H%M%S)"

echo ""
echo "=== 2. Add www -> apex redirect in OpenLiteSpeed ==="
cp "$VHOST" "$BACKUP"
echo "Backup: $BACKUP"

python3 << 'PY'
from pathlib import Path
import re

vhost = Path("/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf")
text = vhost.read_text()

redirect_rules = """# Canonical host: www -> apex
RewriteCond %{HTTP_HOST} ^www\\.veriaguide\\.gr$ [NC]
RewriteRule ^(.*)$ https://veriaguide.gr/$1 [R=301,L]

"""

# Remove old www redirect if present
text = re.sub(
    r"# Canonical host: www -> apex\nRewriteCond %\{HTTP_HOST\} \^www\\.veriaguide\\.gr\$ \[NC\]\nRewriteRule \^\(\.\*\)\$ https://veriaguide.gr/\$1 \[R=301,L\]\n\n",
    "",
    text,
)

if "www.veriaguide.gr" in text and "Canonical host" in text:
    print("www redirect already configured")
else:
    marker = "RewriteEngine On\n\n"
    if marker in text:
        text = text.replace(marker, marker + redirect_rules, 1)
    else:
        raise SystemExit("Could not find RewriteEngine On in vhost.conf — edit manually.")

vhost.write_text(text)
print("vhost.conf updated with www -> veriaguide.gr redirect")
PY

/usr/local/lsws/bin/lswsctrl restart
sleep 3

echo ""
echo "=== 3. Verification ==="
echo -n "apex cert SANs: "
openssl s_client -connect veriaguide.gr:443 -servername veriaguide.gr </dev/null 2>/dev/null \
  | openssl x509 -noout -ext subjectAltName 2>/dev/null | tr '\n' ' '
echo ""
echo -n "www TLS verify: "
curl -sI "https://www.veriaguide.gr/" | head -1
echo -n "www redirect: "
curl -sI "https://www.veriaguide.gr/sitemap.xml" | grep -i "^location:" || true
echo -n "sitemap on apex: "
curl -s -o /dev/null -w "%{http_code}\n" "https://veriaguide.gr/sitemap.xml"
echo "Done."
