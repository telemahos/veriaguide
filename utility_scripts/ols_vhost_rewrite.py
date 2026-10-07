"""Canonical OpenLiteSpeed rewrite/proxy block for veriaguide.gr.

Used by fix-ols-vhost-proxy.sh. Keep HTTP→HTTPS + www→apex and Authorization
passthrough in this module so re-running the script does not drop them.
"""

from __future__ import annotations

import re
from pathlib import Path

# Exact live security block (must sit immediately after RewriteEngine On).
SECURITY_BLOCK = r"""# BEGIN security-hardening-20261007-rest
# Keep ACME HTTP-01 reachable over plain http (acme.sh webroot = public_html)
RewriteCond %{REQUEST_URI} ^/\.well-known/acme-challenge/
RewriteRule ^ - [L]
# Force HTTPS + canonical apex (preserve path/query). Must run before proxy rules.
RewriteCond %{HTTPS} !=on [OR]
RewriteCond %{HTTP_HOST} ^www\.veriaguide\.gr$ [NC]
RewriteRule ^ https://veriaguide.gr%{REQUEST_URI} [R=301,L]
# END security-hardening-20261007-rest"""

# Defense-in-depth: OLS rewrite env for PHP Application Passwords / REST API.
AUTH_PASSTHROUGH = r"""# Pass Authorization to PHP for Application Passwords / REST API
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]"""

REWRITE_BLOCK = f"""
rewrite  {{
 enable                  1
  autoLoadHtaccess        1
  rules <<<END_rules
RewriteEngine On

{SECURITY_BLOCK}

{AUTH_PASSTHROUGH}

# Fix wp-login trailing slash redirect loop
RewriteRule ^wp-login\\.php/$ /wp-login.php [R=301,L]

# WordPress paths stay on OpenLiteSpeed/PHP
RewriteCond %{{REQUEST_URI}} ^/wp-admin [OR]
RewriteCond %{{REQUEST_URI}} ^/wp-json [OR]
RewriteCond %{{REQUEST_URI}} ^/wp-login\\.php [OR]
RewriteCond %{{REQUEST_URI}} ^/wp-content [OR]
RewriteCond %{{REQUEST_URI}} ^/wp-includes
RewriteRule ^ - [L]

# FastAPI frontend proxy
RewriteRule ^static/(.*)$ http://127.0.0.1:8000/static/$1 [P,L]
# 301 trailing slashes to non-slash canonical, except locale homes /el/ and /de/
# (OpenLiteSpeed was not honoring a prior dedicated [P] rule for those paths).
RewriteCond %{{REQUEST_URI}} !^/(el|de)/$
RewriteRule ^(.+)/$ /$1 [R=301,L]
# Proxy to FastAPI (preserves /el/ and /de/ trailing slash)
RewriteRule ^(.*)$ http://127.0.0.1:8000/$1 [P,L]
END_rules
}}

extprocessor 127.0.0.1:8000 {{
  type                    proxy
  address                 http://127.0.0.1:8000
  maxConns                100
  pcKeepAliveTimeout      60
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}}

"""


def apply_rewrite(text: str) -> str:
    """Replace OLS rewrite/proxy blocks with the canonical rewrite_block once."""
    text = re.sub(r"\nextprocessor frontend_proxy \{.*?\}\n", "\n", text, flags=re.S)
    text = re.sub(r"\nextprocessor 127\.0\.0\.1:8000 \{.*?\}\n", "\n", text, flags=re.S)
    text = re.sub(r"\ncontext /[^\n]*\{.*?(?=\ncontext |\nvhssl)", "\n", text, flags=re.S)
    text = re.sub(r"\nrewrite\s*\{.*?\n\}\n", "\n", text, flags=re.S)
    # Removals leave blank runs; collapse so a second apply matches the first.
    text = re.sub(r"\n{3,}", "\n\n", text)

    marker = "module cache {"
    if marker not in text:
        raise ValueError("vhost.conf has no 'module cache {' insertion point")
    # Insert once so a second apply cannot duplicate after rewrite stripping.
    return text.replace(marker, REWRITE_BLOCK + marker, 1)


def rewrite_vhost_file(path: Path) -> None:
    path.write_text(apply_rewrite(path.read_text()))


if __name__ == "__main__":
    import os
    import sys

    vhost = Path(os.environ.get("OLS_VHOST", "/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf"))
    if not vhost.is_file():
        print(f"vhost not found: {vhost}", file=sys.stderr)
        sys.exit(1)
    rewrite_vhost_file(vhost)
    print("vhost.conf updated (rewrite-based proxy with HTTPS/apex + auth passthrough)")
