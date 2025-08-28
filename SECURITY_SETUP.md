# VeriaGuide Security Setup Guide

## 🔒 Sicherheitsverbesserungen implementiert

### ✅ Was wurde korrigiert:

1. **Hardcoded Credentials entfernt**
   - Alle Passwörter aus `docker-compose.yml` in `.env` verschoben
   - Sichere Standardpasswörter generiert
   - Environment-basierte Konfiguration

2. **WordPress API Authentifizierung**
   - JWT-Token Integration in alle API-Requests
   - Sichere Authentifizierung für WordPress REST API

3. **Admin-Endpoints abgesichert**
   - API-Key Authentifizierung mit constant-time comparison
   - Logging von Sicherheitsereignissen
   - Debug-Mode Bypass entfernt

4. **HTTPS/SSL Konfiguration** (nur Production)
   - Nginx Reverse Proxy mit SSL
   - Let's Encrypt Integration
   - Automatische HTTP zu HTTPS Redirects

## 🚀 Development vs Production

### Development (HTTP, lokaler Server):
```bash
# Starten
./start-dev.sh

# Oder manuell:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Zugriff:
# Frontend: http://localhost:8000
# WordPress: http://localhost:8086
# Redis: localhost:6379
# Database: localhost:3306
```

### Production (HTTPS, SSL):
```bash
# 1. SSL Zertifikate erstellen (einmalig)
./setup-ssl.sh veriaguide.com admin@veriaguide.com

# 2. Production starten
./start-prod.sh

# Oder manuell:
docker-compose -f docker-compose.yml -f docker-compose.production.yml -f docker-compose.ssl.yml up -d

# Zugriff:
# Frontend: https://veriaguide.com
# WordPress Admin: https://veriaguide.com/wp-admin (IP-beschränkt)
```

## 🔑 Wichtige Sicherheitseinstellungen

### 1. Environment Variables (.env)
```bash
# WICHTIG: Diese Passwörter in Production ändern!
MYSQL_ROOT_PASSWORD=VG_secure_root_2025!
MYSQL_PASSWORD=VG_wp_secure_2025!
WP_API_PASSWORD=VG_admin_secure_2025!
SECRET_KEY=VG_very_secure_secret_key_change_in_production_2025
ADMIN_API_KEY=VG_admin_api_key_secure_2025
```

### 2. Admin API Zugriff
```bash
# Admin-Endpoints benötigen API-Key im Header:
curl -H "X-API-Key: VG_admin_api_key_secure_2025" \
     http://localhost:8000/admin/cache-info
```

### 3. WordPress API Authentifizierung
- Alle WordPress API-Requests verwenden jetzt JWT-Token
- Automatische Token-Generierung und -Verwendung
- Sichere Authentifizierung für alle Content-Abfragen

## 🧪 Sicherheitstests

### Automatische Tests:
```bash
# Sicherheitstests ausführen (Bash-Version)
./test-security.sh

# Oder Python-Version (benötigt requests)
pip3 install requests python-dotenv
python3 test-security.py
```

### Manuelle Tests:
1. **Admin-Zugriff ohne API-Key**: `curl http://localhost:8000/admin/cache-info`
   - Erwartung: 401 Unauthorized

2. **Admin-Zugriff mit API-Key**: 
   ```bash
   curl -H "X-API-Key: VG_admin_api_key_secure_2025" \
        http://localhost:8000/admin/cache-info
   ```
   - Erwartung: 200 OK mit Cache-Informationen

3. **XSS-Test**: `http://localhost:8000/search?q=<script>alert('xss')</script>`
   - Erwartung: 400 Bad Request oder sanitized output

## 🔧 Production Deployment Checklist

### Vor dem Deployment:
- [ ] Alle Passwörter in `.env` geändert
- [ ] `ADMIN_API_KEY` auf sicheren Wert gesetzt
- [ ] `SECRET_KEY` generiert (z.B. mit `openssl rand -hex 32`)
- [ ] Domain-Namen in SSL-Konfiguration angepasst
- [ ] DNS auf Server-IP konfiguriert

### SSL Setup (Production):
```bash
# 1. Domain und Email anpassen
./setup-ssl.sh your-domain.com your-email@domain.com

# 2. Automatische Erneuerung testen
./renew-ssl.sh

# 3. Crontab für automatische Erneuerung prüfen
crontab -l
```

### Nach dem Deployment:
- [ ] HTTPS-Zugriff testen: `https://your-domain.com`
- [ ] HTTP zu HTTPS Redirect testen
- [ ] SSL-Zertifikat Gültigkeit prüfen
- [ ] Admin-Endpoints Zugriffsbeschränkung testen
- [ ] WordPress Admin IP-Beschränkung testen

## 🛡️ Sicherheitsfeatures im Detail

### 1. Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` (stricter in production)
- `Strict-Transport-Security` (nur HTTPS)

### 2. Rate Limiting
- Allgemeine Requests: 100/Minute
- Admin-Endpoints: 1/Sekunde
- API-Endpoints: 10/Sekunde (via nginx)

### 3. Input Validation
- XSS-Schutz durch HTML-Escaping
- SQL-Injection-Schutz durch Parameterisierung
- Längenbeschränkungen für alle Eingaben
- Sichere String-Validierung

### 4. Access Control
- Admin-Endpoints: API-Key erforderlich
- WordPress Admin: IP-Beschränkung (Production)
- Database: Keine direkte Exposition (Production)
- Redis: Keine direkte Exposition (Production)

## 🚨 Troubleshooting

### Problem: Admin-Endpoints geben 401 zurück
```bash
# Lösung: API-Key prüfen
echo $ADMIN_API_KEY
# Oder in .env Datei prüfen
```

### Problem: CSP-Fehler bei externen Ressourcen
```bash
# Lösung: CSP und Assets reparieren
./fix-csp-and-assets.sh
docker-compose restart frontend
```

### Problem: 404-Fehler bei Bildern
```bash
# Lösung: Fehlende Placeholder-Bilder erstellen
./fix-csp-and-assets.sh
```

### Problem: SSL-Zertifikat Fehler
```bash
# Zertifikat neu generieren
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml run --rm certbot \
    certonly --webroot --webroot-path=/var/www/certbot \
    --email your-email@domain.com --agree-tos --no-eff-email \
    -d your-domain.com -d www.your-domain.com
```

### Problem: WordPress API Authentifizierung fehlschlägt
```bash
# WordPress JWT Plugin prüfen
# In WordPress Admin: Plugins > JWT Authentication for WP REST API
```

## 📞 Support

Bei Problemen:
1. Logs prüfen: `docker-compose logs -f`
2. Sicherheitstests ausführen: `./test-security.py`
3. Konfiguration validieren: `docker-compose config`

---

**Wichtig**: Diese Sicherheitsmaßnahmen sind ein guter Start, aber für Production sollten zusätzliche Maßnahmen wie WAF, DDoS-Schutz und regelmäßige Security-Audits implementiert werden.