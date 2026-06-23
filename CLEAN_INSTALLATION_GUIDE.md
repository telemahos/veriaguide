# VeriaGuide - Οδηγός Καθαρής Εγκατάστασης στον VPS

## 📋 Προαπαιτούμενα

- **VPS Server**: AlmaLinux 9.8
- **CyberPanel**: Εγκατεστημένο με OpenLiteSpeed
- **Domain**: veriaguide.gr (με SSL certificate)
- **Database**: Θα δημιουργηθεί μέσω CyberPanel
- **SSH Access**: root@***REMOVED*** (port 22)
- **Project Root**: `$WP_DOCUMENT_ROOT/` (WordPress + Frontend + Docker)

---

## 🎯 Σειρά Εγκατάστασης

### **Φάση 1: WordPress (Χειροκίνητα μέσω CyberPanel)**
### **Φάση 2: Docker Setup**
### **Φάση 3: Frontend (FastAPI)**
### **Φάση 4: Proxy Configuration**
### **Φάση 5: Import Content**

---

## 📝 ΦΑΣΗ 1: WordPress Εγκατάσταση (Χειροκίνητα)

### **1.1 Δημιουργία Database μέσω CyberPanel**

1. Σύνδεση στο CyberPanel: `https://***REMOVED***:8090`
2. **Databases** → **Create Database**
   - Database Name: `veria_wordpress`
   - Username: `veria_wpuser`
   - Password: `[STRONG_PASSWORD]` (κράτησέ το!)
3. Σημείωσε τα credentials:
   ```
   DB_NAME: veria_wordpress
   DB_USER: veria_wpuser
   DB_PASS: [το password που έβαλες]
   DB_HOST: localhost
   ```

### **1.2 Εγκατάσταση WordPress μέσω CyberPanel**

1. **Websites** → **List Websites** → **veriaguide.gr**
2. **Applications** → **Install WordPress**
   - Path: `/` (root)
   - Database: `veria_wordpress`
   - Admin Username: `admin`
   - Admin Password: `[STRONG_PASSWORD]`
   - Admin Email: `info@veriaguide.gr`
3. Περίμενε να ολοκληρωθεί (2-3 λεπτά)

### **1.3 Επαλήθευση WordPress**

1. Άνοιξε: `https://veriaguide.gr/wp-admin/`
2. Κάνε login με τα credentials
3. ✅ **ΕΠΙΒΕΒΑΙΩΣΗ**: Βλέπεις το WordPress Dashboard

### **1.4 Ενεργοποίηση Plugins**

Πήγαινε στο **Plugins** και ενεργοποίησε:
- ✅ Advanced Custom Fields (ACF)
- ✅ Custom Post Type UI
- ✅ VeriaguideαCPT (custom plugin)
- ✅ API Key for Google Maps

### **1.5 Δημιουργία Custom Post Types**

**Plugins** → **CPT UI** → **Add/Edit Post Types**

Δημιούργησε αυτούς τους post types:

#### **Post Type 1: Accommodation**
```
Post Type Slug: accommodation
Plural Label: Accommodations
Singular Label: Accommodation
✅ REST API: Enabled
✅ REST Base: accommodations
```

#### **Post Type 2: Restaurant**
```
Post Type Slug: restaurant
Plural Label: Restaurants
Singular Label: Restaurant
✅ REST API: Enabled
✅ REST Base: restaurants
```

#### **Post Type 3: Cafe**
```
Post Type Slug: cafe
Plural Label: Cafes
Singular Label: Café
✅ REST API: Enabled
✅ REST Base: cafes
```

#### **Post Type 4: Museum**
```
Post Type Slug: museum
Plural Label: Museums
Singular Label: Museum
✅ REST API: Enabled
✅ REST Base: museums
```

#### **Post Type 5: Archaeological Site**
```
Post Type Slug: archaeological_site
Plural Label: Archaeological Sites
Singular Label: Archaeological Site
✅ REST API: Enabled
✅ REST Base: archaeological_sites
```

#### **Post Type 6: Religious Site**
```
Post Type Slug: religious_site
Plural Label: Religious Sites
Singular Label: Religious Site
✅ REST API: Enabled
✅ REST Base: religious_sites
```

### **1.6 Δοκιμή REST API**

Άνοιξε: `https://veriaguide.gr/wp-json/wp/v2/accommodations`

✅ **ΕΠΙΒΕΒΑΙΩΣΗ**: Βλέπεις JSON response (έστω και άδειο `[]`)

---

