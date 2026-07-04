#!/bin/bash
# Issue Let's Encrypt SSL for veriaguide.gr + www (run on VPS as root)
set -e

DOMAIN="veriaguide.gr"
WWW="www.veriaguide.gr"
WEBROOT="$WP_DOCUMENT_ROOT"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

echo "=== DNS check ==="
APEX_IP=$(dig +short "${DOMAIN}" A @8.8.8.8 | head -1)
WWW_IP=$(dig +short "${WWW}" A @8.8.8.8 | head -1)

if [ -z "$APEX_IP" ]; then
    echo "ERROR: ${DOMAIN} has no A record."
    exit 1
fi
if [ -z "$WWW_IP" ]; then
    echo "ERROR: ${WWW} has no A record."
    exit 1
fi
echo "${DOMAIN} -> ${APEX_IP}"
echo "${WWW} -> ${WWW_IP}"

echo ""
echo "=== Issue certificate (apex + www) ==="
/root/.acme.sh/acme.sh --issue -d "${DOMAIN}" -d "${WWW}" \
  -w "${WEBROOT}" --server letsencrypt --force

echo ""
echo "=== Install certificate ==="
/root/.acme.sh/acme.sh --install-cert -d "${DOMAIN}" \
  --cert-file "${CERT_DIR}/fullchain.pem" \
  --key-file "${CERT_DIR}/privkey.pem" \
  --fullchain-file "${CERT_DIR}/fullchain.pem" \
  --reloadcmd "/usr/local/lsws/bin/lswsctrl restart"

echo ""
echo "=== Certificate SANs ==="
openssl x509 -in "${CERT_DIR}/fullchain.pem" -noout -subject -issuer -dates -ext subjectAltName
echo "Done. Run utility_scripts/fix-www-ssl-redirect.sh to add www -> apex redirect."
