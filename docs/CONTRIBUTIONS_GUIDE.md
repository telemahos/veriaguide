# User Contributions Guide

## Übersicht

Die Contributions-Funktion ermöglicht es Benutzern, Inhalte (Fotos, Videos, Beschreibungen) zu bestehenden Listings hinzuzufügen. Dies fördert Community-Engagement und hält die Inhalte aktuell.

## Features

### Für Benutzer

**Seite**: `/contribute`

**Funktionen**:
- Suche nach existierenden Listings mit Autocomplete
- Auswahl des Contribution-Typs:
  - 📸 Fotos (max. 10, je 5MB)
  - 🎥 Videos (max. 3, je 50MB)
  - 📝 Beschreibung/Bewertung (max. 1000 Zeichen)
- Mehrsprachige Oberfläche (Griechisch, Englisch, Deutsch)
- Live-Vorschau von hochgeladenen Medien

**Unterstützte Formate**:
- Bilder: JPG, JPEG, PNG, WEBP
- Videos: MP4, WEBM, OGG

### Für Administratoren

**API-Endpoints**:
- `GET /admin/contributions` - Liste aller ausstehenden Contributions
- `POST /admin/contributions/{id}/approve` - Contribution genehmigen
- `POST /admin/contributions/{id}/reject` - Contribution ablehnen

## Workflow

### Benutzer-Workflow

1. Benutzer öffnet `/contribute`
2. Sucht nach einem Listing (z.B. "Restaurant Akropolis")
3. Wählt das gewünschte Listing aus der Autocomplete-Liste
4. Wählt Contribution-Typ(en):
   - Fotos hochladen
   - Videos hochladen
   - Beschreibung/Bewertung schreiben
5. Gibt Email-Adresse an (optional: Name)
6. Akzeptiert Nutzungsbedingungen
7. Sendet Contribution ab
8. Erhält Bestätigung mit Referenznummer

### Admin-Workflow

1. Admin ruft Contributions-Liste ab:
   ```bash
   curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/admin/contributions
   ```

2. Prüft Inhalte:
   - Fotos auf Qualität und Relevanz
   - Videos auf Inhalt und Größe
   - Beschreibungen auf Angemessenheit

3. Genehmigt oder lehnt ab:
   ```bash
   # Genehmigen
   curl -X POST -H "X-API-Key: YOUR_KEY" \
     -F "admin_notes=Good quality photos" \
     http://localhost:8000/admin/contributions/{id}/approve
   
   # Ablehnen
   curl -X POST -H "X-API-Key: YOUR_KEY" \
     -F "admin_notes=Inappropriate content" \
     http://localhost:8000/admin/contributions/{id}/reject
   ```

4. Bei Genehmigung: Inhalte manuell zum WordPress-Listing hinzufügen

## Sicherheit

### Validierung

1. **Datei-Upload**:
   - Format-Prüfung (Whitelist)
   - Größen-Limits
   - Anzahl-Limits

2. **Eingabe-Validierung**:
   - Email-Format
   - Text-Länge
   - HTML-Sanitization

3. **Rate Limiting**:
   - Middleware begrenzt Anfragen
   - Schutz vor Spam

### Datenspeicherung

```
data/contributions/
├── {uuid-1}.json
├── {uuid-2}.json
└── .gitignore
```

**JSON-Format**:
```json
{
  "id": "uuid",
  "status": "pending",
  "submitted_at": "2026-02-15T23:00:00",
  "listing_info": {
    "listing_id": "123",
    "category": "restaurant"
  },
  "contributor": {
    "email": "user@example.com",
    "name": "John Doe"
  },
  "contribution_types": ["photos", "description"],
  "content": {
    "description": "Great food and service!",
    "photos": [
      {
        "filename": "photo.jpg",
        "content_type": "image/jpeg",
        "size": 123456,
        "data": "base64..."
      }
    ],
    "videos": []
  },
  "admin_notes": ""
}
```

## Integration mit WordPress

Nach Genehmigung einer Contribution:

1. **Fotos hinzufügen**:
   - Base64-Daten dekodieren
   - In WordPress Media Library hochladen
   - Zum Listing hinzufügen

2. **Videos hinzufügen**:
   - Video-Hosting-Service verwenden (z.B. YouTube, Vimeo)
   - Oder direkt in WordPress hochladen
   - Embed-Code zum Listing hinzufügen

3. **Beschreibungen hinzufügen**:
   - Als Kommentar/Review speichern
   - Oder in ACF-Feld "User Reviews" einfügen

## Mehrsprachigkeit

Die Seite unterstützt drei Sprachen:

- **Griechisch (Standard)**: Primäre Sprache für lokale Benutzer
- **Englisch**: Für internationale Touristen
- **Deutsch**: Für deutschsprachige Besucher

Sprachauswahl wird in localStorage gespeichert.

## API-Beispiele

### Contributions abrufen

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/admin/contributions
```

**Response**:
```json
{
  "success": true,
  "contributions": [...],
  "count": 5
}
```

### Contribution genehmigen

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "admin_notes=Excellent photos" \
  http://localhost:8000/admin/contributions/abc-123/approve
```

### Contribution ablehnen

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "admin_notes=Low quality images" \
  http://localhost:8000/admin/contributions/abc-123/reject
```

## Unterschiede: Submissions vs. Contributions

| Feature | Submissions | Contributions |
|---------|-------------|---------------|
| Zweck | Neue Listings erstellen | Inhalte zu existierenden Listings hinzufügen |
| Route | `/submit` | `/contribute` |
| Erforderlich | Vollständige Geschäftsinformationen | Nur Medien/Beschreibung |
| Listing-Auswahl | Nicht erforderlich | Erforderlich (via Suche) |
| GPS-Koordinaten | Nicht erforderlich | Nicht erforderlich |
| Öffnungszeiten | Erforderlich | Nicht erforderlich |

## Zukünftige Erweiterungen

- **Automatische Moderation**: KI-basierte Inhaltsfilterung
- **Email-Benachrichtigungen**: Status-Updates an Contributor
- **Öffentliches Profil**: Contributor können ihre Beiträge sehen
- **Gamification**: Punkte/Badges für aktive Contributors
- **Direkter WordPress-Import**: Automatische Integration genehmigter Inhalte
- **Bildoptimierung**: Automatische Kompression und Größenanpassung
- **Video-Transcoding**: Konvertierung in optimale Formate

## Fehlerbehebung

### Problem: Suche findet keine Ergebnisse

- Prüfen Sie, ob der globale Autocomplete-Endpoint funktioniert:
  ```bash
  curl "http://localhost:8000/api/search/autocomplete?q=restaurant"
  ```
- Stellen Sie sicher, dass Listings im Cache sind

### Problem: Upload schlägt fehl

- Überprüfen Sie Dateigrößen (Fotos: 5MB, Videos: 50MB)
- Prüfen Sie Dateiformate
- Überprüfen Sie Server-Logs: `frontend/logs/veriaguide.log`

### Problem: Contributions werden nicht gespeichert

- Prüfen Sie Verzeichnis-Berechtigungen:
  ```bash
  chmod -R 755 data/contributions/
  ```
- Überprüfen Sie Speicherplatz

## Support

Bei Fragen oder Problemen:
- Dokumentation: `docs/USER_SUBMISSIONS.md`
- Kontakt: info@veriaguide.com
