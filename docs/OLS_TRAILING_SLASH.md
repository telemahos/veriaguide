# OpenLiteSpeed trailing slashes (veriaguide.gr)

FastAPI listing **canonicals** have **no** trailing slash (`/cafes/floretta`, `/el/cafes/floretta`). Locale homepages **do** (`/el/`, `/de/`).

## What went wrong

`utility_scripts/fix-ols-vhost-proxy.sh` used to **proxy** `^(.+)/$` to FastAPI **without** the slash (`[P,L]`). The browser URL stayed `/cafes/floretta/` and OLS returned **200**, while the HTML canonical pointed at the non-slash URL. FastAPI never saw the slash, so app middleware could not 301 it.

## What to run on the VPS

Re-apply `utility_scripts/fix-ols-vhost-proxy.sh` (or the equivalent `rewrite` block in the vhost):

1. Proxy `/el/` and `/de/` **with** the slash.
2. **301** every other `.../` path to the same path without the slash (`[R=301,L]`).
3. Proxy the remaining requests to `127.0.0.1:8000`.

The FastAPI `TrailingSlashRedirectMiddleware` still 301s listing (and other) trailing-slash URLs when the request reaches the app (tests, direct `:8000`).
