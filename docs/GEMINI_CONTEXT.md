# Gemini Project Context: VeriaGuide

This document summarizes the architecture, tools, and operational workflow for the VeriaGuide project to ensure efficient collaboration.

## 1. Operational Workflow

-   **Gemini's Environment:** I am running on a local macOS machine. My access is restricted to the local project directory at `<LOCAL_REPO>`.
-   **User's Environment:** The user operates on the production server. The project root on the server is `$WP_DOCUMENT_ROOT/`.
-   **Interaction Model:** I **cannot** access the production server directly.
    -   Any files I modify locally must be **uploaded by the user** to the server.
    -   Any shell commands I provide must be **executed by the user** on the server.

## 2. System Architecture

The application is orchestrated with Docker Compose and runs on an **AlmaLinux 9** host.

-   **Project Root on Server:** `$WP_DOCUMENT_ROOT/`
-   **Compose File:** `docker-compose.prod.yml` (located in project root)
-   **Environment Variables:** `.env.production.docker`

### Services:

-   **`traefik`**: The reverse proxy that routes external traffic to the appropriate backend service.
-   **`db`**: A `mariadb:latest` container for the WordPress database.
-   **`wordpress`**: A `wordpress:latest` container (Apache/PHP) serving as a headless CMS.
    -   **WordPress Root:** The server's project root (`$WP_DOCUMENT_ROOT`) is mounted directly into the container at `/var/www/html`.
-   **`redis`**: A `redis:7-alpine` container for caching.
-   **`frontend`**: A **FastAPI** (Python) application that serves as the public-facing website. It fetches data from the WordPress REST API.

## 3. Troubleshooting & Known Issues

This section documents common problems and their solutions for this specific project.

### 3.1. SELinux Permissions
-   **Symptom:** WordPress fails to start correctly, or there are unexpected "Permission Denied" errors despite correct file permissions. The `ls -l` command shows a `+` at the end of the permission string (e.g., `-rw-rw-r--+`).
-   **Cause:** The AlmaLinux host uses SELinux, which blocks container access to mounted volumes by default.
-   **Solution:** Add the `:Z` flag to the volume mount in `docker-compose.prod.yml`.
    -   **Example:** `volumes: - $WP_DOCUMENT_ROOT:/var/www/html:Z`

### 3.2. WordPress REST API returns 404
-   **Symptom:** The frontend application cannot display posts, and its logs show "404 Not Found" errors when calling `/wp-json/...` endpoints.
-   **Cause:** WordPress permalinks are not set correctly, or the `.htaccess` file is missing/incorrect.
-   **Solution:** The `wp-cli` tool is **not available** in the `wordpress` container. The `fix-permalinks.php` script must be used.
    1.  **Upload:** User uploads `fix-permalinks.php` to `$WP_DOCUMENT_ROOT/`.
    2.  **Execute:** `docker exec -u www-data wp_veriaguide_prod php /var/www/html/fix-permalinks.php`
    3.  **Delete:** `rm $WP_DOCUMENT_ROOT/fix-permalinks.php`

### 3.3. Broken WordPress Admin Panel (JS/CSS not loading)
-   **Symptom:** The WordPress admin panel is unstyled, and browser console shows MIME type errors (`text/html` instead of `application/javascript`).
-   **Cause:** The Traefik routing rule for the `wordpress` service is too specific and doesn't include paths for static assets.
-   **Solution:** Modify the Traefik label in `docker-compose.prod.yml` to include `/wp-content` and `/wp-includes`.
    -   **Correct Rule:** `"Host(`veriaguide.gr`) && (PathPrefix(`/wp-admin`) || PathPrefix(`/wp-json`) || PathPrefix(`/wp-login.php`) || PathPrefix(`/wp-content`) || PathPrefix(`/wp-includes`))"`

### 3.4. Content Security Policy (CSP) Errors
-   **Symptom:** Browser console shows errors like `Refused to execute inline script...`.
-   **Cause:** The CSP is set in the FastAPI middleware (`frontend/app/middleware/security.py`) and is too restrictive.
-   **Solution:** The `script-src` directive in the production CSP likely needs the `'unsafe-inline'` keyword added. After modification, the `frontend` container must be rebuilt (`docker-compose up --build...`).

### 3.5. Google Maps API Errors
-   **Symptom:** Maps don't load; browser console shows `BillingNotEnabledMapError`.
-   **Cause:** The Google Cloud project associated with the API key does not have a billing account enabled.
-   **Solution:** The user must log in to the Google Cloud Console and enable billing for the project. This is an account issue, not a code issue.
