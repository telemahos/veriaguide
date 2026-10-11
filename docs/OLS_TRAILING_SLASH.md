# OpenLiteSpeed trailing slashes (veriaguide.gr)

FastAPI listing **canonicals** have **no** trailing slash (`/cafes/floretta`, `/el/cafes/floretta`). Locale homepages **do** (`/el/`, `/de/`).

## What went wrong

`utility_scripts/fix-ols-vhost-proxy.sh` used to **proxy** `^(.+)/$` to FastAPI **without** the slash (`[P,L]`). The browser URL stayed `/cafes/floretta/` and OLS returned **200**, while the HTML canonical pointed at the non-slash URL. FastAPI never saw the slash, so app middleware could not 301 it.

## What to run on the VPS

Re-apply `utility_scripts/fix-ols-vhost-proxy.sh` (or the equivalent `rewrite` block in the vhost). The script is idempotent. After `RewriteEngine On` it always emits the HTTPS/apex security block (ACME `/.well-known/acme-challenge/` stays on HTTP), then the Authorization passthrough, then proxy rules.

1. **301** `.../` paths to the same path without the slash (`[R=301,L]`), with a **`RewriteCond`** that **excludes** locale homes `/el/` and `/de/`.
2. Proxy the remaining requests to `127.0.0.1:8000` (locale homes keep the trailing slash).

```bash
# on the VPS, from the repo checkout
sudo bash utility_scripts/fix-ols-vhost-proxy.sh

# HTTPS / apex (path and query preserved)
curl -sI http://veriaguide.gr/
curl -sI http://www.veriaguide.gr/
# both should 301 to https://veriaguide.gr/
```

Offline check of generated rules:

```bash
cd utility_scripts && python3 -m pytest test_ols_vhost_rewrite.py
```

A dedicated `RewriteRule ^(el|de)/$ … [P,L]` **before** the strip rule did **not** stick on OpenLiteSpeed (OLS still 301ed `/el/` → `/el` and `/de/` → `/de`). The `RewriteCond %{REQUEST_URI} !^/(el|de)/$` exclusion on the 301 rule is required.

The FastAPI `TrailingSlashRedirectMiddleware` still 301s listing (and other) trailing-slash URLs when the request reaches the app (tests, direct `:8000`).
