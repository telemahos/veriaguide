#!/bin/bash

# Fix MySQL permissions for Docker containers
echo "🔧 Fixing MySQL permissions for Docker containers..."

# MySQL Credentials (anpassen falls nötig)
DB_NAME="veri_veriaguide_db"
DB_USER="veri_wp_kostass"
DB_PASSWORD="1234"

echo "📋 Creating MySQL user with Docker network access..."

# MySQL Commands ausführen
mysql -u root -p << EOF
-- User für Docker Container erstellen (erlaubt alle IPs im Docker-Netzwerk)
CREATE USER IF NOT EXISTS '${DB_USER}'@'172.%.%.%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'172.%.%.%';

-- User für localhost (falls noch nicht vorhanden)
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';

-- User für alle Hosts (weniger sicher, aber funktioniert immer)
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';

-- Datenbank erstellen falls nicht vorhanden
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Berechtigungen neu laden
FLUSH PRIVILEGES;

-- Aktuelle User anzeigen
SELECT User, Host FROM mysql.user WHERE User = '${DB_USER}';

-- MySQL Bind-Address prüfen
SHOW VARIABLES LIKE 'bind_address';
EOF

echo "✅ MySQL permissions updated!"
echo ""
echo "📋 Next steps:"
echo "1. Restart MySQL if bind-address was 127.0.0.1"
echo "2. Test connection: mysql -u ${DB_USER} -p${DB_PASSWORD} -h localhost ${DB_NAME}"
echo "3. Restart Docker containers: ./start-production-docker.sh"