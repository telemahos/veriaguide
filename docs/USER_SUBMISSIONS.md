# User Submissions Feature

## Übersicht

Die User-Submission-Funktion ermöglicht es Geschäftsinhabern, ihre Unternehmen selbst bei VeriaGuide einzutragen. Alle Einreichungen werden manuell geprüft, bevor sie veröffentlicht werden.

## Funktionen

### Für Benutzer

- **Formular**: `/submit` - Geschäftsinformationen einreichen
- **Kategorien**: Restaurant, Café, Unterkunft, Museum, Tour, Geschäft, Dienstleistung
- **Erforderliche Felder**:
  - Geschäftsname
  - Kategorie
  - Beschreibung (min. 50 Zeichen)
  - Stadt und Adresse
  - E-Mail und Telefon
  - Öffnungszeiten
  - Mindestens 1 Foto (max. 10 Fotos)
- **Optionale Felder**:
  - Website
  - GPS-Koordinaten (Breitengrad/Längengrad)

### Für Administratoren

- **Dashboard**: `/admin/submissions/dashboard` - Übersicht aller Einreichungen
- **API-Endpoints**:
  - `GET /admin/submissions` - Liste aller ausstehenden Einreichungen
  - `POST /admin/submissions/{id}/approve` - Einreichung genehmigen
  - `POST /admin/submissions/{id}/reject` - Einreichung ablehnen

## Sicherheitsmechanismen

### Validierung

1. **Eingabevalidierung**:
   - Alle Felder werden auf Länge und Format geprüft
   - HTML-Sanitization gegen XSS-Angriffe
   - E-Mail- und URL-Format-Validierung
   - GPS-Koordinaten-Bereichsprüfung

2. **Datei-Upload-Sicherheit**:
   - Erlaubte Formate: JPG, JPEG, PNG, WEBP
   - Maximale Dateigröße: 5MB pro Bild
   - Maximale Anzahl: 10 Bilder
   - Dateiformat-Validierung

3. **Rate Limiting**:
   - Middleware begrenzt Anfragen auf 100 pro Minute
   - Schutz vor Spam und Missbrauch

4. **Admin-Zugriff**:
   - API-Key-Authentifizierung erforderlich
   - Constant-time Vergleich gegen Timing-Angriffe
   - Logging aller Admin-Aktionen

### Datenspeicherung

- Submissions werden als JSON-Dateien in `data/submissions/` gespeichert
- Bilder werden als Base64 kodiert gespeichert
- Status: `pending`, `approved`, `rejected`
- Jede Submission erhält eine eindeutige UUID

## Workflow

### Benutzer-Workflow

1. Benutzer öffnet `/submit`
2. Füllt das Formular aus
3. Lädt Fotos hoch (Client-seitige Vorschau)
4. Akzeptiert Datenschutzerklärung und Bedingungen
5. Sendet Formular ab
6. Erhält Bestätigung mit Referenznummer

### Admin-Workflow

1. Admin öffnet `/admin/submissions/dashboard`
2. Gibt API-Key ein
3. Sieht Liste aller ausstehenden Einreichungen
4. Klickt auf "Details" für vollständige Ansicht
5. Prüft alle Informationen und Fotos
6. Genehmigt oder lehnt Einreichung ab (mit Notizen)
7. System aktualisiert Status

## API-Authentifizierung

Alle Admin-Endpoints erfordern einen API-Key im Header:

```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/admin/submissions
```

Der API-Key wird in der Umgebungsvariable `ADMIN_API_KEY` konfiguriert.

## Konfiguration

### Umgebungsvariablen

```bash
# .env
ADMIN_API_KEY=your-secure-api-key-here
```

### Verzeichnisstruktur

```
data/
└── submissions/
    ├── {uuid-1}.json
    ├── {uuid-2}.json
    └── ...
```

### Submission JSON-Format

```json
{
  "id": "uuid",
  "status": "pending",
  "submitted_at": "2026-02-15T10:30:00",
  "business_info": {
    "name": "Restaurant Name",
    "category": "restaurant",
    "description": "...",
    "city": "Veria",
    "address": "...",
    "phone": "+30...",
    "email": "...",
    "website": "...",
    "opening_hours": "..."
  },
  "location": {
    "latitude": 40.5246,
    "longitude": 22.2022
  },
  "images": [
    {
      "filename": "image.jpg",
      "content_type": "image/jpeg",
      "size": 123456,
      "data": "base64..."
    }
  ],
  "admin_notes": ""
}
```

## Nächste Schritte

Nach Genehmigung einer Submission sollte der Admin:

1. Die Daten in WordPress als neuen Post-Type-Eintrag erstellen
2. Die Bilder in WordPress hochladen
3. Alle ACF-Felder ausfüllen
4. Den Eintrag veröffentlichen
5. Optional: Dem Geschäftsinhaber eine Bestätigungs-E-Mail senden

## Zukünftige Erweiterungen

- Automatische E-Mail-Benachrichtigungen bei Status-Änderungen
- Direkter Import in WordPress via REST API
- Benutzer-Dashboard zum Verfolgen eigener Submissions
- Bulk-Aktionen für Admins (mehrere Submissions gleichzeitig genehmigen)
- Bildoptimierung und automatische Größenanpassung
- Duplicate-Detection basierend auf Name/Adresse

## Fehlerbehebung

### Submission schlägt fehl

- Prüfen Sie die Browser-Konsole auf JavaScript-Fehler
- Überprüfen Sie die Dateigröße der Bilder (max. 5MB)
- Stellen Sie sicher, dass alle Pflichtfelder ausgefüllt sind
- Prüfen Sie die Server-Logs: `frontend/logs/veriaguide.log`

### Admin kann Submissions nicht sehen

- Überprüfen Sie, ob der API-Key korrekt ist
- Prüfen Sie die Umgebungsvariable `ADMIN_API_KEY`
- Überprüfen Sie die Berechtigungen des `data/submissions/` Verzeichnisses
- Prüfen Sie die Server-Logs auf Authentifizierungsfehler

### Bilder werden nicht angezeigt

- Überprüfen Sie das Bildformat (nur JPG, PNG, WEBP erlaubt)
- Prüfen Sie die Base64-Kodierung in der JSON-Datei
- Stellen Sie sicher, dass der Browser Base64-Bilder unterstützt

## Support

Bei Problemen oder Fragen:
- E-Mail: info@veriaguide.com
- Kontaktformular: `/contact`
