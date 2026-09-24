# Analysis of Potentially Unnecessary Files

This document provides a list of files that can likely be removed from the project to clean up the main directory. They are categorized by how safe they are to delete.

---

### Category 1: Safe to Delete

These files are system-specific metadata and are not used by the application.

-   **`.DS_Store`**: Automatically created by macOS. It can be deleted without any issues.

---

### Category 2: Likely Safe to Delete (Backups & Exports)

These files appear to be one-time backups or exports. The running application does not use them. It's recommended to delete them unless you want to keep them as manual backups.

-   **`acf-export-2025-05-09.json`**: A backup of "Advanced Custom Fields" data from a specific date.
-   **`vhost.conf.corrected`**: A backup of a web server virtual host configuration.
-   **`wordpress-htaccess-fixed.txt`**: A backup of a WordPress `.htaccess` file.

---

### Category 3: Optional Cleanup (Scripts & Documentation)

These files are not part of the core application but are one-off helper scripts or documentation. They can be deleted to clean up the project, but a better option might be to move them into a new sub-folder (e.g., a `scripts/` or `docs/` folder) if you want to keep them for future reference.

**One-Time Scripts:**
-   `activate-plugin.php`
-   `debug-religious-sites.php`
-   `fix-csp-and-assets.sh`
-   `fix-cyberpanel-permissions.sh`
-   `fix-mysql-permissions.sh`
-   `fix-permalinks.php`
-   `fix-wordpress-api.sh`
-   `wp-setup.php`
-   `test-security.py`
-   `test-security.sh`

**Documentation:**
-   `ARCHITEKTUR_REVIEW_VERIAGUIDE.md`
-   `CYBERPANEL_SETUP.md`
-   `SECURITY_SETUP.md`

---

### Category 4: Development-Only Files

These files define the **local development environment**. The production server uses `docker-compose.vps.yml` (frontend + Redis only).

-   **`docker-compose.yml`**: The base configuration for the local development environment.
-   **`docker-compose.dev.yml`**: An extension file for the local development environment.

**Recommendation:** You can delete these two files **IF AND ONLY IF** you never work on or run this project on your local laptop and only work on the production server. Deleting them will remove the ability to run the local development setup. If you want to keep the ability to develop locally, **do not delete these files.**
