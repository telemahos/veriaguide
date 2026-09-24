# SEO-Bericht veriaguide.gr

Live-Crawl am 24. September 2026. Geprüft: Startseite, Kategorie-Hubs, `robots.txt`, `sitemap.xml` und eine Detail-URL. Quelle: öffentliche HTML-Antworten von https://veriaguide.gr.

**Gesamtnote: 38 / 100**

| Kennzahl | Wert |
| --- | --- |
| URLs in der Sitemap | 7 |
| Kirchen live auf `/religious-sites` | 0 |
| H1 auf der Startseite | 1 |

## Bewertung nach Bereich

| Bereich | Score (0–100) |
| --- | --- |
| Technik | 72 |
| Metadaten | 70 |
| Strukturierte Daten | 58 |
| Sitemap | 22 |
| Indexierbarer Inhalt | 15 |

## Der Guide ist für Google leer

Die Kategorie-Seiten antworten mit HTTP 200, zeigen aber keine Einträge. Auf `/religious-sites` steht wörtlich „0 Byzantine churches“ und „No religious sites found“. Die Autocomplete-APIs für Kirchen, Museen und Ausgrabungen liefern leere Listen. Eine bekannte Kirchen-URL antwortet mit 404. Google kann den eigentlichen Reiseführer deshalb nicht indexieren.

## Was bereits stimmt

HTTPS mit HSTS, `www` leitet auf `veriaguide.gr` um, Canonical und Open Graph plus Twitter Cards sind auf der Startseite gesetzt. Jede geprüfte Seite hat genau eine H1. Title und Description der Startseite sowie der drei Kultur-Hubs (Kirchen, Museen, Archäologie) sind geo-spezifisch und in sinnvoller Länge. `robots.txt` existiert und verweist auf die Sitemap. JSON-LD auf der Startseite enthält WebSite und Organization.

## Seiten-Check

Zeichenzahlen aus dem gerenderten HTML. Zielbereich Description: etwa 140–160 Zeichen.

| URL | Title | Description | Befund |
| --- | --- | --- | --- |
| `/` | 60 Zeichen | 155 Zeichen | Gut: Ort, Vergina, Apostel Paulus |
| `/religious-sites` | 62 Zeichen | 150 Zeichen | Meta gut, Inhalt leer (0 Einträge) |
| `/museums` | 32 Zeichen | 165 Zeichen | Meta gut, Katalog leer |
| `/archaeological-sites` | 46 Zeichen | 154 Zeichen | Meta gut, Katalog leer |
| `/about` | 24 Zeichen | 159 Zeichen | Ausreichend |
| `/contact` | 21 Zeichen | 37 Zeichen | Description zu kurz |
| `/map` | 34 Zeichen | 77 Zeichen | Description knapp |
| `/restaurants` | 38 Zeichen | 65 Zeichen | Generisch, wenig Unique Content |
| `/cafes` | 32 Zeichen | 59 Zeichen | Generisch |
| `/accommodations` | 42 Zeichen | 68 Zeichen | Generisch |

## Sitemap

`sitemap.xml` enthält nur Startseite, Kontakt, About, Karte und die drei Kultur-Kategorien. Keine Detailseiten, keine Restaurants, Cafés oder Unterkünfte. Der Code würde Inhalte aus WordPress aufnehmen — live kommen keine Posts zurück, deshalb bleiben nur die statischen URLs.

## Strukturierte Daten

Die Startseite hat ein Schema-Graph mit WebSite und Organization. Die SearchAction zeigt auf `/search`, diese URL ist in `robots.txt` aber mit Disallow gesperrt. Detailseiten liefern im Crawl kein JSON-LD, weil die Inhalte nicht ausgeliefert werden.

## Prioritäten

### Sofort

1. WordPress-Anbindung auf dem Live-Server prüfen. Die Autocomplete-APIs und die Listen sind leer, obwohl ein internes Audit vom 3. Juli 2026 noch 65 Kirchen mit durchschnittlich 3.300 Zeichen Text gesehen hat (`data/religious_sites_seo_audit.md`).
2. Sobald Einträge wieder da sind: Sitemap neu erzeugen und in der Google Search Console einreichen. Ohne Detail-URLs rankt der Guide nicht für einzelne Kirchen, Museen oder Vergina.
3. SearchAction im JSON-LD entweder entfernen oder `/search` für Google freigeben. Ein gesperrtes Suchziel in den strukturierten Daten ist ein Widerspruch.

### Danach

Descriptions von Kontakt, Karte, Restaurants, Cafés, Unterkünften und Ski-Resorts auf 140–160 Zeichen mit Ortsbezug verlängern. Eine griechische Sprachversion fehlt komplett (`html lang` ist nur `en`) — für lokale Suche in Griechenland ein klarer Nachteil. Der Footer zeigt noch 2025.

Interne Verlinkung entsteht erst, wenn Karten und Detailseiten serverseitig im HTML stehen. Reine JavaScript-Listen sieht Google nicht als echte Links.

## Abgrenzung

Keine Search-Console-Daten, keine Backlink-Analyse und kein Core-Web-Vitals-Lab. Die Note beschreibt Indexierbarkeit und On-Page-Signale der öffentlichen Seiten, nicht das Ranking in Google.
