# VPS Deployment Fix - Accommodations Listings Not Showing

## Root Cause
Two issues:
1. **Old Docker image**: VPS running old code with template extending `base/base.html` instead of `base/layout.html`
2. **Traefik Docker API issue**: Docker daemon API version mismatch prevents Traefik from discovering services

## Solution
1. Rebuild frontend with latest code
2. Disable Traefik Docker provider (use file-based routing instead)
3. Expose frontend directly on port 8000

## Steps on VPS

### 1. SSH into your VPS
```bash
ssh root@srv516119
cd /home/veriaguide.gr/public_html
```

### 2. Stop all containers
```bash
docker compose -f docker-compose.prod.yml down
```

### 3. Rebuild and restart
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### 4. Verify it's working
```bash
# Wait 30 seconds for services to start
sleep 30

# Check status
docker compose -f docker-compose.prod.yml ps

# Test accommodations directly on port 8000
curl http://localhost:8000/accommodations | head -50

# Test via Traefik on port 8091
curl -k https://localhost:8091/accommodations | head -50

# Check logs
docker compose -f docker-compose.prod.yml logs frontend | tail -50
docker compose -f docker-compose.prod.yml logs traefik | tail -50
```

### 5. Configure OpenLiteSpeed to proxy to port 8000
In your OpenLiteSpeed config, make sure it proxies requests to `http://localhost:8000` instead of through Traefik.

## What Changed
- **Traefik**: Disabled Docker provider, now uses file-based routing (`traefik/frontend.yml`)
- **Frontend**: Exposed on port 8000 directly
- **Routing**: Traefik routes `veriaguide.gr` → `http://veriaguide_frontend_prod:8000`
- **Code**: Latest templates with correct inheritance and data access

## Expected Result
- ✅ Frontend container runs without errors
- ✅ `/accommodations` returns full HTML with 25 listings on port 8000
- ✅ Traefik routes traffic correctly on port 8091
- ✅ External access via www.veriaguide.gr/accommodations works
- ✅ Each listing shows: title, address, amenities, rating, price range
- ✅ Favorites functionality works
- ✅ Distance to city center calculates correctly

## Troubleshooting

### If Traefik still shows errors:
```bash
# Check Traefik logs
docker compose -f docker-compose.prod.yml logs traefik | grep -i error

# Restart Traefik
docker compose -f docker-compose.prod.yml restart traefik
```

### If frontend doesn't start:
```bash
# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend | tail -100

# Verify WordPress is accessible
curl http://localhost:8086/wp-json/wp/v2/accommodations | head -20
```

### If accommodations still show fallback data:
```bash
# Check if WordPress has accommodation data
curl http://localhost:8086/wp-json/wp/v2/accommodations?per_page=1

# Check Redis connection
docker compose -f docker-compose.prod.yml logs redis | tail -20
```
