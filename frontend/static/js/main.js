/**
 * VeriaGuide - Main JavaScript
 * A tourism directory website for Veria, Greece
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    initializeTooltips();
    
    // Initialize favorite buttons 
    initializeFavoriteButtons();
    
    // Initialize lazy loading for images
    initializeLazyLoading();
    
    // Initialize mobile menu behavior
    initializeMobileMenu();
    
    // Initialize scroll animations
    initializeScrollAnimations();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Favorite button functionality
 */
function initializeFavoriteButtons() {
    const favBtns = document.querySelectorAll('.add-favorite');
    
    favBtns.forEach(btn => {
        // Check if already in favorites
        const isFavorited = checkIfFavorite(btn.dataset.id);
        if (isFavorited) {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.classList.remove('far');
                icon.classList.add('fas');
            }
        }
        
        // Add click event listener
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const itemId = this.dataset.id;
            const itemType = this.dataset.type;
            const itemTitle = this.dataset.title;
            const itemImage = this.dataset.image;
            
            // Send AJAX request to add to favorites
            fetch('/favorites/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `item_id=${itemId}&item_type=${itemType}&item_title=${encodeURIComponent(itemTitle)}&item_image=${encodeURIComponent(itemImage)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update heart icon
                    const icon = this.querySelector('i');
                    if (icon) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                    }
                    
                    // Update button text if it's the detail page button
                    if (this.classList.contains('btn-danger')) {
                        this.innerHTML = `<i class="fas fa-heart"></i> Added to Favorites`;
                    }
                    
                    // Update favorite count in header
                    const favCount = document.querySelector('.badge');
                    if (favCount) {
                        favCount.textContent = data.favorites.length;
                    }
                    
                    // Show notification
                    showNotification('Added to favorites!', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error adding to favorites. Please try again.', 'error');
            });
        });
    });
}

/**
 * Check if an item is already in favorites
 */
function checkIfFavorite(itemId) {
    // In a real app, this would check against actual favorites storage
    // For now, we'll just return false
    return false;
}

/**
 * Initialize lazy loading for images
 */
function initializeLazyLoading() {
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports native lazy loading
        lazyImages.forEach(img => {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    } else {
        // Browser doesn't support native lazy loading
        // Implement IntersectionObserver or other methods
        // This is a simplified version
        lazyImages.forEach(img => {
            const src = img.getAttribute('data-src');
            if (src) {
                img.setAttribute('src', src);
            }
        });
    }
}

/**
 * Initialize mobile menu behavior
 */
function initializeMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navbarToggler.contains(event.target) && !navbarCollapse.contains(event.target) && navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Initialize scroll animations
 */
function initializeScrollAnimations() {
    const animatedElements = document.querySelectorAll('.fade-in, .zoom-in');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(el => {
            observer.observe(el);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedElements.forEach(el => {
            el.classList.add('active');
        });
    }
}

/**
 * Helper function to get marker icon based on location type
 */
function getMarkerIcon(type) {
    const iconBase = '/static/img/markers/';
    const icons = {
        'museum': iconBase + 'museum.png',
        'attraction': iconBase + 'attraction.png',
        'archaeological_site': iconBase + 'archaeological.png',
        'religious_site': iconBase + 'religious.png',
        'hiking_trail': iconBase + 'hiking.png',
        'restaurant': iconBase + 'restaurant.png',
        'cafe': iconBase + 'cafe.png',
        'bar_club': iconBase + 'bar.png',
        'historical_site': iconBase + 'historical.png'
    };
    
    return icons[type] || null;
} 
async function init() {
  await customElements.whenDefined('gmp-map');

  const map = document.querySelector('gmp-map');
  const marker = document.querySelector('gmp-advanced-marker');
  const placePicker = document.querySelector('gmpx-place-picker');
  const infowindow = new google.maps.InfoWindow();

  map.innerMap.setOptions({
    mapTypeControl: false
  });

  placePicker.addEventListener('gmpx-placechange', () => {
    const place = placePicker.value;

    if (!place.location) {
      window.alert(
        "No details available for input: '" + place.name + "'"
      );
      infowindow.close();
      marker.position = null;
      return;
    }

    if (place.viewport) {
      map.innerMap.fitBounds(place.viewport);
    } else {
      map.center = place.location;
      map.zoom = 17;
    }

    marker.position = place.location;
    infowindow.setContent(
      `<strong>${place.displayName}</strong><br>
       <span>${place.formattedAddress}</span>
    `);
    infowindow.open(map.innerMap, marker);
  });
}

document.addEventListener('DOMContentLoaded', init);
/**
 * Initialize Google Map
 */
function initMap() {
    // This function will be called when the Google Maps API is loaded
}