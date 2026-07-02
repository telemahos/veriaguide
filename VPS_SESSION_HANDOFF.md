# VeriaGuide – Session Handoff (Stand: 24. Juni 2026)

> Neue Cursor-Session: `@VPS_SESSION_HANDOFF.md` anhängen und Aufgabe beschreiben.

---

## Server

| Eigenschaft | Wert |
|-------------|------|
| Host | `178.105.68.81` |
| SSH | `ssh root@178.105.68.81` oder `ssh vps` |
| SSH-Key | `~/.ssh/id_ed25519` (Passphrase) |
| SSH-Alias | `vps` / `vps-veriaguide` in `~/.ssh/config` |
| OS | AlmaLinux 9.8 |
| Panel | CyberPanel + OpenLiteSpeed |
| Domain | `veriaguide.gr` |
| Projekt-Pfad | `/home/veriaguide.gr/public_html/` |

### Verzeichnisstruktur (Server)

```
/home/veriaguide.gr/public_html/
├── wp-admin/, wp-content/, wp-config.php   ← WordPress (nativ, CyberPanel)
├── frontend/                                ← FastAPI (Docker Build Context)
├── data/
├── wordpress/                               ← Plugin-Quelle (lokal im Repo)
├── utility_scripts/
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
cd /home/veriaguide.gr/public_html
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

## GitHub

| | |
|--|--|
| URL | https://github.com/telemahos/veriaguide (private) |
| Branch | `main` (aktuell, synced mit remote) |
| Letzter Commit | `5e72d23` – feat: redesign detail pages with gallery, nearby listings, and sidebar UX |
| Vorheriger | `08aa33d` – feat: ACF Homepage-Sektionen und WordPress-Navigation |

**Lokal:** Working tree clean, `main` = `origin/main`

---

## Deploy vom Mac

```bash
ssh-add ~/.ssh/id_ed25519

# Plugin deployen
scp wordpress/veriaguide-cpt.php vps:/home/veriaguide.gr/public_html/wp-content/plugins/veriaguide-cpt.php

# Frontend deployen + rebuild
rsync -avz --exclude '__pycache__' frontend/ vps:/home/veriaguide.gr/public_html/frontend/
ssh vps "cd /home/veriaguide.gr/public_html && docker compose -f docker-compose.vps.yml build frontend && docker compose -f docker-compose.vps.yml up -d frontend"

# Cache leeren nach WP-/Frontend-Änderungen
ssh vps "docker exec veriaguide_redis redis-cli FLUSHALL && docker restart veriaguide_frontend"
```

**Hinweis:** Frontend wurde zuletzt mehrfach auf VPS deployed (Design + Detail-UX). Live-Stand entspricht Commit `5e72d23`.

---

## WordPress

- Plugins: ACF, CPT UI, `veriaguide-cpt.php` **v1.3**, Google Maps API, WPvivid
- **Homepage bearbeiten:** `wp-admin` → **Homepage Settings** (ACF Options Page)
- **Navigation:** WordPress Primary Menu (REST `/wp-json/veriaguide/v1/menus`)

### Custom REST API (Plugin `veriaguide-cpt.php` v1.3)

| Endpoint | Zweck |
|----------|-------|
| `/wp-json/veriaguide/v1/homepage-settings` | Sektionen, Hero, About-Text |
| `/wp-json/veriaguide/v1/menus` | Navigation |

Plugin-Pfad Server: `/home/veriaguide.gr/public_html/wp-content/plugins/veriaguide-cpt.php`  
Plugin-Quelle lokal: `wordpress/veriaguide-cpt.php`

---

## Frontend-Architektur (wichtig)

```
frontend/
├── main.py                          # Routes + build_detail_template_data()
├── app/
│   ├── api/wordpress.py             # get_all_locations() inkl. featured_image
│   ├── services/
│   │   ├── content_service.py       # get_related_items(), get_nearby_items()
│   │   └── template_service.py      # Detail-Context: related_items, nearby_items
│   └── utils/helpers.py             # split_display_title, haversine, placeholders
├── static/
│   ├── css/style.css                # Design-System, Detail-Gallery, Sidebar
│   └── js/main.js                   # Galerie, Placeholders, Favoriten
└── templates/base/
    ├── layout.html                  # Header, Footer, CSS ?v=20260624e
    ├── index.html                   # Homepage
    ├── macros/
    │   ├── directory.html           # Listing-Cards (Listen)
    │   └── detail_sections.html     # detail_section Macro
    └── partials/
        ├── detail_title.html        # Gekürzte Titel (split_display_title)
        ├── detail_gallery.html      # Hauptbild + Thumbs + Modal
        ├── detail_sidebar_listings.html  # Near This Site + More in Veria
        ├── detail_sidebar_actions.html # Save & Share (unten fixiert)
        └── detail_sidebar_extras.html  # Wrapper → listings only (legacy compat)
