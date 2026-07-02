# Religious Sites – SEO-Checkliste (WordPress Redaktion)

> Stand: 03.07.2026 · VeriaGuide Frontend ergänzt Meta-Tags & Schema automatisch.  
> **Diese Checkliste betrifft Inhalte in WordPress** (`wp-admin` → Religious Sites).

---

## Ziel-Keywords (aus Google-Daten)

| Keyword | Suchvolumen/Monat | Verwendung |
|---------|-------------------|------------|
| veria | 50.000 | Titel, Excerpt, erster Absatz |
| veroia | 5.000 | Alternative Schreibweise im Text |
| veria imathia greece | 5.000 | Excerpt, Adresse, Schlussabsatz |
| byzantine church / churches | – | Kategorie, Fließtext |
| apostle paul / vema | – | Wo historisch passend (Veria-Kontext!) |

**Nicht verwenden:** generische „Saint Paul“-Keywords ohne Veria-Bezug (falsches Suchintent).

---

## Pro Kirche abhaken

### 1. Titel (SEO Title)

- [ ] Format: **`{Kirchenname}: {Kurzbeschreibung} in Veria, Greece`**
- [ ] Enthält mindestens eines: `Veria`, `Veroia`, `Imathia`, `Greece`, `Byzantine`
- [ ] Länge: **50–70 Zeichen** für den Hauptteil (Frontend hängt `| VeriaGuide` an)
- [ ] Doppelpunkt `:` trennt Kurztitel und Untertitel (wird auf der Seite schön umgebrochen)

**Beispiel (gut):**  
`Holy Church of Saint Nicholas: A 15th-Century Shrine in Veria, Greece`

**Vermeiden:** Titel ohne Ortsbezug, z. B. nur `Holy Church of Saint Timothy`

---

### 2. Excerpt (SEO-Beschreibung) — **wichtig!**

WordPress erzeugt sonst automatisch einen abgeschnittenen Text mit `…` — das ist **schlecht für SEO**.

- [ ] **Eigenes Excerpt schreiben** (Feld „Excerpt“ / „Auszug“ in WP, nicht nur Inhalt kopieren)
- [ ] Länge: **120–160 Zeichen** (max. ~2 Sätze)
- [ ] Enthält: Kirchenname + `Veria` oder `Veroia` + `Imathia` + `Greece`
- [ ] Call-to-action optional: *Visit*, *Discover*, *Explore*
- [ ] Kein `…` am Ende

**Beispiel:**  
`Visit the Holy Church of Saint Nicholas in Veria (Veroia), Imathia — a 15th-century Byzantine church with frescoes and visiting hours for travellers.`

---

### 3. Hauptinhalt (Content)

- [ ] Mindestens **500 Wörter** (aktueller Durchschnitt: ~3.300 Zeichen ≈ gut)
- [ ] Erster Absatz: Was ist es? Wo in Veria? Warum besuchen?
- [ ] Zwischenüberschriften (H2/H3) mit Keywords: *History*, *Architecture*, *Visiting Veria*, *How to get there*
- [ ] Natürliche Variation: Veria, Veroia, Imathia, Central Macedonia, Greece
- [ ] Keine leeren Beiträge veröffentlichen (nur Titel = schlechtestes SEO)

---

### 4. Interne Links

- [ ] Link zur **Übersichtsseite:** `/religious_sites` (Text z. B. *more Byzantine churches in Veria*)
- [ ] 1–2 Links zu **verwandten Kirchen** auf VeriaGuide (echte URLs, kein `#`)
- [ ] Optional: Link zu `/museums`, `/archaeological_sites`, `/map`
- [ ] **Keine kaputten Links:** keine `href="#"`, keine `artifacts.grokusercontent.com`

**Interne Link-Vorlage:**  
`https://veriaguide.gr/religious_sites/{slug}`

---

### 5. ACF-Felder (Technik + Local SEO)

- [ ] **Featured Image** gesetzt (echtes Foto, kein Platzhalter)
- [ ] **Location Map** mit Lat/Lng und Adresse (`Ierarchon, Veria, Greece` o. ä.)
- [ ] **Opening Hours** / Visiting Hours ausgefüllt
- [ ] **Site Type** Tag gesetzt (Church, Monastery, Chapel …)
- [ ] **Religious Affiliation** wenn bekannt (Greek Orthodox …)

---

### 6. Bilder

- [ ] Alt-Text in WP-Mediathek: `{Kirchenname} – Byzantine church in Veria, Greece`
- [ ] Dateiname sinnvoll: `saint-nicholas-veria-exterior.jpg`

---

## Was das Frontend automatisch macht (nicht doppelt pflegen)

| Element | Automatisch |
|---------|-------------|
| Meta Description | aus Excerpt, ggf. mit Veria/Imathia ergänzt |
| Meta Title | mit `Veria, Greece` wenn im Titel fehlt |
| Church Schema (JSON-LD) | ja |
| Breadcrumbs | ja |
| Listing-Card Excerpt | Fallback wenn Excerpt leer |
| SEO-Intro auf Detailseite | nur wenn **kein** ausreichender Artikeltext |

---

## Priorität bei Überarbeitung

1. **Kritisch** – leerer Inhalt + leeres Excerpt (sofort befüllen)
2. **Schwach** – sehr kurzer Text (< 200 Zeichen)
3. **Links** – Grok-/Platzhalter-Links entfernen (27+ Beiträge betroffen)
4. **Excerpt** – eigenen Text statt WP-Auto-Auszug (62/65 nutzen noch Auto-`…`)
5. **Titel kürzen** – 31 Titel > 75 Zeichen (optional optimieren)

---

## Nach dem Speichern in WordPress

```bash
# Auf dem VPS – Cache leeren
ssh vps "docker exec veriaguide_redis redis-cli FLUSHALL && docker restart veriaguide_frontend"
```

Oder warten (~30–60 Min. Redis-TTL).

---

## Audit erneut ausführen

```bash
python3 utility_scripts/audit_religious_sites_seo.py
```

Ergebnis: `data/religious_sites_seo_audit.json` + `data/religious_sites_seo_audit.md`
