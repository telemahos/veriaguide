# OpenStreetMap Migration Guide

## Overview
Μετάβαση από Google Maps σε OpenStreetMap (Leaflet.js) για το VeriaGuide project.

## Πλεονεκτήματα

- ✅ **Δωρεάν & Open Source** - Χωρίς API keys, χωρίς κόστος
- ✅ **Καλύτερα δεδομένα για Ελλάδα** - Πιο λεπτομερής χαρτογράφηση
- ✅ **Privacy-friendly** - Δεν στέλνει δεδομένα σε Google
- ✅ **Πλήρης έλεγχος styling**

## Αλλαγές που έγιναν

### 1. Base Layout (`frontend/templates/base/layout.html`)
- ✅ Αφαιρέθηκε το Google Maps API script
- ✅ Προστέθηκε Leaflet CSS & JS (v1.9.4)

```html
<!-- Leaflet CSS & JS for OpenStreetMap -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### 2. Religious Sites Map (`frontend/templates/religious_sites/map-listings.html`)
- ✅ Μετατράπηκε πλήρως σε Leaflet
- ✅ Όλες οι λειτουργίες διατηρήθηκαν:
  - Markers με popups
  - Click events
  - Highlight listings
  - Pan to marker
  - Fit bounds

## Templates που χρειάζονται ενημέρωση

### Υψηλής Προτεραιότητας
- [ ] `frontend/templates/base/map.html` - Κύριος χάρτης
- [ ] `frontend/templates/search/results.html` - Αποτελέσματα αναζήτησης

### Detail Pages
- [ ] `frontend/templates/museums/detail.html`
- [ ] `frontend/templates/religious_sites/detail.html`
- [ ] `frontend/templates/restaurants/detail.html`
- [ ] `frontend/templates/accommodations/detail.html`
- [ ] `frontend/templates/hiking_trails/detail.html`
- [ ] `frontend/templates/ski_resorts/detail.html`

### List Pages με Maps
- [ ] `frontend/templates/museums/list.html`
- [ ] `frontend/templates/hiking_trails/list.html`
- [ ] `frontend/templates/ski_resorts/list.html`

## Leaflet API Basics

### Δημιουργία χάρτη
```javascript
// Google Maps
const map = new google.maps.Map(element, {
    center: { lat: 40.5246, lng: 22.2022 },
    zoom: 13
});

// Leaflet
const map = L.map(element).setView([40.5246, 22.2022], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);
```

### Markers
```javascript
// Google Maps
const marker = new google.maps.Marker({
    position: { lat: 40.5246, lng: 22.2022 },
    map: map,
    title: 'Title'
});

// Leaflet
const marker = L.marker([40.5246, 22.2022]).addTo(map);
marker.bindPopup('Content');
```

### Popups/InfoWindows
```javascript
// Google Maps
const infoWindow = new google.maps.InfoWindow({ content: 'Content' });
marker.addListener('click', () => infoWindow.open(map, marker));

// Leaflet
marker.bindPopup('Content');
marker.on('click', () => marker.openPopup());
```

### Bounds
```javascript
// Google Maps
const bounds = new google.maps.LatLngBounds();
bounds.extend({ lat: 40.5246, lng: 22.2022 });
map.fitBounds(bounds);

// Leaflet
const bounds = [[40.5246, 22.2022], [40.5300, 22.2100]];
map.fitBounds(bounds);
```

## Custom Markers

### Χρωματιστά Icons
```javascript
// Δημιουργία custom icon με χρώμα
const customIcon = L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: #0d6efd; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
});

const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
```

## Tile Providers

### OpenStreetMap (Default)
```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
}).addTo(map);
```

### Alternatives
```javascript
// CartoDB Positron (light theme)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © CartoDB'
}).addTo(map);

// CartoDB Dark Matter (dark theme)
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © CartoDB'
}).addTo(map);
```

## Testing

Μετά την ενημέρωση κάθε template, δοκίμασε:
1. ✅ Φόρτωση χάρτη
2. ✅ Εμφάνιση markers
3. ✅ Click σε marker (popup)
4. ✅ Zoom & Pan
5. ✅ Fit bounds με πολλά markers
6. ✅ Mobile responsiveness

## Environment Variables

Μπορείς να αφαιρέσεις το `GOOGLE_MAPS_API_KEY` από:
- `.env`
- `.env.example`
- `docker-compose.yml`
- `frontend/app/config.py`

## Επόμενα Βήματα

1. Ενημέρωση υπόλοιπων templates
2. Αφαίρεση Google Maps API key
3. Testing σε όλες τις σελίδες
4. Ενημέρωση documentation

## Resources

- [Leaflet Documentation](https://leafletjs.com/)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [Leaflet Plugins](https://leafletjs.com/plugins.html)