## 📝 ΦΑΣΗ 2: Docker Setup

### **2.1 Σύνδεση στον VPS**

```bash
ssh root@***REMOVED***
```

### **2.2 Εγκατάσταση Docker (αν δεν υπάρχει)**

```bash
# Έλεγχος αν υπάρχει Docker
docker --version

# Αν ΔΕΝ υπάρχει:
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io
systemctl start docker
systemctl enable docker
```

### **2.3 Εγκατάσταση Docker Compose (αν δεν υπάρχει)**

```bash
# Έλεγχος
docker-compose --version

# Αν ΔΕΝ υπάρχει:
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
```

### **2.4 Δημιουργία Project Structure**

```bash
# Πήγαινε στο project root (WordPress + Frontend μαζί)
cd $WP_DOCUMENT_ROOT

# Δημιούργησε structure
mkdir -p frontend/app
mkdir -p frontend/static
mkdir -p frontend/templates
mkdir -p frontend/logs
mkdir -p data/submissions
mkdir -p data/contributions
mkdir -p redis-data
mkdir -p traefik
```

### **2.5 Upload Project Files από Local**

Από το **LOCAL μηχάνημα** σου:

```bash
# Frontend application
scp -r ***REMOVED***/frontend/* root@***REMOVED***:$WP_DOCUMENT_ROOT/frontend/

# Docker compose files
scp ***REMOVED***/docker-compose.prod.yml root@***REMOVED***:$WP_DOCUMENT_ROOT/
scp ***REMOVED***/.env.production.docker root@***REMOVED***:$WP_DOCUMENT_ROOT/

# Data files για imports
scp -r ***REMOVED***/data/* root@***REMOVED***:$WP_DOCUMENT_ROOT/data/
```

### **2.6 Δημιουργία Προσαρμοσμένου docker-compose.yml**

**⚠️ ΚΡΙΣΙΜΟ**: Δημιούργησε ένα **νέο** docker-compose file που **ΔΕΝ περιλαμβάνει** WordPress!

Στον VPS:

```bash
cd $WP_DOCUMENT_ROOT

cat > docker-compose.vps.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: veriaguide_redis
    restart: always
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - ./redis-data:/data
    networks:
      - veriaguide_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
    container_name: veriaguide_frontend
    restart: always
    environment:
      SITE_URL: https://veriaguide.gr
      ENVIRONMENT: production
      WP_API_URL: https://veriaguide.gr/wp-json/wp/v2
      REDIS_URL: redis://veriaguide_redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_HOSTS: veriaguide.gr,www.veriaguide.gr
      GOOGLE_MAPS_API_KEY: ${GOOGLE_MAPS_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - redis
    networks:
      - veriaguide_network

volumes:
  redis-data:

networks:
  veriaguide_network:
    name: veriaguide_network
    driver: bridge
EOF

echo "✅ docker-compose.vps.yml created"
```

### **2.7 Ρύθμιση Environment Variables**

```bash
cd $WP_DOCUMENT_ROOT

cat > .env << 'EOF'
# Production Environment
ENVIRONMENT=production

# WordPress API (existing WordPress installation)
WP_API_URL=https://veriaguide.gr/wp-json/wp/v2

# Redis
REDIS_URL=redis://veriaguide_redis:6379/0
REDIS_DEFAULT_TTL=1800

# Security
SECRET_KEY=CHANGE_THIS_TO_VERY_LONG_RANDOM_STRING_MIN_50_CHARS
ALLOWED_HOSTS=veriaguide.gr,www.veriaguide.gr

# Google Maps
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE

# Site Configuration
SITE_URL=https://veriaguide.gr
DEBUG=False
LOG_LEVEL=INFO
EOF

# Γέμισε τα SECRET_KEY και GOOGLE_MAPS_API_KEY!
nano .env
```

### **2.8 Εκκίνηση Docker Containers**

```bash
cd $WP_DOCUMENT_ROOT

# Symlink production env file
ln -sf .env.production.docker .env

# Build και start
docker-compose -f docker-compose.vps.yml up -d --build

# Έλεγχος status
docker-compose -f docker-compose.vps.yml ps

# Περίμενε 30 δευτερόλεπτα για initialization
sleep 30

# Έλεγχος logs
docker-compose -f docker-compose.vps.yml logs frontend
```

✅ **ΕΠΙΒΕΒΑΙΩΣΗ**: Θα δεις "Cache warming completed successfully!"

---

## 📝 ΦΑΣΗ 3: OpenLiteSpeed Proxy Configuration

