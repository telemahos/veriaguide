# VeriaGuide – Session Handoff (Stand: 23. Juni 2026)

> Neue Cursor-Session: `@VPS_SESSION_HANDOFF.md` anhängen und Aufgabe beschreiben.

---

## Server

| Eigenschaft | Wert |
|-------------|------|
| Host | `***REMOVED***` |
| SSH | `ssh root@***REMOVED***` oder `ssh vps` |
| SSH-Key | `~/.ssh/id_ed25519` (Passphrase, **nicht** Server-Passwort) |
| SSH-Alias | `vps` / `SSH_HOST` in `~/.ssh/config` |
| OS | AlmaLinux 9.8 |
| Panel | CyberPanel + OpenLiteSpeed |
| Domain | `veriaguide.gr` |
| DNS | A-Record → `***REMOVED***` (Papaki: dns1/dns2.papaki.gr) |
| Projekt-Pfad | `$WP_DOCUMENT_ROOT/` |

### Verzeichnisstruktur (Server)

```
$WP_DOCUMENT_ROOT/
├── wp-admin/, wp-content/, wp-config.php   ← WordPress (nativ, CyberPanel)
├── frontend/                                ← FastAPI (Docker Build Context)
├── data/                                    ← Import-Skripte
├── wordpress/                               ← Plugin-Quelle (lokal im Repo)
├── utility_scripts/                           ← Deploy/OLS/SSL-Skripte
├── redis-data/
├── docker-compose.vps.yml
├── .env
└── fix-ols-vhost-proxy.sh
```

---

## Architektur

```
Browser → OpenLiteSpeed :443
  ├── /wp-admin, /wp-json, /wp-login.php, /wp-content, /wp-includes → WordPress (PHP)
  └── alles andere → FastAPI Docker :8000
                        └── Redis Docker (intern)
                        └── WordPress API: http://veriaguide.gr/wp-json/wp/v2
```

**OLS vhost:** `/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf`  
**Wichtig:** Trailing-Slash-Regel aktiv – `^(.+)/$` wird ohne Slash an FastAPI proxied.

---

## Docker

```bash
cd $WP_DOCUMENT_ROOT
docker compose -f docker-compose.vps.yml ps
docker compose -f docker-compose.vps.yml logs -f frontend
docker compose -f docker-compose.vps.yml build --no-cache frontend
docker compose -f docker-compose.vps.yml up -d frontend
docker exec veriaguide_redis redis-cli FLUSHALL
docker restart veriaguide_frontend
```

| Container | Port |
|-------------|------|
| `veriaguide_frontend` | `8000:8000` |
| `veriaguide_redis` | intern `6379` |

**.env (wichtig):**
- `WP_API_URL=http://veriaguide.gr/wp-json/wp/v2`
- `REDIS_URL=redis://veriaguide_redis:6379/0`
- Docker mappt `veriaguide.gr` → `host-gateway`

---

## Produktions-Status (alles OK ✅)

| Test | Status |
|------|--------|
| `https://veriaguide.gr/` | ✅ 200, FastAPI, Hero + About-Sektion |
| `https://veriaguide.gr/restaurants` | ✅ 200, 15 Listings (FastAPI) |
| `https://veriaguide.gr/cafes` | ✅ 200 |
| `https://veriaguide.gr/wp-json/` | ✅ 200, WordPress |
| `https://veriaguide.gr/wp-json/wp/v2/restaurants` | ✅ 111 Restaurants |
| `https://veriaguide.gr/wp-json/veriaguide/v1/homepage-settings` | ✅ 200 |
| `https://veriaguide.gr/wp-login.php` | ✅ 200 |
| `https://veriaguide.gr/wp-admin/` | ✅ 302 (Login) |
| SSL | ✅ Let's Encrypt (gültig bis 21. Sep 2026) |
| Performance | ✅ ~0,3–1,0 s pro Seite (Redis-Cache warm) |
| WP Sitename | ✅ **Veria Guide** (korrigiert von „Veoia Guide“) |

---

## WordPress

- Installiert über CyberPanel, MariaDB nativ
- Plugins: ACF, CPT UI, `veriaguide-cpt.php`, Google Maps API, WPvivid
- Daten: 111 Restaurants, 73 Cafés, 65 Religious Sites, etc.
- **Homepage bearbeiten:** `wp-admin` → **Homepage Settings** (ACF Options Page)
  - Hero Slides (Bild-URL, Titel, Untertitel)
  - Hero Speed
  - About Veria Text
  - Homepage Sections (Reihenfolge, Anzahl, aktiv/inaktiv)

### Custom REST API (Plugin `veriaguide-cpt.php` v1.3)

| Endpoint | Zweck |
|----------|-------|
| `/wp-json/veriaguide/v1/homepage-settings` | Sektionen, Hero, About-Text |
| `/wp-json/veriaguide/v1/menus` | Navigation |

Plugin-Pfad Server: `$WP_DOCUMENT_ROOT/wp-content/plugins/veriaguide-cpt.php`  
Plugin-Quelle lokal: `wordpress/veriaguide-cpt.php`

---

## GitHub