```

### Detail-Seiten Datenfluss

```python
# main.py → build_detail_template_data()
location_data = content_service.get_location_data_for_item(item, category)
related_items = content_service.get_related_items(post_type, slug)  # gleiche Kategorie
nearby_items = content_service.get_nearby_items(location_data, slug, id)  # geo, alle Kategorien, 12 km, max 4
# Duplikate aus related_items entfernen wenn in nearby_items
```

---

## Erledigte Design-/UX-Arbeiten (Sessions bis 24.06.2026)

### Homepage & Global (Design 1–4, 11–12) ✅ deployed
1. Header vereinfacht (keine Top-Bar, schlanke Navbar)
2. Detail-Titel gekürzt (`split_display_title` Filter)
3. Hero-Suche vereinfacht (ein Feld + Category-Chips)
4. Visuelle Identität: Playfair Display, Terrakotta `#c8863a`, Dunkelblau `#0f2d5c`
5. About-Sektion zweispaltig mit Quicklinks
6. Homepage-Sektionen: Card-Layout mit Section-Header

### Listen-Seiten (Design 5–7) ✅ deployed
5. `directory_listing_card` Macro in allen `list.html`
6. Sticky Sidebar (`.list-page-sidebar`)
7. Kategorie-Gradient-Placeholders (`.category-image-placeholder`)

### Detail-Seiten (Design 8–10) ✅ deployed + committed
8. **Sidebar:** Save & Share, Favoriten, „More in Veria“ (related)
9. **Content:** `detail_section` Macro statt `border-bottom`-Überschriften (alle 10 Kategorien)
10. **Galerie:** `detail_gallery.html` – Hauptbild, Thumbnail-Strip, Bootstrap-Modal/Carousel

### Detail-UX Verbesserungen (24.06.) ✅ deployed + committed `5e72d23`
- **Near This Site:** Geo-basierte Nearby-Listings (Haversine, 12 km Radius, max 4, alle Kategorien)
- **Galerie-Placeholder:** Kategorie-Gradient + Icon statt kaputtem `placeholder.jpg`
- **Sidebar-Thumbnails:** Fester 3rem-Wrapper (`detail-related-thumb-wrap`)
- **Save & Share unten fixiert:** Sidebar = scrollbarer Bereich + pinned Actions-Block
- **HTML-Entities:** `decode_entities` Filter (`&amp;` → `&`) in Nav + Titeln
- **Karte in Sidebar:** 220px Höhe (statt 300px)

---

## Detail-Templates (alle 10 Kategorien)

```
templates/{category}/detail.html
```

Kategorien: `religious_sites`, `museums`, `archaeological_sites`, `restaurants`, `cafes`,
`accommodations`, `ski_resorts`, `hiking_trails`, `tours`, `hidden_gems`

**Sidebar-Struktur (einheitlich):**
```html
<div class="detail-page-sidebar">
    <div class="detail-page-sidebar__scroll">
        <!-- Karte, Infos -->
        {% include "base/partials/detail_sidebar_listings.html" %}
    </div>
    {% include "base/partials/detail_sidebar_actions.html" %}
</div>
```

**Referenz-Implementierung:** `templates/religious_sites/detail.html`

---

## Wichtige CSS-Klassen

| Klasse | Zweck |
|--------|-------|
| `.detail-page-sidebar` | Sticky, max-height viewport, flex column |
| `.detail-page-sidebar__scroll` | Scrollbarer Inhalt oben |
| `.detail-sidebar-card--actions` | Save & Share, unten fixiert |
| `.detail-gallery__placeholder` | Leere Galerie mit Icon |
| `.detail-related-thumb-wrap` | 3×3rem Thumbnail-Container |
| `.detail-content-section` | Content-Abschnitte mit Akzentlinie |
| `.directory-listing-card` | Listen-Cards |
| `.list-page-sidebar` | Sticky Filter-Sidebar |