### **3.1 Δημιουργία Proxy Configuration**

Στον VPS:

```bash
# Backup πριν αλλάξεις proxy settings
cd $WP_HOME
mkdir -p backups
tar -czf backups/public_html_backup_$(date +%Y%m%d_%H%M%S).tar.gz public_html/

# Προαιρετικό test file (ΜΗΝ το χρησιμοποιήσεις αν το WordPress ήδη τρέχει)
cat > $WP_DOCUMENT_ROOT/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>VeriaGuide</title></head>
<body>
<h1>OpenLiteSpeed Proxy Test</h1>
<p>If you see this, OpenLiteSpeed is working.</p>
</body>
</html>
EOF
```

### **3.2 Ρύθμιση OpenLiteSpeed Virtual Host**

1. **CyberPanel** → **Websites** → **List Websites** → **veriaguide.gr**
2. **Rewrite Rules** → Άνοιξε το configuration
3. Πρόσθεσε αυτό:

```apache
RewriteEngine On

# Proxy WordPress Admin/API paths to existing WordPress
RewriteCond %{REQUEST_URI} ^/wp-admin [OR]
RewriteCond %{REQUEST_URI} ^/wp-json [OR]
RewriteCond %{REQUEST_URI} ^/wp-login\.php [OR]
RewriteCond %{REQUEST_URI} ^/wp-content [OR]
RewriteCond %{REQUEST_URI} ^/wp-includes
RewriteRule ^(.*)$ - [L]

# Proxy everything else to FastAPI Frontend
RewriteCond %{REQUEST_URI} !^/wp-
RewriteCond %{REQUEST_URI} !^/static
RewriteRule ^(.*)$ http://127.0.0.1:8000/$1 [P,L]

# Proxy /static to Frontend
RewriteRule ^static/(.*)$ http://127.0.0.1:8000/static/$1 [P,L]
```

4. **Save** και **Restart OpenLiteSpeed**:

```bash
systemctl restart lsws
```

### **3.3 Alternative: Context-Based Proxy (Προτιμότερο)**

Αν τα Rewrite Rules δεν δουλεύουν, χρησιμοποίησε contexts:

```bash
# Edit vhost configuration
nano /usr/local/lsws/conf/vhosts/veriaguide.gr/vhost.conf
```

Πρόσθεσε πριν το `vhssl`:

```
# External App - FastAPI Frontend
extprocessor frontend_proxy {
  type                    proxy
  address                 http://127.0.0.1:8000
  maxConns                100
  pcKeepAliveTimeout      60
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}

# Context για Root (Frontend)
context / {
  type                    proxy
  handler                 frontend_proxy
  addDefaultCharset       off
}

# Context για Static Files
context /static {
  type                    proxy
  handler                 frontend_proxy
  addDefaultCharset       off
}
```

Restart:
```bash
systemctl restart lsws
```

---

## 📝 ΦΑΣΗ 4: Testing & Verification

### **4.1 Test WordPress**

```bash
# Test REST API
curl -s https://veriaguide.gr/wp-json/wp/v2/posts | jq .

# Test Admin
curl -I https://veriaguide.gr/wp-admin/
```

✅ **Expected**: 200 OK ή 302 Redirect

### **4.2 Test Frontend**

```bash
# Test homepage
curl -s https://veriaguide.gr/ | head -50

# Test specific route
curl -I https://veriaguide.gr/restaurants
```

✅ **Expected**: HTML response από FastAPI

### **4.3 Test Redis**

```bash
# Connect to Redis
docker exec -it veriaguide_redis redis-cli

# Inside redis-cli:
PING
# Should return: PONG

KEYS *
# Should show cached keys

EXIT
```

### **4.4 Browser Testing**

1. **Homepage**: `https://veriaguide.gr/` → FastAPI frontend
2. **WordPress Admin**: `https://veriaguide.gr/wp-admin/` → WordPress dashboard
3. **API Test**: `https://veriaguide.gr/wp-json/wp/v2/restaurants` → JSON response
4. **Category Page**: `https://veriaguide.gr/restaurants` → Frontend με data από WordPress

---

## 📝 ΦΑΣΗ 5: Import Content

### **5.1 Import ACF Fields**

Μέσω WordPress Admin:

1. **Tools** → **Import** → **WordPress**
2. Ανέβασε: `$WP_DOCUMENT_ROOT/data/acf-export-2025-09-15.json`
3. Click **Import**

Ή μέσω SSH (native WordPress, χωρίς Docker container):

