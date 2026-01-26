# WordPress Update Anleitung (Docker-Umgebung)

Dieses Dokument beschreibt den korrekten Prozess zur Aktualisierung der WordPress-Instanz, die in der Docker-Umgebung auf dem AlmaLinux-Server läuft.

**Wichtiger Hinweis:** Führen Sie die Befehle immer aus dem Home-Verzeichnis des Benutzers (`/home/veriaguide.gr`) aus, nicht aus `public_html`.

---

#WP Backup 

## Backup wp-content
mkdir /home/veriaguide.gr/wp_content_backup
nano /home/veriaguide.gr/public_html/create_backup.sh
     #!/bin/sh
     docker run --rm -v /home/veriaguide.gr/public_html/wp-content:/source:ro,Z
     -v /home/veriaguide.gr/wp_content_backup:/dest:Z alpine cp -a /source/. /dest/

chmod +x /home/veriaguide.gr/create_backup.sh
sudo /home/veriaguide.gr/public_html/create_backup.sh

## WP DB Backup
nano /home/veriaguide.gr/public_html/db_backup.sh
    #!/bin/sh
    docker compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml exec db sh -c 'mariadb-dump -u${MYSQL_USER} -p${MYSQL_PASSWORD}
     ${MYSQL_DATABASE}' > /home/veriaguide.gr/db_backup_$(date +%Y-%m-%d).sql

chmod +x /home/veriaguide.gr/db_backup.sh
sudo /home/veriaguide.gr/public_html/db_backup.sh

## WP Download
sudo docker compose -f
     /home/veriaguide.gr/public_html/docker-compose.prod.yml pull wordpress

sudo docker compose -f
     /home/veriaguide.gr/public_html/docker-compose.prod.yml up -d --no-deps
     wordpress

---   

## Schritt 1: Backups erstellen

Vor jedem Update ist die Erstellung von Backups zwingend erforderlich.

### 1.1 Backup der WordPress-Dateien (`wp-content`)

Wir erstellen eine 1:1-Kopie des `wp-content`-Ordners.

1.  **Backup-Verzeichnis erstellen:** Erstellen Sie einen datierten Ordner, um die Backups zu organisieren.
    ```bash
    mkdir /home/veriaguide.gr/backup_$(date +%Y-%m-%d)
    ```

2.  **Dateien kopieren:** Dieser Befehl startet einen temporären Docker-Container, um den gesamten `wp-content`-Ordner sicher in ein Unterverzeichnis des neuen Backup-Ordners zu kopieren. Dies umgeht mögliche SELinux-Berechtigungsprobleme.
    ```bash
    sudo docker run --rm -v /home/veriaguide.gr/public_html/wp-content:/source:ro,Z -v /home/veriaguide.gr/backup_$(date +%Y-%m-%d)/wp-content-backup:/dest:Z alpine cp -a /source/. /dest/
    ```

### 1.2 Backup der Datenbank

Wir erstellen einen SQL-Dump der MariaDB-Datenbank.

1.  **Datenbank-Dump erstellen:** Dieser Befehl führt `mariadb-dump` innerhalb des Datenbank-Containers aus und speichert das Ergebnis in einer `.sql`-Datei im zuvor erstellten Backup-Ordner.
    ```bash
    sudo docker-compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml exec db sh -c 'mariadb-dump -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}' > /home/veriaguide.gr/backup_$(date +%Y-%m-%d)/db_backup.sql
    ```

---

## Schritt 2: Update durchführen

Nachdem die Backups sicher sind, kann das eigentliche Update beginnen.

### 2.1 Dateiberechtigungen vorbereiten

Neue WordPress-Images können strengere Anforderungen an die Dateiberechtigungen haben. Wir setzen den Eigentümer aller WordPress-Dateien auf den Webserver-Benutzer (`www-data`, UID `33`), um Lesefehler zu vermeiden.

```bash
sudo chown -R 33:33 /home/veriaguide.gr/public_html/
```

### 2.2 WordPress-Container aktualisieren

1.  **Neuestes Image herunterladen:**
    ```bash
    sudo docker-compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml pull wordpress
    ```

2.  **Container neu erstellen:** Dieser Befehl ersetzt den alten Container durch den neuen, aktualisierten.
    ```bash
    sudo docker-compose -f /home/veriaguide.gr/public_html/docker-compose.prod.yml up -d --no-deps wordpress
    ```

---

## Schritt 3: Abschluss

Der technische Teil des Updates ist abgeschlossen. Der letzte Schritt findet im WordPress-Admin-Bereich statt.

1.  **Anmelden:** Öffnen Sie `https://veriaguide.gr/wp-admin` und melden Sie sich an.
2.  **Datenbank-Update bestätigen:** Falls WordPress Sie auffordert, die Datenbank zu aktualisieren, bestätigen Sie diesen Vorgang. Dies ist ein normaler Schritt nach einem Core-Update.

Wenn keine Aufforderung erscheint, ist alles erledigt.