---

## Wichtige JS-Funktionen (`main.js`)

| Funktion | Zweck |
|----------|-------|
| `initializeDetailGalleries()` | Thumb-Klicks → Hauptbild + Carousel sync |
| `handleDetailGalleryImageError()` | Kaputtes Galerie-Bild → Gradient-Placeholder |
| `handleImageError()` | Listing-Placeholders (schützt `.detail-related-thumb`) |
| `syncFavoritesOnLoad()` | Favoriten-Sync |

---

## Helper-Funktionen (`helpers.py`)

| Funktion | Zweck |
|----------|-------|
| `split_display_title()` | SEO-Titel → `{title, subtitle}` |
| `decode_entities()` | HTML-Entities dekodieren |
| `is_placeholder_image()` | Erkennt Platzhalter-URLs |
| `get_category_placeholder_url()` | Kategorie-SVG-Placeholder |
| `get_category_gallery_icon()` | FA-Icon für leere Galerie |
| `haversine_distance_km()` | Distanz für Nearby |
| `get_featured_image()` | Gibt `None` zurück wenn kein echtes Bild |

---

## POST_TYPES (config)

```python
"museums", "archaeological_sites", "religious_sites", "restaurants",
"cafes", "accommodations", "ski_resorts"
```

**Hinweis:** Templates existieren auch für `hiking_trails`, `tours`, `hidden_gems` – aber diese sind **nicht** in `POST_TYPES` (config). Nearby/Listen für diese Kategorien ggf. eingeschränkt.

---

## Produktions-Status

| Test | Status |
|------|--------|
| `https://veriaguide.gr/` | ✅ 200 |
| `https://veriaguide.gr/religious_sites/...` | ✅ 200, Detail mit Nearby + Placeholder |
| `https://veriaguide.gr/wp-json/` | ✅ 200 |
| SSL | ✅ Let's Encrypt |
| Git | ✅ `main` @ `5e72d23` pushed |

---

## Offen / Nächste Schritte

- [ ] **HTTPS-Warnung im Browser** – User wollte das ignorieren; ggf. Mixed-Content prüfen
- [ ] **SSL Auto-Renew** prüfen: `acme.sh` / CyberPanel Cron
- [ ] **hiking_trails / tours / hidden_gems** in `POST_TYPES` aufnehmen (falls gewünscht)
- [ ] **Branches** `ai_guide` / `booking` – Features weiterentwickeln
- [ ] **Accommodations:** Doppelter Favoriten-Button (Header + Sidebar) – ggf. Header-Button entfernen
- [ ] **Design-Punkt 13+** aus ursprünglicher Liste – falls noch offen, User fragen

---

## Verifikation

```bash
# Öffentlich
curl -sk -o /dev/null -w "%{http_code}\n" https://veriaguide.gr/
curl -sk https://veriaguide.gr/religious_sites/holy-church-of-saint-andrew-of-kyriotissa-a-15th-century-treasure-in-veria-greece | rg "Near This Site|detail-gallery__placeholder"

# Nach Deploy
ssh vps "docker exec veriaguide_redis redis-cli FLUSHALL && docker restart veriaguide_frontend"
```

---

## SSH-Hinweise für Cursor-Agent

- Funktioniert mit: `ssh-add ~/.ssh/id_ed25519` + Passphrase
- Deploy/rsync/push brauchen ggf. User-Freigabe (Smart Mode)
- **Sprache:** User bevorzugt **Deutsch**
- **Commits:** Nur auf explizite Anfrage

---

## Prompt für neue Session (Beispiel)

```
@VPS_SESSION_HANDOFF.md

[Lies den Handoff und mache X]
```

Beispiele:
- „Deploye die letzten lokalen Änderungen auf den VPS“
- „Füge hiking_trails zu POST_TYPES hinzu“
- „Entferne den doppelten Favoriten-Button bei accommodations“
- „Arbeite am booking Branch weiter“
