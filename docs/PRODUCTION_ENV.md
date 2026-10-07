# Production environment (VPS)

`docker-compose.vps.yml` is what the live server uses (FastAPI + Redis). WordPress runs natively under CyberPanel/OpenLiteSpeed. Compose loads **`env_file: .env`** from the document root. That file must exist **only on the server** (or locally for development) and is gitignored.

## Required on the server `.env`

These names match what the app and compose already read:

| Variable | Used by | Notes |
|----------|---------|--------|
| `ENVIRONMENT` | FastAPI | Use `production` |
| `SITE_URL` | FastAPI / compose | Public site URL (compose also sets `https://veriaguide.gr`) |
| `WP_API_URL` | FastAPI | Public WP REST base, e.g. `https://veriaguide.gr/wp-json/wp/v2` |
| `WP_API_USERNAME` | FastAPI contact/admin WP calls | WordPress user |
| `WP_API_PASSWORD` | FastAPI | WordPress **Application Password** |
| `REDIS_URL` | FastAPI / compose | Default in compose: `redis://veriaguide_redis:6379/0` |
| `SECRET_KEY` | FastAPI sessions/stats HMAC | Long random string |
| `ADMIN_API_KEY` | Admin/cache-warm/AI stats | Long random string |
| `GOOGLE_MAPS_API_KEY` | Maps in the frontend | Restrict by HTTP referrer |
| `GOOGLE_API_KEY` | AI Guide (Gemini) | Required if `AI_GUIDE_ENABLED=true` |
| `AI_GUIDE_ENABLED` | compose / AI Guide | Compose sets `"true"` for production |
| `ENABLE_API_DOCS` | compose | Compose sets `"false"` |

Optional: `MYSQL_*` / `DB_*` if you still run the legacy Docker WordPress/DB stack (`docker-compose.yml` / `docker-compose.legacy-fullstack.yml`). The VPS compose file does **not** start MySQL.

Copy `.env.example` to `.env` on the server and fill real values. Never commit `.env`.

## Deploy scripts (local machine)

Scripts such as `sync_to_vps.sh`, `full-deploy-to-vps.sh`, and `utility_scripts/deploy-trailing-slash-fix.sh` expect:

- `SSH_HOST` — SSH alias or `user@host` from your **local** SSH config
- `WP_DOCUMENT_ROOT` — absolute document root **on the server**

Do not put those values in the repository.

## `docker-compose.vps.yml` defaults

Compose still binds FastAPI to `127.0.0.1:8000` and adds `extra_hosts` for `veriaguide.gr` → host gateway so the container can reach native WordPress. After pulling this branch on the VPS, restart with:

```bash
docker compose -f docker-compose.vps.yml up -d
```

No compose keys were renamed; existing server `.env` keys keep working.
