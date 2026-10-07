# OpenLiteSpeed: Authorization-Header für WordPress REST / Application Passwords

**Symptom:** `GET /wp-json/wp/v2/users/me` mit HTTP Basic (Application Password) liefert `401 rest_not_logged_in`, obwohl das Passwort stimmt. WordPress sieht den Header nicht (`PHP_AUTH_USER` / `HTTP_AUTHORIZATION` fehlen).

OpenLiteSpeed + LSAPI verwirft `Authorization` oft, bevor PHP startet. Die Apache-`RewriteRule … [E=HTTP_AUTHORIZATION:…]` in `.htaccess` reicht auf OLS häufig nicht.

Dieses Repo ergänzt:

1. Root-`.htaccess`: `SetEnvIf` **und** die bestehende `RewriteRule`.
2. Must-use-Plugin `wordpress/mu-plugins/veria-authorization-header.php` (stellt Header + Basic-User/Pass in `$_SERVER` wieder her).
3. Vhost-Rewrite in `utility_scripts/fix-ols-vhost-proxy.sh` (OLS-seitig, vor den WP-/Proxy-Regeln).

Es gibt **keinen SSH aus der Cursor-Cloud-VM**. Dateien müssen auf den VPS kopiert und OLS neu geladen werden.

## Deploy-Pfade (siehe `VPS_SESSION_HANDOFF.md`)

| Quelle im Repo | Ziel auf dem VPS |
|----------------|------------------|
| `.htaccess` | `$WP_DOCUMENT_ROOT/.htaccess` |
| `wordpress/mu-plugins/veria-authorization-header.php` | `$WP_DOCUMENT_ROOT/wp-content/mu-plugins/veria-authorization-header.php` |
| `utility_scripts/fix-ols-vhost-proxy.sh` | `$WP_DOCUMENT_ROOT/fix-ols-vhost-proxy.sh` (optional, nur wenn das Script dort genutzt wird) |
| OLS vhost | `/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf` |

## 1. Dateien kopieren

```bash
ssh-add ~/.ssh/id_ed25519
# oder: ssh vps / ssh root@***REMOVED***

scp .htaccess vps:$WP_DOCUMENT_ROOT/.htaccess

ssh vps "mkdir -p $WP_DOCUMENT_ROOT/wp-content/mu-plugins"
scp wordpress/mu-plugins/veria-authorization-header.php \
  vps:$WP_DOCUMENT_ROOT/wp-content/mu-plugins/veria-authorization-header.php
```

MU-Plugins brauchen **keine** Aktivierung in wp-admin.

## 2. Vhost: Authorization an PHP durchreichen

In `/usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf` im bestehenden `rewrite { … rules <<<END_rules … }` **oben** (vor den `[L]`-Regeln für `/wp-json`) einfügen:

```apache
RewriteEngine On

# Pass Authorization to PHP (Application Passwords / REST Basic auth)
RewriteCond %{HTTP:Authorization} .+
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
```

`autoLoadHtaccess 1` muss gesetzt bleiben, damit die gehärtete Document-Root-`.htaccess` geladen wird.

Backup + Restart:

```bash
cp /usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf \
  /usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf.bak.$(date +%Y%m%d_%H%M%S)

# Nach dem Edit:
/usr/local/lsws/bin/lswsctrl restart
```

Wer das Proxy-Fix-Script **neu** laufen lässt, bekommt denselben Snippet mit (Script überschreibt den Rewrite-Block — vorher Backup prüfen):

```bash
scp utility_scripts/fix-ols-vhost-proxy.sh vps:$WP_DOCUMENT_ROOT/fix-ols-vhost-proxy.sh
ssh vps "bash $WP_DOCUMENT_ROOT/fix-ols-vhost-proxy.sh"
```

## 3. Prüfen (ohne Passwort im Repo)

```bash
curl -sS -u 'WPUSER:APPLICATION_PASSWORD' \
  https://veriaguide.gr/wp-json/wp/v2/users/me
```

Erfolg: JSON des aktuellen Users (nicht `{"code":"rest_not_logged_in"}`).

Falsches Passwort: `401` mit Application-Password-Fehler, **nicht** `rest_not_logged_in` (letzteres = Header kommt nicht an).
