# ✅ VeriaGuide - Production Installation Complete!

**Date:** June 21, 2026  
**Server:** 178.105.68.81 (AlmaLinux 9.8)

---

## 🎉 Installation Summary

Όλα τα components έχουν εγκατασταθεί επιτυχώς στον production server!

### ✅ Installed Components

1. **Docker 29.6.0** - Container runtime
2. **Docker Compose 5.1.4** - Multi-container orchestration
3. **Python 3.11.13** - Runtime environment
4. **MariaDB** - Database server (running in container)
5. **WordPress** - Headless CMS (running in container)
6. **Redis 7.4.9** - Cache server (running in container)
7. **FastAPI Frontend** - Python web application (running in container)
8. **Traefik 2.10** - Reverse proxy (running in container)

---

## 🚀 Services Status

All containers are running:

```bash
✅ veriaguide_frontend_prod   - Port 8000 (Healthy)
✅ veriaguide_redis_prod      - Internal (Redis cache)
✅ veriaguide_traefik         - Ports 8080, 8091, 8443
✅ veriaguide_wp_db_prod      - Internal (MariaDB)
✅ wp_veriaguide_prod         - Internal (WordPress)
```

---

## 📡 Access Points

### Frontend Application
- **URL:** http://178.105.68.81:8000
- **Status:** ✅ RUNNING
- **Health Check:** http://178.105.68.81:8000/health

### WordPress Admin
- **URL:** http://178.105.68.81:8091/wp-admin
- **Status:** ⚠️  NEEDS SETUP
- **Note:** WordPress database is empty - needs initial setup via browser

### Traefik Dashboard
- **URL:** http://178.105.68.81:8080
- **Status:** ✅ RUNNING

---

## 📁 File Locations

### Application Directory
```
/home/veriaguide.gr/public_html/
```

### Important Files
- **Environment:** `.env.production.docker` (symlinked to `.env`)
- **Docker Compose:** `docker-compose.prod.yml`
- **Frontend Code:** `frontend/`
- **Data:** `data/submissions/`, `data/contributions/`
- **Logs:** `frontend/logs/`
- **SSL Certs:** `/etc/letsencrypt/live/veriaguide.gr/`

---

## 🔐 Configuration

### Database Credentials
```env
MYSQL_ROOT_PASSWORD=VeriaGuide2026!RootPass
MYSQL_DATABASE=veriaguide_db
MYSQL_USER=wp_kostass
MYSQL_PASSWORD=fai3don4
```

### Environment Variables
Location: `/home/veriaguide.gr/public_html/.env.production.docker`

---

## 🛠️ Common Commands

### View Container Status
```bash
cd /home/veriaguide.gr/public_html
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f wordpress
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart frontend
```

### Stop Everything
```bash
docker-compose -f docker-compose.prod.yml down
```

### Start Everything
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Rebuild Frontend
```bash
docker-compose -f docker-compose.prod.yml up -d --build frontend
```

---

## ⚠️ Next Steps Required

### 1. WordPress Setup
WordPress database is empty and needs initial setup:

1. Open browser to: http://178.105.68.81:8091/wp-admin/install.php
2. Complete WordPress installation wizard
3. Install required plugins:
   - Advanced Custom Fields (ACF)
   - Custom Post Type UI
4. Import ACF field definitions from `acf-export-2025-09-11.json`
5. Create custom post types for all content categories

### 2. Import Data
Once WordPress is set up, import the existing data:

```bash
# Import accommodations
php import_accommodations.php

# Import cafes
php import_cafes.php

# Import restaurants (if exists)
php import_restaurants.php
```

### 3. Configure OpenLiteSpeed/CyberPanel
Set up reverse proxy to forward requests from port 80/443 to port 8000:

- Main domain (veriaguide.gr) → http://localhost:8000
- WordPress endpoints (/wp-admin, /wp-json) → http://localhost:8091

### 4. Update Environment Variables
Edit `/home/veriaguide.gr/public_html/.env.production.docker`:

- Add real `GOOGLE_MAPS_API_KEY`
- Change `ADMIN_API_KEY` to a secure random value
- Update `SECRET_KEY` to a secure random value (min 50 chars)

### 5. Warm the Cache
Once WordPress has content:

```bash
curl -X POST http://localhost:8000/admin/warm-cache \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

### 6. Test All Pages
Visit and test:
- Homepage: http://178.105.68.81:8000/
- Categories: /restaurants, /museums, /accommodations, etc.
- Submissions: http://178.105.68.81:8000/submit
- Contributions: http://178.105.68.81:8000/contribute

---

## 🔥 Firewall Ports

These ports are open:
- **8000** - Frontend application
- **8091** - Traefik HTTP proxy
- **8443** - Traefik HTTPS proxy
- **8080** - Traefik dashboard

---

## 📊 System Information

- **OS:** AlmaLinux 9.8 (Seafoam Ocelot)
- **Server:** CyberPanel + OpenLiteSpeed
- **SSH Access:** root@178.105.68.81
- **Application Path:** /home/veriaguide.gr/public_html

---

## 🆘 Troubleshooting

### Containers Won't Start
```bash
# Check Docker status
systemctl status docker

# Restart Docker
systemctl restart docker

# Clean up networks
docker network prune -f

# Try again
cd /home/veriaguide.gr/public_html
docker-compose -f docker-compose.prod.yml up -d
```

### Permission Issues
```bash
# Fix WordPress permissions
chown -R 33:33 /home/veriaguide.gr/public_html/wp-*
chmod -R 755 /home/veriaguide.gr/public_html/wp-content

# Restart WordPress
docker-compose -f docker-compose.prod.yml restart wordpress
```

### Frontend Not Responding
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs frontend

# Restart frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Database Connection Issues
```bash
# Check if database is running
docker-compose -f docker-compose.prod.yml ps

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Connect to database
docker-compose -f docker-compose.prod.yml exec db mariadb -uroot -pVeriaGuide2026!RootPass
```

---

## 📝 Notes

1. **SSL Certificates:** Already exist at `/etc/letsencrypt/live/veriaguide.gr/`
2. **WordPress Content:** Existing wp-content files are preserved
3. **Submissions/Contributions:** Systems are ready at `/submit` and `/contribute`
4. **Cache:** Redis is running and ready for cache warming
5. **Docker Compose:** Using production config (`docker-compose.prod.yml`)

---

## ✨ Success!

Το VeriaGuide έχει εγκατασταθεί επιτυχώς! 🎉

Το frontend τρέχει και είναι έτοιμο να χρησιμοποιηθεί.
Απλά χρειάζεται να ολοκληρώσεις το WordPress setup και να κάνεις import τα δεδομένα.

**Enjoy!** 🚀
