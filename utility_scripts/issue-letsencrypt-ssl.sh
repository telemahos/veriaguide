#!/bin/bash
# Issue Let's Encrypt SSL for veriaguide.gr (run on VPS after DNS A-record is fixed)
set -e

echo "=== DNS check ==="
IP=$(dig +short veriaguide.gr A @8.8.8.8 | head -1)
if [ -z "$IP" ]; then
    echo "ERROR: veriaguide.gr has no A record (SERVFAIL)."
    echo "Fix at Papaki (dns1/dns2.papaki.gr): A record -> 178.105.68.81"
    exit 1
fi
echo "veriaguide.gr -> $IP"

echo ""
echo "=== Issue certificate ==="
/root/.acme.sh/acme.sh --issue -d veriaguide.gr -w /home/veriaguide.gr/public_html --server letsencrypt --force

echo ""
echo "=== Install certificate ==="
/root/.acme.sh/acme.sh --install-cert -d veriaguide.gr \
  --cert-file /etc/letsencrypt/live/veriaguide.gr/fullchain.pem \
  --key-file /etc/letsencrypt/live/veriaguide.gr/privkey.pem \
  --fullchain-file /etc/letsencrypt/live/veriaguide.gr/fullchain.pem \
  --reloadcmd "/usr/local/lsws/bin/lswsctrl restart"

echo ""
openssl x509 -in /etc/letsencrypt/live/veriaguide.gr/fullchain.pem -noout -subject -issuer -dates
echo "Done."
