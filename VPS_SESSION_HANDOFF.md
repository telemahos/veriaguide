# VeriaGuide VPS – Session Handoff

> Neue Cursor-Session: `@VPS_SESSION_HANDOFF.md` anhängen und Prompt unten einfügen.

## Server

- **SSH:** `ssh root@***REMOVED***` (Key: `~/.ssh/id_ed25519` + Passphrase)
- **Alias:** `vps` / `SSH_HOST` in `~/.ssh/config`
- **OS:** AlmaLinux 9.8, CyberPanel, OpenLiteSpeed
- **Project root:** `$WP_DOCUMENT_ROOT/`

## Architektur

```
Browser → OpenLiteSpeed :443
  ├── /wp-admin, /wp-json, /wp-login.php, /wp-content, /wp-includes → WordPress (nativ)
  └── alles andere → FastAPI Docker :8000 → Redis Docker
```

## Docker

```bash
cd $WP_DOCUMENT_ROOT
docker compose -f docker-compose.vps.yml ps
docker compose -f docker-compose.vps.yml logs -f frontend
docker exec veriaguide_redis redis-cli FLUSHALL
```

| Container | Port |
|-----------|------|
| `veriaguide_frontend` | 8000 |
| `veriaguide_redis` | intern |

**.env:** `WP_API_URL=http://veriaguide.gr/wp-json/wp/v2`, `REDIS_URL=redis://veriaguide_redis:6379/0`

## Was funktioniert (Stand Juni 2026)

- ✅ Homepage `https://veriaguide.gr/` (FastAPI)
- ✅ `wp-json/`, `wp-json/wp/v2/restaurants` (WordPress, 111 Restaurants)
- ✅ `wp-login.php` (200)
- ✅ FastAPI direkt: `curl http://127.0.0.1:8000/restaurants` → 12+ Listings

## Was noch kaputt ist

**Trailing-Slash-Problem:**

```
/restaurants → OLS 301 → /restaurants/ → WordPress .htaccess → „Veoia Guide“ Theme
FastAPI wird für Kategorie-URLs über HTTPS nicht erreicht.
```

## Fixes (noch ausführen)

### 1. OpenLiteSpeed vhost

**Datei:** `/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf`

- Doppelten `rewrite {}` Block entfernen (nur einer!)
- Vor Catch-all: `RewriteRule ^(.+)/$ http://127.0.0.1:8000/$1 [P,L]`
- `extprocessor 127.0.0.1:8000` muss existieren
- Skript: `utility_scripts/fix-ols-vhost-proxy.sh` (lokal + auf Server)

```bash
/usr/local/lsws/bin/lswsctrl restart
```

### 2. FastAPI

`frontend/main.py`: `redirect_slashes=False` bei `FastAPI(...)`

```bash
docker compose -f docker-compose.vps.yml up -d --build --no-cache frontend
docker exec veriaguide_redis redis-cli FLUSHALL
```

### 3. Code deployen (falls nicht auf Server)

- `frontend/app/api/wordpress.py` – WP_API_URL, kein Dummy-Fallback in Production
- `frontend/app/services/homepage_service.py`
- `frontend/templates/*/list.html` – opening_hours Fix

## Verifikation

```bash
curl -sk -H "Host: veriaguide.gr" "https://127.0.0.1/wp-json/wp/v2/restaurants?per_page=1" | head -c 80
# → [{"id":...

curl -sk -H "Host: veriaguide.gr" https://127.0.0.1/restaurants | grep -c restaurant-listing
# → 12+ (nicht 0!)

curl -sk -o /dev/null -w "%{http_code}\n" -H "Host: veriaguide.gr" https://127.0.0.1/wp-login.php
# → 200
```

## SSH vom Mac (Agent)

```bash
/usr/bin/expect << 'EOF'
spawn ssh -i ~/.ssh/id_ed25519 root@***REMOVED*** "BEFEHL"
expect "passphrase" { send "PASSPHRASE\r" }
expect eof
EOF
```

`BatchMode=yes` ohne Passphrase funktioniert nicht.

## Docs im Repo

- `VPS-INSTALLATION-STEPS.md`
- `CLEAN_INSTALLATION_GUIDE.md`
- `utility_scripts/fix-ols-vhost-proxy.sh`

## WordPress

- Nativ via CyberPanel, Daten vorhanden (Restaurants, Cafés, Hotels, …)
- Plugin-API: `/wp-json/veriaguide/v1/homepage-settings`
- Site-Name in WP: „Veoia Guide“ (Tippfehler)