```bash
cd $WP_DOCUMENT_ROOT/data

# Run ACF import για hotels
php $WP_DOCUMENT_ROOT/data/hotels_veria/import_acf_fields.php

# Run ACF import για cafes
php $WP_DOCUMENT_ROOT/data/cafe_veria/import_acf_fields_cafes.php

# Run ACF import για restaurants
php $WP_DOCUMENT_ROOT/data/restaurants_veria/import_acf_fields_restaurants.php
```

### **5.2 Import CSV Data**

```bash
cd $WP_DOCUMENT_ROOT/data

# Import hotels
php $WP_DOCUMENT_ROOT/data/hotels_veria/import_accommodations.php

# Import cafes
php $WP_DOCUMENT_ROOT/data/cafe_veria/import_cafes.php

# Import restaurants
php $WP_DOCUMENT_ROOT/data/restaurants_veria/import_restaurants.php
```

### **5.3 Upload Media/Photos**

```bash
# From LOCAL machine
scp -r /path/to/your/photos/* root@***REMOVED***:$WP_DOCUMENT_ROOT/wp-content/uploads/

# Set permissions
ssh root@***REMOVED*** 'chown -R nobody:nobody $WP_DOCUMENT_ROOT/wp-content/uploads/'
```

---

## 🔍 Troubleshooting

### **Problem: Frontend δεν φορτώνει**

```bash
# Check logs
docker logs veriaguide_frontend

# Restart
docker restart veriaguide_frontend
```

### **Problem: WordPress REST API δεν λειτουργεί**

1. **Settings** → **Permalinks** → Save (ξαναφρέσκαρε το .htaccess)
2. Έλεγξε ότι τα Custom Post Types έχουν REST API enabled

### **Problem: 502 Bad Gateway**

```bash
# Check if containers are running
docker ps

# Restart OpenLiteSpeed
systemctl restart lsws

# Check ports
netstat -tlnp | grep -E '8000|6379'
```

### **Problem: Database Connection Error**

```bash
# Check WordPress wp-config.php
cat $WP_DOCUMENT_ROOT/wp-config.php | grep DB_

# Should match your database credentials from Step 1.1
```

---

## ✅ Final Checklist

- [ ] WordPress εγκαταστάθηκε και λειτουργεί
- [ ] WordPress Admin accessible (`/wp-admin/`)
- [ ] WordPress REST API λειτουργεί (`/wp-json/`)
- [ ] Custom Post Types δημιουργήθηκαν
- [ ] ACF Fields imported
- [ ] Docker containers running (Redis, Frontend)
- [ ] Frontend accessible (homepage loads)
- [ ] OpenLiteSpeed proxy configuration working
- [ ] Content imported (hotels, cafes, restaurants)
- [ ] Photos/media uploaded

---

## 📞 Σημαντικά Endpoints

- **Frontend Homepage**: https://veriaguide.gr/
- **WordPress Admin**: https://veriaguide.gr/wp-admin/
- **WordPress API**: https://veriaguide.gr/wp-json/wp/v2/
- **Restaurants**: https://veriaguide.gr/restaurants
- **Museums**: https://veriaguide.gr/museums
- **Accommodations**: https://veriaguide.gr/accommodations

---

## 🔐 Credentials Reference

Κράτησε αυτά τα credentials:

```
=== WordPress Database ===
DB_NAME: veria_wordpress
DB_USER: veria_wpuser
DB_PASS: [το password που έβαλες]
DB_HOST: localhost

=== WordPress Admin ===
Username: admin
Password: [το password που έβαλες]
URL: https://veriaguide.gr/wp-admin/

=== Docker ===
Redis: redis://veriaguide_redis:6379/0
Frontend: http://localhost:8000

=== SSH ===
Host: ***REMOVED***
User: root
Port: 22
```

---

## 🎯 Key Differences από την προηγούμενη προσπάθεια

1. ✅ **WordPress εγκαθίσταται ΠΡΩΤΑ** (χειροκίνητα, stable)
2. ✅ **Δεν χρησιμοποιούμε WordPress Docker container** (conflict με existing installation)
3. ✅ **Frontend μόνο του με Redis** (απλοποίηση)
4. ✅ **OpenLiteSpeed proxy** μόνο για το Frontend, WordPress μένει native
5. ✅ **Ένα project root**: Όλα (WordPress, Frontend, Docker, Data) κάτω από `$WP_DOCUMENT_ROOT/`

---

Καλή τύχη! 🚀
