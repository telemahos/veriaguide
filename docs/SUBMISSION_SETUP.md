# Setup-Anleitung: User Submissions

## Schnellstart

### 1. API-Key konfigurieren

Fügen Sie einen sicheren API-Key zu Ihrer `.env` Datei hinzu:

```bash
# .env
ADMIN_API_KEY=ihr-sicherer-api-key-hier-mindestens-32-zeichen
```

Generieren Sie einen sicheren Key mit:

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Submissions-Verzeichnis erstellen

```bash
mkdir -p data/submissions
chmod 755 data/submissions
```

### 3. Server neu starten

```bash
# Docker
docker-compose restart frontend

# Lokal
uvicorn main:app --reload
```

## Verwendung

### Für Benutzer

1. Öffnen Sie: `http://localhost:8000/submit`
2. Füllen Sie das Formular aus
3. Laden Sie Fotos hoch
4. Senden Sie ab

### Für Administratoren

1. Öffnen Sie: `http://localhost:8000/admin/submissions/dashboard`
2. Geben Sie Ihren API-Key ein (aus `.env`)
3. Überprüfen Sie Einreichungen
4. Genehmigen oder lehnen Sie ab

## API-Endpoints testen

```bash
# Liste aller Submissions abrufen
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/admin/submissions

# Submission genehmigen
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "admin_notes=Looks good!" \
  http://localhost:8000/admin/submissions/{submission_id}/approve

# Submission ablehnen
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "admin_notes=Incomplete information" \
  http://localhost:8000/admin/submissions/{submission_id}/reject
```

## Sicherheitshinweise

1. **API-Key geheim halten**: Niemals in Git committen
2. **HTTPS verwenden**: In Produktion nur über HTTPS
3. **Regelmäßig prüfen**: Submissions zeitnah bearbeiten
4. **Backups**: `data/submissions/` regelmäßig sichern

## Produktions-Deployment

### Nginx-Konfiguration

```nginx
# Größere Upload-Limits für Bilder
client_max_body_size 50M;

# Admin-Endpoints schützen
location /admin/ {
    # Optional: IP-Whitelist
    allow 192.168.1.0/24;
    deny all;
    
    proxy_pass http://localhost:8000;
}
```

### Umgebungsvariablen (Produktion)

```bash
# .env.production
ADMIN_API_KEY=sehr-langer-und-sicherer-produktions-key
ENVIRONMENT=production
```

## Monitoring

Überwachen Sie die Logs:

```bash
# Submissions-bezogene Logs
tail -f frontend/logs/veriaguide.log | grep -i submission

# Fehler
tail -f frontend/logs/veriaguide_errors.log
```

## Wartung

### Alte Submissions archivieren

```bash
# Genehmigte/Abgelehnte Submissions verschieben
mkdir -p data/submissions/archive
mv data/submissions/*.json data/submissions/archive/
```

### Speicherplatz überwachen

```bash
# Größe des Submissions-Verzeichnisses
du -sh data/submissions/
```

## Fehlerbehebung

### Problem: "API-Key nicht konfiguriert"

```bash
# Prüfen Sie die .env Datei
cat .env | grep ADMIN_API_KEY

# Stellen Sie sicher, dass die Variable geladen wird
docker-compose config | grep ADMIN_API_KEY
```

### Problem: "Permission denied" beim Speichern

```bash
# Berechtigungen korrigieren
chmod -R 755 data/submissions/
chown -R $USER:$USER data/submissions/
```

### Problem: Bilder zu groß

Passen Sie die Limits in `submission_service.py` an:

```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB statt 5MB
```

## Integration mit WordPress

Nach Genehmigung einer Submission können Sie die Daten manuell in WordPress übertragen:

1. Öffnen Sie WordPress Admin
2. Erstellen Sie einen neuen Post des entsprechenden Post-Types
3. Kopieren Sie die Daten aus der JSON-Datei
4. Laden Sie die Bilder hoch (dekodieren Sie Base64 falls nötig)
5. Veröffentlichen Sie den Eintrag

### Automatisierung (zukünftig)

Ein Python-Script könnte dies automatisieren:

```python
# Beispiel: auto_import.py
import json
import requests
from pathlib import Path

def import_to_wordpress(submission_id):
    # Submission laden
    with open(f'data/submissions/{submission_id}.json') as f:
        data = json.load(f)
    
    # WordPress REST API verwenden
    wp_api = "http://localhost:8086/wp-json/wp/v2/"
    
    # Post erstellen
    # Bilder hochladen
    # ACF-Felder setzen
    # ...
```

## Support

Bei Fragen oder Problemen:
- Dokumentation: `docs/USER_SUBMISSIONS.md`
- Kontakt: info@veriaguide.com
