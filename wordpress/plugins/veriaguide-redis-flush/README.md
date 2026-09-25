# VeriaGuide Redis Flush

WordPress admin tool to flush the Redis cache used by the FastAPI frontend (`veriaguide_redis`). Same effect as:

```bash
docker exec veriaguide_redis redis-cli FLUSHALL
```

without SSH. After a flush, do a **hard refresh** in the browser (cached HTML/CDN cookies can still look stale). Restarting `veriaguide_frontend` is **optional and separate** — this plugin does not restart Docker.

## Install

1. Copy this folder to WordPress:

   ```text
   wp-content/plugins/veriaguide-redis-flush/
   ```

   On the live VPS (CyberPanel native WordPress):

   ```bash
   # from the repo checkout
   cp -r wordpress/plugins/veriaguide-redis-flush \
     /home/veriaguide.gr/public_html/wp-content/plugins/
   ```

   (Adjust the public_html path if your site root differs.)

2. In wp-admin: **Plugins → Activate “VeriaGuide Redis Flush”**.
3. Open **Tools → Redis cache**.
4. Click **Flush Redis cache**. Only users with `manage_options` (Administrators) can do this.

The repo also keeps the existing CPT file at `wordpress/veriaguide-cpt.php` (copied onto the server as a single-file plugin). This flush plugin is a separate directory under `wordpress/plugins/` so it matches a normal `wp-content/plugins` layout.

## Redis connection (CyberPanel + Docker)

On production, `docker-compose.vps.yml` runs **only frontend + Redis**. WordPress is **not** in Docker — it runs on the host (LiteSpeed). Redis has **no published ports** in that compose file, so PHP cannot reach `veriaguide_redis:6379` by container name.

**Recommended on the VPS:** publish Redis on loopback only, then use the plugin defaults.

In `docker-compose.vps.yml` under the `redis` service:

```yaml
ports:
  - "127.0.0.1:6379:6379"
```

Recreate the Redis container after that change. Plugin defaults:

| Setting | Default | Why |
| --- | --- | --- |
| Host | `127.0.0.1` | WordPress on the host talks to the published Redis port |
| Port | `6379` | Redis default |
| Password | empty | Current VPS Redis has no `requirepass` |
| Database | `0` | Frontend `REDIS_URL=redis://veriaguide_redis:6379/0` |
| Command | `FLUSHDB` | Wipes only DB 0 |

If you instead run WordPress **inside** the same Docker network as Redis, set host to `veriaguide_redis` (or `redis`) in the admin form.

Do **not** bind Redis to `0.0.0.0` on the public IP.

## wp-config constants (optional, no secrets in git)

Constants override the admin fields:

```php
define('VERIAGUIDE_REDIS_HOST', '127.0.0.1');
define('VERIAGUIDE_REDIS_PORT', 6379);
define('VERIAGUIDE_REDIS_PASSWORD', ''); // set only if you enable Redis AUTH
define('VERIAGUIDE_REDIS_DB', 0);
define('VERIAGUIDE_REDIS_FLUSH_MODE', 'FLUSHDB'); // or FLUSHALL
```

`FLUSHALL` matches the old SSH habit and **clears the whole Redis instance**. The admin page shows a warning. Use it only because this Redis is dedicated to VeriaGuide.

## PHP Redis extension

Not required. If `phpredis` is missing, the plugin speaks Redis RESP over TCP. Optional:

```bash
# Debian/Ubuntu example
apt-get install php-redis
```

No Composer / Predis.

## Smoke-check from the host

After publishing `127.0.0.1:6379`:

```bash
redis-cli -h 127.0.0.1 PING
# or
docker exec veriaguide_redis redis-cli PING
```

Use **Test connection (PING)** on the Tools page before flushing.