| | |
|--|--|
| URL | https://github.com/telemahos/veriaguide (private) |
| Remote | `origin` → `https://github.com/telemahos/veriaguide.git` |
| Branches | `main`, `ai_guide`, `booking` |
| Auth | `gh auth login` + HTTPS (SSH-Key ist für VPS, nicht GitHub) |

**Letzter Commit auf `main`:** `d5fe6e2` – exclude runtime data from version control

**Lokal uncommitted (muss noch committed werden):**
- `wordpress/veriaguide-cpt.php` (v1.2: ACF Homepage Settings, Sitename-Fix)
- `frontend/app/services/homepage_service.py` (Default Hero/About-Texte)

---

## Wichtige lokale Dateien

| Datei | Zweck |
|-------|-------|
| `VPS-INSTALLATION-STEPS.md` | VPS-Installation Schritt für Schritt |
| `CLEAN_INSTALLATION_GUIDE.md` | Vollständiger Guide |
| `docker-compose.vps.yml` | Nur Redis + Frontend (Server) |
| `docker-compose.prod.yml` | Alt, **nicht** auf Server verwenden |
| `utility_scripts/fix-ols-vhost-proxy.sh` | OLS Proxy + Trailing-Slash-Fix |
| `utility_scripts/deploy-trailing-slash-fix.sh` | Deploy Frontend + OLS |
| `utility_scripts/issue-letsencrypt-ssl.sh` | SSL erneuern (auf Server) |
| `wordpress/veriaguide-cpt.php` | WordPress Plugin (CPT + REST API + ACF) |

---

## Deploy vom Mac

```bash
# SSH-Key laden
ssh-add ~/.ssh/id_ed25519

# Plugin deployen
scp wordpress/veriaguide-cpt.php vps:$WP_DOCUMENT_ROOT/wp-content/plugins/veriaguide-cpt.php

# Frontend deployen + rebuild
rsync -avz --exclude '__pycache__' frontend/ vps:$WP_DOCUMENT_ROOT/frontend/
ssh vps "cd $WP_DOCUMENT_ROOT && docker compose -f docker-compose.vps.yml build --no-cache frontend && docker compose -f docker-compose.vps.yml up -d frontend"

# Cache leeren nach WP-Änderungen
ssh vps "docker exec veriaguide_redis redis-cli FLUSHALL && docker restart veriaguide_frontend"
```

---

## Verifikation

```bash
# Öffentlich
curl -sk -o /dev/null -w "homepage: %{http_code}\n" https://veriaguide.gr/
curl -sk -o /dev/null -w "restaurants: %{http_code}\n" https://veriaguide.gr/restaurants
curl -sk https://veriaguide.gr/wp-json/veriaguide/v1/homepage-settings | python3 -m json.tool | head -20

# Auf dem Server
ssh vps
curl -sk -H "Host: veriaguide.gr" https://127.0.0.1/restaurants | grep -c restaurant-listing   # Erwartung: 12+
curl -sk -H "Host: veriaguide.gr" https://127.0.0.1/wp-json/wp/v2/restaurants?per_page=1 | head -c 80
```

---

## Erledigte Fixes (diese Sessions)

1. ✅ OLS Trailing-Slash → FastAPI für `/restaurants`, `/cafes`, etc.
2. ✅ `redirect_slashes=False` in FastAPI
3. ✅ Redis-Cache für `get_all_posts_for_type` + JWT-Token-Cache
4. ✅ Doppelte API-Aufrufe in Listen-Seiten entfernt
5. ✅ Plugin REST API: `homepage-settings` + `menus`
6. ✅ SSL Let's Encrypt (DNS bei Papaki repariert)
7. ✅ GitHub Repo erstellt, History bereinigt (ohne qdrant_data, wp-core)
8. ✅ WP Sitename „Veria Guide“
9. ✅ Homepage Hero + About-Text via ACF Options Page
10. ✅ WordPress Primary Navigation (auto-seeded, REST API)
11. ✅ Homepage-Sektionen via ACF Repeater konfigurierbar

---

## Offen / Nächste Schritte

- [x] **Commit + Push** der uncommitted Änderungen (`veriaguide-cpt.php` v1.2, `homepage_service.py`)
- [x] **Navigation-Menü** in WordPress anlegen (aktuell Fallback-Menü in FastAPI)
- [x] **Homepage-Sektionen** optional in ACF konfigurierbar machen (aktuell Defaults)
- [ ] **SSL Auto-Renew** prüfen: `acme.sh` / CyberPanel Cron
- [ ] Branches `ai_guide` / `booking` – Features weiterentwickeln

---

## SSH-Hinweise für Cursor-Agent

- Funktioniert mit: `ssh-add ~/.ssh/id_ed25519` + Passphrase
- Funktioniert **nicht**: `BatchMode=yes` ohne geladenen Key
- **Sicherheit:** Passphrase nicht im Chat teilen

---

## Prompt für neue Session (Beispiel)

```
@VPS_SESSION_HANDOFF.md

[Lies den Handoff und mache X]
```

Beispiele:
- „Committe und pushe die offenen Änderungen“
- „Richte das WordPress-Navigationsmenü ein“
- „Arbeite am ai_guide Branch weiter“
