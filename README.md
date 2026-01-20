- docker-compose down && docker-compose up --build
- docker compose -f docker-compose.prod.yml up --build -d
- Bei Google Maps und ACF musst du im theme/
- LIVE: 
    - docker compose -f /home/veriaguide.gr/public_html/docker-compose.production.yml build
    - *** Build the Frontend ***
        - sudo docker compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml up --build -d frontend
    - sudo docker compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml restart frontend
    - Free Redis Cache:
        - sudo docker compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml exec redis redis-cli FLUSHALL
        - docker compose  exec redis redis-cli FLUSHALL
        - docker exec veriaguide_frontend_prod env | grep ADMIN
        - docker exec veriaguide_redis_prod redis-cli FLUSHALL

    
# WP Update on Live VPS Server - on Docker Container
--------------------------------------------------------
# WordPress Core aktualisieren
sh utility_scripts/update-wordpress-via-host.sh

# Plugins aktualisieren
sh utility_scripts/update-wordpress-plugins.sh

# Themes aktualisieren
sh utility_scripts/update-wordpress-themes.sh
--------------------------------------------------------


    
functions.php das einstellen:
'''
// Add Google Maps API key for ACF Free
function my_acf_google_map_api($api) {
    $api['key'] = 'AIzaSyBdrHX7o7PWWawwvuIPGENMjo346F9OH-0'; // Dein Google Maps API-Schlüssel
    return $api;
}
add_filter('acf/fields/google_map/api', 'my_acf_google_map_api');
'''

Suggestions
- Add async WordPress API client to prevent blocking
- Implement Redis caching for WordPress API responses
Extract route logic into service classes
- Add environment-specific configs (dev/staging/prod)
- Consider adding API rate limiting and error handling middleware

# Import accomodasions on localhost
- docker cp data/hotels_in_veria.csv wp_veriaguide:/var/www/html/data/
- docker-compose exec wordpress mkdir -p /var/www/html/data
- docker cp data/hotels_in_veria.csv wp_veriaguide:/var/www/html/data/
- docker cp import_accommodations.php wp_veriaguide:/var/www/html/
- docker cp veriaguide-cpt.php wp_veriaguide:/var/www/html/wp-content/plugins/
- docker cp data/acf-export-2025-09-11.json  wp_veriaguide:/var/www/html/ 
- docker cp import_acf_fields.php wp_veriaguide:/var/www/html/
- docker-compose exec wordpress php /var/www/html/import_acf_fields.php
- docker-compose exec wordpress php /var/www/html/import_accommodations.php
- curl -s "http://localhost:8086/wp-json/wp/v2/accommodations" | head -10


# Import accomodasions in PRODUCTION:
   * Ihr lokaler Befehl:
      docker-compose exec wordpress php /var/www/html/import_acf_fields.php
   * Ihr Produktions-Befehl:
      docker compose -f docker-compose.prod.yml exec wordpress php /var/www/html/import_acf_fields.php

   * Ihr lokaler Befehl:
      docker-compose exec wordpress php /var/www/html/import_accommodations.php
   * Ihr Produktions-Befehl:
      docker compose -f docker-compose.prod.yml exec wordpress php /var/www/html/import_accommodations.php



ODER:

### Anleitung: Import von Unterkünften (Accommodations)

Diese Anleitung beschreibt den korrekten Prozess, um Unterkunftsdaten aus der CSV-Datei zu importieren. Der kritischste Teil ist die korrekte Synchronisierung der ACF-Felddefinitionen VOR dem eigentlichen Datenimport, um Fehler zu vermeiden.

**Voraussetzung:** Die Docker-Container laufen (`docker-compose up -d`).

**Schritt 1: Datenbank vorbereiten**

Stellen Sie sicher, dass Sie mit einem sauberen Zustand starten. Wenn Sie den Import wiederholen, löschen Sie am besten vorher alle bestehenden "Accommodation"-Beiträge über das WordPress-Admin-Panel.

**Schritt 2: ACF Custom Fields synchronisieren (Wichtigster Schritt!)**

Wir verwenden die empfohlene Methode von ACF, um die Feldgruppen über eine `*.json`-Datei im Theme-Ordner zu synchronisieren. Dies ist der robusteste Weg.

1.  **`acf-json`-Verzeichnis im Theme erstellen und die aktuelle JSON-Definition dorthin kopieren.**
    *Hinweis: Der Befehl geht vom Theme `twentytwentyfour` aus. Passen Sie den Namen an, falls Sie ein anderes Theme verwenden.*

    ```bash
    docker-compose exec wordpress bash -c "mkdir -p /var/www/html/wp-content/themes/twentytwentyfour/acf-json && cp /var/www/html/data/acf-export-2025-09-11.json /var/www/html/wp-content/themes/twentytwentyfour/acf-json/group_681bc0a358918.json"
    ```

2.  **Im WordPress-Admin-Panel synchronisieren:**
    - Gehen Sie zu `Benutzerdefinierte Felder` -> `Feldgruppen`.
    - Oben sollte eine Benachrichtigung `Synchronisierung verfügbar` erscheinen.
    - Klicken Sie auf den Button `Änderungen synchronisieren`.


# Re-import All Data after DB Restore

## Cafes
docker exec -u www-data wp_veriaguide php /var/www/html/data/cafe_veria/import_acf_fields_cafes.php
docker exec -u www-data wp_veriaguide php /var/www/html/data/cafe_veria/import_cafes.php

## Restaurants
docker exec -u www-data wp_veriaguide php /var/www/html/data/restaurants_veria/import_acf_fields_restaurants.php
docker exec -u www-data wp_veriaguide php /var/www/html/data/restaurants_veria/import_restaurants.php


# VPS SERVER EINFUEGEN:
  1. Hotels (Unterkünfte)

   1 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/hotels_veria/import_acf_fields.php
   2 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/hotels_veria/import_accommodations.php

  2. Cafés

   1 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/cafe_veria/import_acf_fields_cafes.php
   2 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/cafe_veria/import_cafes.php

  3. Restaurants

   1 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/restaurants_veria/import_acf_fields_restaurants.php
   2 docker exec -u www-data wp_veriaguide_prod php /var/www/html/data/restaurants_veria/import_restaurants.php