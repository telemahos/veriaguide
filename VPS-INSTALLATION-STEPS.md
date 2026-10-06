Τ# VeriaGuide - VPS Installation Steps

Αυτές είναι οι εντολές που πρέπει να τρέξεις **ΣΤΟΝ VPS SERVER** (AlmaLinux 9.8 με CyberPanel).

## Βήμα 1: Σύνδεση στον VPS

Από το **local μηχάνημα** σου, συνδέσου στον server:

```bash
ssh -p "$SSH_PORT" "$VPS_USER@$VPS_HOST"
```‚

---

## Βήμα 2: Γίνε root user

```bash
sudo su -
```

---

## Βήμα 3: Εγκατάσταση Docker

```bash
# Update system
dnf update -y

# Install Docker
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io

# Start Docker
systemctl start docker
systemctl enable docker

# Verify
docker --version
```

---

## Βήμα 4: Εγκατάσταση Docker Compose

```bash
# Download latest version
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
chmod +x /usr/local/bin/docker-compose

# Create symlink
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify
docker-compose --version
```

---

## Βήμα 5: Εγκατάσταση Python 3.11

```bash
# Install Python 3.11
dnf install -y python3.11 python3.11-pip python3.11-devel

# Verify
python3.11 --version
```

---

## Βήμα 6: Προσθήκη χρήστη στο Docker group

```bash
# Add users to docker group
usermod -aG docker "$VPS_USER"
usermod -aG docker cyberpanel

# You may need to log out and back in for this to take effect
```

---

## Βήμα 7: Ρύθμιση Firewall

```bash
# Allow Docker ports
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=8091/tcp
firewall-cmd --permanent --add-port=8443/tcp
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload

# Check status
firewall-cmd --list-ports
```

---

## Βήμα 8: Fix Docker iptables issues

```bash
# Restart Docker to fix iptables
systemctl restart docker

# Clean up old networks
docker network prune -f

# If still issues, try:
iptables -F
iptables -X
systemctl restart docker
```

---

## Βήμα 9: Δημιουργία directories

```bash
# Go to application directory
cd $WP_DOCUMENT_ROOT

# Create necessary directories
mkdir -p frontend/app
mkdir -p frontend/static
mkdir -p frontend/templates
mkdir -p frontend/logs
mkdir -p data/submissions
mkdir -p data/contributions
mkdir -p mysql-data
mkdir -p traefik

# Set permissions
chown -R "$VPS_USER:$VPS_USER" $WP_DOCUMENT_ROOT
chmod -R 755 $WP_DOCUMENT_ROOT
```

---

## Βήμα 10: Έξοδος από root und Anmeldung als `$VPS_USER`

```bash
# Exit root
exit

# Verify you are $VPS_USER
whoami

# Go to app directory
cd $WP_DOCUMENT_ROOT
```

---

## Βήμα 11: Δημιουργία .env.production.docker

```bash
# Create environment file
nano .env.production.docker
```

Πρόσθεσε τα εξής (αντικατέστησε με τα δικά σου passwords):

```env
# Production Environment Configuration
ENVIRONMENT=production

# Database Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_DATABASE=veriaguide_db
MYSQL_USER=wp_user
MYSQL_PASSWORD=your_secure_db_password_here

# WordPress Configuration
WP_API_URL=http://wordpress/wp-json

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_DEFAULT_TTL=1800

# Application Configuration
SECRET_KEY=your_secure_secret_key_here_minimum_50_characters_long
ALLOWED_HOSTS=veriaguide.gr,www.veriaguide.gr
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Admin API Key
ADMIN_API_KEY=your_secure_admin_api_key_here

# Site Configuration
SITE_URL=https://veriaguide.gr
DEBUG=False
```

Πάτησε `Ctrl+X`, μετά `Y`, μετά `Enter` για να αποθηκεύσεις.

---

## Βήμα 12: Δημιουργία Traefik configuration

```bash
# Create traefik config
nano traefik/tls.yml
```

Πρόσθεσε:

```yaml
tls:
  certificates:
    - certFile: /etc/traefik/certs/fullchain.pem
      keyFile: /etc/traefik/certs/privkey.pem
```

Αποθήκευσε με `Ctrl+X`, `Y`, `Enter`.

---

## Βήμα 13: Έλεγχος SSL Certificates

```bash
# Check if SSL certs exist
ls -la /etc/letsencrypt/live/veriaguide.gr/
```

Πρέπει να δεις:
- `fullchain.pem`
- `privkey.pem`

Αν δεν υπάρχουν, θα πρέπει να τα δημιουργήσεις με CyberPanel ή certbot.

---

## Βήμα 14: Τώρα πρέπει να ανεβάσεις τα αρχεία από το local μηχάνημα

**ΑΠΟ ΤΟ LOCAL ΜΗΧΑΝΗΜΑ ΣΟΥ** (όχι από τον VPS), τρέξε:

```bash
# Make script executable
chmod +x full-deploy-to-vps.sh

# Run deployment
./full-deploy-to-vps.sh
```

---

## Βήμα 15: Επιστροφή στον VPS - Έλεγχος αρχείων

```bash
# Back on VPS
cd $WP_DOCUMENT_ROOT

# Check if files exist
ls -la

# Should see:
# - docker-compose.prod.yml
# - frontend/
# - data/
# - etc.
```

---

## Βήμα 16: Symlink για .env file

```bash
# Link production env file
ln -sf .env.production.docker .env

# Verify
ls -la .env
```

---

## Βήμα 17: Εκκίνηση Docker Containers

```bash
# Make sure you're in the right directory
cd $WP_DOCUMENT_ROOT

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Βήμα 18: Έλεγχος εάν τρέχει

```bash
# Check if containers are running
docker ps

# Test frontend
curl http://localhost:8000/health

# Test WordPress
curl http://localhost:8091/wp-json/
```

---

## Χρήσιμες Εντολές

### Restart services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Stop all
```bash
docker-compose -f docker-compose.prod.yml down
```

### Rebuild frontend
```bash
docker-compose -f docker-compose.prod.yml up -d --build frontend
```

### View logs
```bash
# All logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Clear cache
```bash
# Clear Redis cache
docker exec veriaguide_redis_prod redis-cli FLUSHALL
```

---

## Troubleshooting

### Αν δεις "network error":
```bash
docker network prune -f
systemctl restart docker
docker-compose -f docker-compose.prod.yml up -d
```

### Αν δεις "permission denied":
```bash
sudo chown -R "$VPS_USER:$VPS_USER" $WP_DOCUMENT_ROOT
```

### Αν το WordPress δεν μπορεί να γράψει αρχεία:
```bash
docker exec wp_veriaguide_prod chown -R www-data:www-data /var/www/html/wp-content
```

---

## Επόμενα Βήματα μετά την εγκατάσταση

1. Ρύθμισε το OpenLiteSpeed να κάνει proxy το port 8000
2. Άνοιξε το WordPress Admin και ελέγχα τα plugins
3. Test όλες τις σελίδες: /restaurants, /museums, /accommodations, κτλ.
4. Test τα submissions: /submit και /contribute
5. Warm το cache: `curl -X POST http://localhost:8000/admin/warm-cache -H "X-API-Key: YOUR_ADMIN_KEY"`

---

Αυτό είναι! 🚀
