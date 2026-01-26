# Cache Warming Guide

## Τι είναι το Cache Warming;

Το Cache Warming είναι η διαδικασία προφόρτωσης δημοφιλούς περιεχομένου στο Redis cache κατά την εκκίνηση της εφαρμογής. Αυτό βελτιώνει την απόδοση γιατί:

- Οι πρώτοι χρήστες δεν περιμένουν για API calls στο WordPress
- Μειώνεται το φορτίο στο WordPress backend
- Βελτιώνεται η συνολική ταχύτητα απόκρισης

## Αυτόματο Cache Warming

Η εφαρμογή κάνει αυτόματα cache warming κατά την εκκίνηση:

```bash
# Όταν ξεκινάει η εφαρμογή
docker-compose up

# Θα δεις στα logs:
# 🔥 Starting cache warming process...
# ✓ Warmed museum: 3 items
# ✓ Warmed archaeological_site: 5 items
# ✓ Warmed religious_site: 65 items
# ...
# ✅ Cache warming completed successfully!
```

## Χειροκίνητο Cache Warming

### Χρήση του Script

```bash
# Warm όλα τα caches
python frontend/scripts/warm_cache.py warm

# Warm συγκεκριμένο post type
python frontend/scripts/warm_cache.py warm --post-type restaurant

# Έλεγχος status
python frontend/scripts/warm_cache.py status

# Invalidate και rewarm συγκεκριμένο post type
python frontend/scripts/warm_cache.py invalidate --post-type cafe
```

### Χρήση API Endpoints

Χρειάζεσαι το `ADMIN_API_KEY` για authentication:

```bash
# Set το API key
export ADMIN_API_KEY="VG_admin_api_key_secure_2025"

# Warm όλα τα caches
curl -X POST http://localhost:8000/admin/warm-cache \
  -H "X-API-Key: $ADMIN_API_KEY"

# Warm συγκεκριμένο post type
curl -X POST http://localhost:8000/admin/warm-cache/restaurant \
  -H "X-API-Key: $ADMIN_API_KEY"

# Invalidate και rewarm
curl -X POST http://localhost:8000/admin/invalidate-and-rewarm/cafe \
  -H "X-API-Key: $ADMIN_API_KEY"

# Έλεγχος status
curl http://localhost:8000/admin/cache-warming-status \
  -H "X-API-Key: $ADMIN_API_KEY"
```

## Πότε να κάνεις Manual Cache Warming

### 1. Μετά από Content Updates στο WordPress

Όταν προσθέτεις ή επεξεργάζεσαι περιεχόμενο στο WordPress:

```bash
# Invalidate και rewarm το συγκεκριμένο post type
python frontend/scripts/warm_cache.py invalidate --post-type restaurant
```

### 2. Μετά από Cache Clear

Αν έχεις κάνει clear το cache:

```bash
# Warm ξανά όλα τα caches
python frontend/scripts/warm_cache.py warm
```

### 3. Για Testing

Για να δοκιμάσεις την απόδοση με warm cache:

```bash
# Warm τα caches πριν το testing
python frontend/scripts/warm_cache.py warm
```

## Available Post Types

Τα post types που υποστηρίζονται:

- `museum` - Μουσεία
- `archaeological_site` - Αρχαιολογικοί χώροι
- `religious_site` - Θρησκευτικά μνημεία
- `restaurant` - Εστιατόρια
- `cafe` - Καφετέριες
- `accommodation` - Καταλύματα
- `ski_resort` - Χιονοδρομικά κέντρα

## Monitoring

### Έλεγχος Cache Status

```bash
# Δες τι είναι cached
python frontend/scripts/warm_cache.py status

# Output:
# 📊 Checking cache warming status...
# ✅ Cache Status:
#    Total cached items: 296
#    Cached post types:
#       - museum: 2 cache keys
#       - archaeological_site: 2 cache keys
#       - religious_site: 2 cache keys
#       ...
```

### Έλεγχος Redis Info

```bash
# Δες γενικές πληροφορίες για το cache
curl http://localhost:8000/admin/cache-info \
  -H "X-API-Key: $ADMIN_API_KEY"
```

## Troubleshooting

### Cache Warming Αποτυγχάνει

1. **Έλεγξε αν το Redis τρέχει:**
   ```bash
   docker-compose ps redis
   ```

2. **Έλεγξε τα logs:**
   ```bash
   docker logs veriaguide_frontend | grep "cache warming"
   ```

3. **Έλεγξε το WordPress:**
   ```bash
   curl http://localhost:8086/wp-json/wp/v2
   ```

### Αργό Cache Warming

Το cache warming μπορεί να πάρει 10-30 δευτερόλεπτα ανάλογα με:
- Τον αριθμό των items
- Την ταχύτητα του WordPress
- Το network latency

Αυτό είναι φυσιολογικό και γίνεται στο background χωρίς να επηρεάζει την εφαρμογή.

### API Key Errors

Αν παίρνεις 401 Unauthorized:

```bash
# Βεβαιώσου ότι το API key είναι σωστό
echo $ADMIN_API_KEY

# Ή πέρασέ το απευθείας
python frontend/scripts/warm_cache.py warm --api-key "your_key_here"
```

## Best Practices

1. **Automatic Warming on Startup**: Ενεργοποιημένο by default ✅
2. **Manual Warming After Updates**: Κάνε invalidate & rewarm μετά από content changes
3. **Monitor Cache Status**: Έλεγξε περιοδικά το cache status
4. **Use Specific Post Types**: Warm μόνο αυτό που χρειάζεται για ταχύτερη ανανέωση

## Integration με CI/CD

Για production deployments:

```bash
# Στο deployment script σου
docker-compose up -d

# Περίμενε να ξεκινήσει η εφαρμογή
sleep 10

# Warm το cache
python frontend/scripts/warm_cache.py warm --url https://veriaguide.gr

# Έλεγξε το status
python frontend/scripts/warm_cache.py status --url https://veriaguide.gr
```

## Performance Metrics

Με cache warming:
- **First Request**: ~50-100ms (από cache)
- **Without Cache**: ~500-1000ms (API call στο WordPress)

**Improvement**: 5-10x ταχύτερο! 🚀
