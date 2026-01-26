# VeriaGuide Setup für WordPress Container + CyberPanel MySQL

## 🎯 **Übersicht**
Du hast bereits:
- ✅ CyberPanel Server
- ✅ MySQL Datenbank (über CyberPanel)

Wir erstellen:
- 🐳 WordPress (Docker Container) → verbindet sich mit CyberPanel MySQL
- 🐳 FastAPI Frontend (Docker Container)
- 🔴 Redis Cache (Docker Container)
- 🔌 WordPress Plugin für Custom Post Types

## 📋 **Setup Schritte**

### **1. CyberPanel MySQL Datenbank vorbereiten**

**In CyberPanel:**
1. Databases → Create Database
2. Database Name: `veri_veriaguide_db`
3. Database User: `wp_user`
4. Password: `***REMOVED***` (oder dein gewünschtes Passwort)

**Oder falls bereits vorhanden, Credentials notieren für .env.production.docker**

### **2. Environment konfigurieren**

Bearbeite `.env.production.docker`:
```bash
# MySQL Credentials (deine CyberPanel Datenbank)
MYSQL_DATABASE=veri_veriaguide_db
MYSQL_USER=wp_user
MYSQL_PASSWORD=***REMOVED***

# API Keys (WICHTIG: Echte Werte eintragen!)
GOOGLE_MAPS_API_KEY=dein_echter_google_maps_api_key
SECRET_KEY=ein_sehr_sicherer_geheimer_schluessel
```

### **3. Container starten**

```bash
# Alle Container starten (WordPress + Frontend + Redis)
./start-production-docker.sh

# Status prüfen
docker compose -f docker-compose.production.external-db.yml ps
```

### **4. WordPress Setup**

Nach dem ersten Start:
1. Gehe zu: http://veriaguide.gr:8086
2. WordPress Installation durchlaufen
3. Admin-Account erstellen
4. Plugin wird automatisch verfügbar sein
5. Plugins → Aktiviere "VeriaGuide Custom Post Types"
6. Settings → Permalinks → "Post name" → Save Changes

### **4. OpenLiteSpeed Virtual Host konfigurieren**

**Option A: CyberPanel (empfohlen)**
1. CyberPanel → Websites → veriaguide.gr
2. Manage → Rewrite Rules
3. Füge hinzu:
```apache
# Frontend Proxy
RewriteRule ^app/(.*)$ http://127.0.0.1:8000/$1 [P,L]
RewriteRule ^api/(.*)$ http://127.0.0.1:8000/$1 [P,L]

# WordPress (Standard)
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
```

**Option B: Manuell**
```bash
# Virtual Host Konfiguration bearbeiten
sudo nano /usr/local/lsws/conf/vhosts/veriaguide.gr/vhconf.conf

# Proxy Context hinzufügen:
context /app/ {
  type                    proxy
  uri                     http://127.0.0.1:8000/
  extraHeaders            Host $host
}
```

### **5. Nginx Reverse Proxy (Alternative)**

Falls du Nginx vor OpenLiteSpeed verwendest:
```nginx
server {
    listen 80;
    server_name veriaguide.gr www.veriaguide.gr;

    # Frontend App
    location /app/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WordPress (OpenLiteSpeed)
    location / {
        proxy_pass http://127.0.0.1:8088;  # OpenLiteSpeed Port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🧪 **Testing**

### **1. WordPress REST API**
```bash
curl http://veriaguide.gr/wp-json/wp/v2/religious_sites
```

### **2. Frontend**
```bash
curl http://localhost:8000
# oder über Proxy:
curl http://veriaguide.gr/app/
```

### **3. Container Status**
```bash
docker compose -f docker-compose.production.external-db.yml ps
docker compose -f docker-compose.production.external-db.yml logs frontend
```

## 📁 **Datei-Struktur**

```
$WP_DOCUMENT_ROOT/
├── docker-compose.production.external-db.yml  # Nur Frontend + Redis
├── .env.production.docker                     # Environment Variables
├── start-production-docker.sh                 # Startup Script
├── veriaguide-cpt.php                        # WordPress Plugin
└── frontend/                                  # FastAPI Code
    ├── Dockerfile.production
    ├── main.py
    └── ...
```

## 🔧 **Troubleshooting**

### **WordPress Plugin nicht sichtbar**
```bash
# Berechtigungen prüfen
sudo chown -R www-data:www-data /usr/local/lsws/Example/html/wp-content/plugins/
sudo chmod 644 /usr/local/lsws/Example/html/wp-content/plugins/veriaguide-cpt.php
```

### **REST API 404 Fehler**
1. WordPress Admin → Settings → Permalinks → Save Changes
2. OpenLiteSpeed Rewrite Rules prüfen

### **Frontend nicht erreichbar**
```bash
# Container Logs prüfen
docker compose -f docker-compose.production.external-db.yml logs frontend

# Port prüfen
sudo netstat -tlnp | grep :8000
```

## 🚀 **Go Live Checklist**

- [ ] WordPress Plugin aktiviert
- [ ] Permalinks auf "Post name" gesetzt
- [ ] .env.production.docker konfiguriert
- [ ] Google Maps API Key eingetragen
- [ ] SECRET_KEY geändert
- [ ] Frontend Container läuft
- [ ] REST API funktioniert
- [ ] Proxy/Rewrite Rules konfiguriert
- [ ] SSL Zertifikat installiert

## 📞 **Support**

Bei Problemen:
1. **Container Logs**: `docker compose -f docker-compose.production.external-db.yml logs -f`
2. **OpenLiteSpeed Logs**: `/usr/local/lsws/logs/error.log`
3. **WordPress Logs**: `wp-content/debug.log` (falls aktiviert)