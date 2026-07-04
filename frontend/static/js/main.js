/**
 * VeriaGuide - Main JavaScript
 * A tourism directory website for Veria, Greece
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    initializeTooltips();
    
    // Initialize navigation functionality
    initializeNavigation();
    
    // Initialize footer functionality
    initializeFooter();
    
    // Initialize favorite buttons 
    initializeFavoriteButtons();
    
    // Initialize lazy loading for images
    initializeLazyLoading();
    
    // Initialize image placeholder system
    initializeImagePlaceholders();
    
    // Initialize lazy loading with placeholders
    initializeLazyLoadingWithPlaceholders();
    
    // Initialize enhanced image handling
    initializeEnhancedImageHandling();
    
    // Preload placeholder images
    preloadPlaceholderImages();
    
    // Initialize mobile menu behavior (legacy - now handled in initializeNavigation)
    initializeMobileMenu();
    
    // Initialize scroll animations
    initializeScrollAnimations();
    
    // Initialize hero search form
    initializeHeroSearchForm();

    // Detail page galleries (thumbnail strip + modal sync)
    initializeDetailGalleries();
    
    // Initialize destination cards
    initializeDestinationCards();
    
    // Initialize search functionality
    initializeSearchFunctionality();
    
    // Initialize results per page selector
    initializeResultsPerPage();
    
    // Initialize contact form functionality
    initializeContactForm();
    
    // Sync favorites on page load (primary sync)
    syncFavoritesOnLoad();
    
    // Also sync favorites from server periodically (backup sync)
    setTimeout(syncFavoritesFromServer, 2000);
    
    // Set up periodic sync every 30 seconds to keep favorites in sync
    setInterval(syncFavoritesFromServer, 30000);
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
    console.log('Found favorite buttons:', favBtns.length);
    
    favBtns.forEach(btn => {
        // Check if already in favorites
        const isFavorited = checkIfFavorite(btn.dataset.id);
        if (isFavorited) {
            updateFavoriteButtonState(btn, true);
        }
        
        // Add click event listener
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Favorite button clicked:', this.dataset);
            
            const itemId = this.dataset.id;
            const itemType = this.dataset.type;
            const itemTitle = this.dataset.title;
            const itemImage = this.dataset.image;
            const isCurrentlyFavorited = checkIfFavorite(itemId);
            
            console.log('Is currently favorited:', isCurrentlyFavorited);
            
            if (isCurrentlyFavorited) {
                // Remove from favorites
                removeFavoriteItem(itemId, this);
            } else {
                // Add to favorites
                addFavoriteItem(itemId, itemType, itemTitle, itemImage, this);
            }
        });
    });
}

/**
 * Add item to favorites
 */
function addFavoriteItem(itemId, itemType, itemTitle, itemImage, buttonElement) {
    // Send AJAX request to add to favorites
    fetch('/favorites/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `item_id=${itemId}&item_type=${itemType}&item_title=${encodeURIComponent(itemTitle)}&item_image=${encodeURIComponent(itemImage || '')}`
    })
    .then(response => response.json())
    .then(data => {
        console.log('Add favorite response:', data);
        if (data.success) {
            // Update localStorage
            updateLocalStorageFavorites(data.favorites);
            
            // Update button state
            updateFavoriteButtonState(buttonElement, true);
            
            // Update favorite count in header
            updateFavoritesCount(data.favorites.length);
            console.log('Updated favorites count to:', data.favorites.length);
            
            // Show subtle notification
            showNotification('Added to favorites!', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding to favorites. Please try again.', 'error');
    });
}

/**
 * Remove item from favorites
 */
function removeFavoriteItem(itemId, buttonElement) {
    // Send AJAX request to remove from favorites
    fetch('/favorites/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `item_id=${itemId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update localStorage
            updateLocalStorageFavorites(data.favorites);
            
            // Update button state
            updateFavoriteButtonState(buttonElement, false);
            
            // Update favorite count in header
            updateFavoritesCount(data.favorites.length);
            
            // Show notification
            showNotification('Removed from favorites!', 'info');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error removing from favorites. Please try again.', 'error');
    });
}

/**
 * Update favorite button state
 */
function updateFavoriteButtonState(buttonElement, isFavorited) {
    const icon = buttonElement.querySelector('i');
    
    if (isFavorited) {
        if (icon) {
            icon.classList.remove('far');
            icon.classList.add('fas');
        }
        
        // Update button text if it's the detail page button (has btn-outline-danger or btn-danger class)
        if (buttonElement.classList.contains('btn-outline-danger') || buttonElement.classList.contains('btn-danger')) {
            buttonElement.innerHTML = `<i class="fas fa-heart"></i> Remove from Favorites`;
            buttonElement.classList.remove('btn-outline-danger');
            buttonElement.classList.add('btn-danger');
        }
        
        buttonElement.setAttribute('title', 'Remove from favorites');
        
        // Add visual feedback for favorited state
        buttonElement.classList.add('favorited');
    } else {
        if (icon) {
            icon.classList.remove('fas');
            icon.classList.add('far');
        }
        
        // Update button text if it's the detail page button
        if (buttonElement.classList.contains('btn-danger') || buttonElement.classList.contains('btn-outline-danger')) {
            buttonElement.innerHTML = `<i class="far fa-heart"></i> Add to Favorites`;
            buttonElement.classList.remove('btn-danger');
            buttonElement.classList.add('btn-outline-danger');
        }
        
        buttonElement.setAttribute('title', 'Add to favorites');
        
        // Remove visual feedback for favorited state
        buttonElement.classList.remove('favorited');
    }
}

/**
 * Update favorites count in header
 */
function updateFavoritesCount(count) {
    console.log('Updating favorites count to:', count);
    
    const favCountBadge = document.getElementById('favorites-count');
    if (favCountBadge) {
        favCountBadge.textContent = count;
        console.log('Updated badge with ID favorites-count');
    } else {
        console.warn('Badge with ID favorites-count not found');
    }
    
    // Also update any other badges that might exist
    const favCountBadges = document.querySelectorAll('.badge');
    console.log('Found badges:', favCountBadges.length);
    favCountBadges.forEach(badge => {
        if (badge.closest('a[href="/favorites"]')) {
            badge.textContent = count;
            console.log('Updated badge in favorites link');
        }
    });
}

/**
 * Update localStorage with favorites
 */
function updateLocalStorageFavorites(favorites) {
    try {
        localStorage.setItem('veriaguide_favorites', JSON.stringify(favorites));
    } catch (error) {
        console.warn('Could not save favorites to localStorage:', error);
    }
}

/**
 * Get favorites from localStorage
 */
function getLocalStorageFavorites() {
    try {
        const favorites = localStorage.getItem('veriaguide_favorites');
        return favorites ? JSON.parse(favorites) : [];
    } catch (error) {
        console.warn('Could not load favorites from localStorage:', error);
        return [];
    }
}

/**
 * Sync favorites on page load
 */
function syncFavoritesOnLoad() {
    // Get current favorites from server (most reliable method)
    fetch('/favorites')
        .then(response => response.text())
        .then(html => {
            // Parse the HTML to extract favorites
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const favoriteItems = doc.querySelectorAll('[id^="favorite-item-"]');
            
            const favoriteIds = [];
            favoriteItems.forEach(item => {
                const itemId = item.id.replace('favorite-item-', '');
                favoriteIds.push(itemId);
            });
            
            console.log('Server favorites loaded:', favoriteIds);
            
            // Update favorites count in header
            updateFavoritesCount(favoriteIds.length);
            
            // Update all favorite buttons on the page
            const favBtns = document.querySelectorAll('.add-favorite');
            favBtns.forEach(btn => {
                const itemId = btn.dataset.id;
                const isFavorited = favoriteIds.includes(itemId);
                updateFavoriteButtonState(btn, isFavorited);
            });
            
            console.log('Favorites synced from server:', {
                totalCount: favoriteIds.length,
                buttonsUpdated: favBtns.length
            });
        })
        .catch(error => {
            console.warn('Could not sync favorites from server, falling back to local data:', error);
            
            // Fallback to cookie/localStorage method
            const cookieFavorites = getCookieFavorites();
            const localFavorites = getLocalStorageFavorites();
            const favorites = cookieFavorites.length > 0 ? cookieFavorites : localFavorites;
            
            if (cookieFavorites.length > 0) {
                updateLocalStorageFavorites(cookieFavorites);
            }
            
            updateFavoritesCount(favorites.length);
            
            const favBtns = document.querySelectorAll('.add-favorite');
            favBtns.forEach(btn => {
                const itemId = btn.dataset.id;
                const isFavorited = favorites.some(item => item.id === itemId);
                updateFavoriteButtonState(btn, isFavorited);
            });
        });
}

/**
 * Sync favorites from server
 */
function syncFavoritesFromServer() {
    // Make a request to get current favorites from server
    fetch('/favorites')
        .then(response => response.text())
        .then(html => {
            // Parse the HTML to extract favorites
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const favoriteItems = doc.querySelectorAll('[id^="favorite-item-"]');
            
            const favoriteIds = [];
            favoriteItems.forEach(item => {
                const itemId = item.id.replace('favorite-item-', '');
                favoriteIds.push(itemId);
            });
            
            // Update the count
            const currentCount = parseInt(document.getElementById('favorites-count')?.textContent || '0');
            if (favoriteIds.length !== currentCount) {
                updateFavoritesCount(favoriteIds.length);
                console.log('Favorites count updated from server:', favoriteIds.length);
            }
            
            // Update all favorite buttons on the page
            const favBtns = document.querySelectorAll('.add-favorite');
            favBtns.forEach(btn => {
                const itemId = btn.dataset.id;
                const isFavorited = favoriteIds.includes(itemId);
                updateFavoriteButtonState(btn, isFavorited);
            });
            
            console.log('Favorites synced from server (periodic):', {
                totalCount: favoriteIds.length,
                buttonsUpdated: favBtns.length
            });
        })
        .catch(error => {
            console.warn('Could not sync favorites from server:', error);
        });
}

/**
 * Check if an item is already in favorites
 */
function checkIfFavorite(itemId) {
    // First try to get from cookies (server-side source of truth)
    const cookieFavorites = getCookieFavorites();
    if (cookieFavorites.length > 0) {
        return cookieFavorites.some(item => item.id === itemId);
    }
    
    // Fallback to localStorage
    const favorites = getLocalStorageFavorites();
    return favorites.some(item => item.id === itemId);
}

/**
 * Get favorites from cookie
 */
function getCookieFavorites() {
    try {
        const cookieValue = getCookie('veriaguide_favorites');
        return cookieValue ? JSON.parse(decodeURIComponent(cookieValue)) : [];
    } catch (error) {
        console.warn('Could not load favorites from cookie:', error);
        return [];
    }
}

/**
 * Get cookie value by name
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
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
 * Show notification (subtle style)
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.subtle-notification');
    existingNotifications.forEach(n => n.remove());
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `subtle-notification subtle-notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#d4edda' : '#f8d7da'};
        color: ${type === 'success' ? '#155724' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
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

  if (map && map.innerMap) {
    map.innerMap.setOptions({
      mapTypeControl: false
    });
  }

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

/**
 * Detail page gallery: sync main image, thumbnails, and carousel modal
 */
function initializeDetailGalleries() {
    document.querySelectorAll('.detail-gallery').forEach((gallery) => {
        const mainImg = gallery.querySelector('.detail-gallery__main-img');
        const thumbs = gallery.querySelectorAll('.detail-gallery__thumb');
        if (!mainImg || thumbs.length === 0) return;

        const galleryId = gallery.id ? gallery.id.replace('-gallery', '') : '';
        const carousel = galleryId ? document.getElementById(`${galleryId}Carousel`) : null;

        thumbs.forEach((thumb) => {
            thumb.addEventListener('click', () => {
                const fullUrl = thumb.dataset.full;
                const alt = thumb.dataset.alt || '';
                const index = parseInt(thumb.dataset.index, 10);

                if (fullUrl) {
                    mainImg.src = fullUrl;
                    mainImg.alt = alt;
                }

                thumbs.forEach((t) => {
                    t.classList.remove('active');
                    t.removeAttribute('aria-selected');
                });
                thumb.classList.add('active');
                thumb.setAttribute('aria-selected', 'true');

                if (carousel && !Number.isNaN(index)) {
                    carousel.querySelectorAll('.carousel-item').forEach((item, i) => {
                        item.classList.toggle('active', i === index);
                    });
                }
            });
        });

        const modal = gallery.querySelector('.detail-gallery-modal');
        if (modal && carousel) {
            modal.addEventListener('show.bs.modal', () => {
                const activeThumb = gallery.querySelector('.detail-gallery__thumb.active');
                if (!activeThumb) return;
                const index = parseInt(activeThumb.dataset.index, 10);
                if (Number.isNaN(index)) return;
                carousel.querySelectorAll('.carousel-item').forEach((item, i) => {
                    item.classList.toggle('active', i === index);
                });
            });
        }
    });
}

/**
 * Initialize Hero Search Form
 */
function initializeHeroSearchForm() {
    console.log('Initializing hero search form...');
    
    // Initialize search tabs
    initializeSearchTabs();
    
    // Initialize browse categories form
    const heroForm = document.getElementById('heroSearchForm');
    console.log('Hero form found:', !!heroForm);
    
    if (heroForm) {
        heroForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const destinationSelect = document.getElementById('destination');
            const selectedDestination = destinationSelect.value;
            
            // Validate that a destination is selected
            if (!selectedDestination || selectedDestination === '') {
                // Show error message
                showNotification('Please select a category.', 'error');
                destinationSelect.classList.add('is-invalid');
                return;
            }
            
            // Remove invalid class if present
            destinationSelect.classList.remove('is-invalid');
            
            // Add loading state to button
            const submitBtn = heroForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Loading...';
            
            // Navigate to the selected destination
            setTimeout(() => {
                window.location.href = selectedDestination;
            }, 300);
        });
        
        // Remove invalid class when user selects an option
        const destinationSelect = document.getElementById('destination');
        if (destinationSelect) {
            destinationSelect.addEventListener('change', function() {
                this.classList.remove('is-invalid');
            });
        }
    }
    
    // Initialize search everything form
    const searchForm = document.getElementById('heroSearchEverythingForm');
    console.log('Search form found:', !!searchForm);
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('searchQuery');
            const query = searchInput.value.trim();
            
            // Validate search query
            if (!query || query.length < 2) {
                e.preventDefault();
                showNotification('Please enter at least 2 characters to search.', 'error');
                searchInput.focus();
                searchInput.classList.add('is-invalid');
                return;
            }
            
            // Remove invalid class if present
            searchInput.classList.remove('is-invalid');
            
            // Add loading state to button
            const submitBtn = searchForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Searching...';
        });
        
        // Remove invalid class when user types
        const searchInput = document.getElementById('searchQuery');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                this.classList.remove('is-invalid');
            });
        }
    }
}

/**
 * Initialize Search Tabs - SIMPLIFIED VERSION
 */
function initializeSearchTabs() {
    console.log('Initializing search tabs...');
    
    // Wait for DOM to be fully ready
    setTimeout(function() {
        const searchTab = document.querySelector('[data-tab="search"]');
        const browseTab = document.querySelector('[data-tab="browse"]');
        const searchForm = document.querySelector('[data-form="search"]');
        const browseForm = document.querySelector('[data-form="browse"]');
        
        console.log('Elements found:', {
            searchTab: !!searchTab,
            browseTab: !!browseTab,
            searchForm: !!searchForm,
            browseForm: !!browseForm
        });
        
        if (!searchTab || !browseTab || !searchForm || !browseForm) {
            console.error('Missing elements!');
            return;
        }
        
        // Function to switch tabs
        function switchToSearch() {
            console.log('Switching to Search');
            searchTab.classList.add('active');
            browseTab.classList.remove('active');
            searchForm.style.display = 'block';
            browseForm.style.display = 'none';
            searchForm.classList.add('active');
            browseForm.classList.remove('active');
        }
        
        function switchToBrowse() {
            console.log('Switching to Browse');
            browseTab.classList.add('active');
            searchTab.classList.remove('active');
            browseForm.style.display = 'block';
            searchForm.style.display = 'none';
            browseForm.classList.add('active');
            searchForm.classList.remove('active');
        }
        
        // Add event listeners
        searchTab.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            switchToSearch();
        });
        
        browseTab.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            switchToBrowse();
        });
        
        // Initialize with search form visible
        switchToSearch();
        
        console.log('Search tabs initialized successfully');
    }, 100);
}

/**
 * Initialize Destination Cards
 */
function initializeDestinationCards() {
    const destinationCards = document.querySelectorAll('.destination-card.clickable');
    
    if (!destinationCards.length) {
        return;
    }
    
    destinationCards.forEach(card => {
        // Add click event listener
        card.addEventListener('click', function() {
            const destination = this.dataset.destination;
            if (destination) {
                // Add visual feedback
                this.style.transform = 'scale(0.95)';
                
                // Navigate to destination
                setTimeout(() => {
                    window.location.href = destination;
                }, 150);
            }
        });
        
        // Add keyboard support (Enter and Space keys)
        card.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
        
        // Add hover effect enhancement
        card.addEventListener('mouseenter', function() {
            this.style.cursor = 'pointer';
        });
    });
}

/**
 * Initialize Search Functionality
 */
function initializeSearchFunctionality() {
    // Initialize search forms
    initializeSearchForms();
    
    // Initialize search filters
    initializeSearchFilters();
    
    // Initialize search suggestions
    initializeSearchSuggestions();
}

/**
 * Initialize Search Forms
 */
function initializeSearchForms() {
    const searchForms = document.querySelectorAll('form[action="/search"]');
    
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const searchInput = form.querySelector('input[name="q"]');
            
            if (searchInput) {
                const query = searchInput.value.trim();
                
                // Validate search query
                if (!query || query.length < 2) {
                    e.preventDefault();
                    showNotification('Please enter at least 2 characters to search.', 'error');
                    searchInput.focus();
                    return;
                }
                
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
                }
            }
        });
    });
    
    // Handle search input with live suggestions
    const searchInputs = document.querySelectorAll('input[name="q"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    showSearchSuggestions(this, query);
                }, 300);
            } else {
                hideSearchSuggestions(this);
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target)) {
                hideSearchSuggestions(input);
            }
        });
    });
}

/**
 * Initialize Search Filters
 */
function initializeSearchFilters() {
    // Handle category filter changes
    const categoryFilters = document.querySelectorAll('input[name="category-filter"]');
    categoryFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            if (this.checked) {
                // Add loading state
                const filterContainer = this.closest('.form-check');
                if (filterContainer) {
                    filterContainer.style.opacity = '0.7';
                }
                
                // Navigate to filtered results
                setTimeout(() => {
                    window.location.href = this.value;
                }, 200);
            }
        });
    });
    
    // Handle search type dropdown
    const searchTypeSelect = document.getElementById('search-type');
    if (searchTypeSelect) {
        searchTypeSelect.addEventListener('change', function() {
            if (this.value) {
                // Add loading state
                this.disabled = true;
                
                // Navigate to filtered results
                window.location.href = this.value;
            }
        });
    }
}

/**
 * Initialize Search Suggestions
 */
function initializeSearchSuggestions() {
    // Popular search terms
    const popularSearches = [
        'museum', 'byzantine', 'church', 'traditional', 'ancient', 
        'local', 'restaurant', 'cafe', 'accommodation'
    ];
    
    // Store for later use
    window.popularSearches = popularSearches;
}

/**
 * Show Search Suggestions
 */
function showSearchSuggestions(input, query) {
    // Remove existing suggestions
    hideSearchSuggestions(input);
    
    const suggestions = getSearchSuggestions(query);
    
    if (suggestions.length === 0) {
        return;
    }
    
    // Create suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'search-suggestions';
    suggestionsContainer.innerHTML = suggestions.map(suggestion => 
        `<div class="search-suggestion-item" data-query="${suggestion}">
            <i class="fas fa-search me-2"></i>${suggestion}
        </div>`
    ).join('');
    
    // Position suggestions
    const inputRect = input.getBoundingClientRect();
    suggestionsContainer.style.position = 'absolute';
    suggestionsContainer.style.top = (inputRect.bottom + window.scrollY) + 'px';
    suggestionsContainer.style.left = inputRect.left + 'px';
    suggestionsContainer.style.width = inputRect.width + 'px';
    suggestionsContainer.style.zIndex = '1000';
    
    // Add click handlers
    suggestionsContainer.querySelectorAll('.search-suggestion-item').forEach(item => {
        item.addEventListener('click', function() {
            const query = this.dataset.query;
            input.value = query;
            hideSearchSuggestions(input);
            
            // Trigger search
            const form = input.closest('form');
            if (form) {
                form.submit();
            }
        });
    });
    
    // Add to DOM
    document.body.appendChild(suggestionsContainer);
    input.suggestionsContainer = suggestionsContainer;
}

/**
 * Hide Search Suggestions
 */
function hideSearchSuggestions(input) {
    if (input.suggestionsContainer) {
        input.suggestionsContainer.remove();
        input.suggestionsContainer = null;
    }
}

/**
 * Get Search Suggestions
 */
function getSearchSuggestions(query) {
    const popularSearches = window.popularSearches || [];
    const queryLower = query.toLowerCase();
    
    // Filter popular searches that match the query
    const matchingSuggestions = popularSearches.filter(term => 
        term.toLowerCase().includes(queryLower)
    );
    
    // Add exact query if not already included
    if (!matchingSuggestions.includes(query)) {
        matchingSuggestions.unshift(query);
    }
    
    return matchingSuggestions.slice(0, 5); // Limit to 5 suggestions
}

/**
 * Initialize Results Per Page Selector
 */
function initializeResultsPerPage() {
    const resultsPerPageSelect = document.getElementById('resultsPerPage');
    
    if (!resultsPerPageSelect) {
        return;
    }
    
    resultsPerPageSelect.addEventListener('change', function() {
        const perPage = this.value;
        const currentUrl = new URL(window.location.href);
        
        // Update the per_page parameter
        currentUrl.searchParams.set('per_page', perPage);
        
        // Reset to page 1 when changing results per page
        currentUrl.searchParams.set('page', '1');
        
        // Navigate to the new URL
        window.location.href = currentUrl.toString();
    });
}

/*
 * Initialize navigation functionality
 */
function initializeNavigation() {
    // Initialize dropdown menus
    initializeDropdownMenus();
    
    // Initialize mobile menu
    initializeMobileMenuToggle();
    
    // Initialize active page highlighting
    initializeActivePageHighlighting();
}

/**
 * Initialize dropdown menus
 */
function initializeDropdownMenus() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        // Ensure Bootstrap dropdown functionality is working
        toggle.addEventListener('click', function(e) {
            // Bootstrap handles this automatically, but we can add custom behavior here
            console.log('Dropdown clicked:', this.textContent.trim());
        });
    });
    
    // Handle dropdown item clicks
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Only handle navigation for real links (not # links)
            if (href && href !== '#' && !href.startsWith('javascript:')) {
                // Add loading state
                this.style.opacity = '0.7';
                
                // Navigate after short delay for visual feedback
                setTimeout(() => {
                    window.location.href = href;
                }, 100);
            }
        });
    });
}

/**
 * Initialize mobile menu toggle
 */
function initializeMobileMenuToggle() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Handle mobile menu toggle
        navbarToggler.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            if (isExpanded) {
                navbarCollapse.classList.remove('show');
                this.setAttribute('aria-expanded', 'false');
            } else {
                navbarCollapse.classList.add('show');
                this.setAttribute('aria-expanded', 'true');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navbarToggler.contains(event.target) && 
                !navbarCollapse.contains(event.target) && 
                navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
                navbarToggler.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close menu when clicking on nav links (mobile)
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) { // Bootstrap lg breakpoint
                    navbarCollapse.classList.remove('show');
                    navbarToggler.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }
}

/**
 * Initialize active page highlighting
 */
function initializeActivePageHighlighting() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, .dropdown-item');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        if (href && href !== '#') {
            // Exact match for home page
            if (currentPath === '/' && href === '/') {
                link.classList.add('active');
            }
            // Partial match for other pages
            else if (currentPath !== '/' && href !== '/' && currentPath.startsWith(href)) {
                link.classList.add('active');
                
                // Also highlight parent dropdown if this is a dropdown item
                const dropdown = link.closest('.dropdown');
                if (dropdown) {
                    const dropdownToggle = dropdown.querySelector('.dropdown-toggle');
                    if (dropdownToggle) {
                        dropdownToggle.classList.add('active');
                    }
                }
            }
        }
    });
}

/**
 * Initialize footer functionality
 */
function initializeFooter() {
    // Initialize newsletter signup
    initializeNewsletterSignup();
    
    // Initialize social media links
    initializeSocialMediaLinks();
    
    // Initialize app store buttons
    initializeAppStoreButtons();
}

/**
 * Initialize newsletter signup
 */
function initializeNewsletterSignup() {
    const newsletterForm = document.querySelector('.footer-subscribe');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const submitBtn = this.querySelector('button[type="button"]');
            
            if (emailInput && submitBtn) {
                const email = emailInput.value.trim();
                
                // Validate email
                if (!email || !isValidEmail(email)) {
                    showNotification('Please enter a valid email address.', 'error');
                    emailInput.focus();
                    return;
                }
                
                // Add loading state
                const originalBtnContent = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
                // Simulate newsletter signup (replace with actual API call)
                setTimeout(() => {
                    showNotification('Thank you for subscribing to our newsletter!', 'success');
                    emailInput.value = '';
                    
                    // Reset button
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnContent;
                }, 1000);
            }
        });
    }
}

/**
 * Initialize social media links
 */
function initializeSocialMediaLinks() {
    const socialLinks = document.querySelectorAll('.social-links a');
    
    socialLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add analytics tracking here if needed
            console.log('Social media link clicked:', this.href);
        });
    });
}

/**
 * Initialize app store buttons
 */
function initializeAppStoreButtons() {
    const appButtons = document.querySelectorAll('.app-buttons a');
    
    appButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show coming soon message for now
            showNotification('Mobile app coming soon!', 'info');
            
            // In the future, redirect to actual app store links
            // window.open(this.href, '_blank');
        });
    });
}

/**
 * Validate email address
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
/**
 
* Initialize Contact Form Functionality
 */
function initializeContactForm() {
    const contactForm = document.querySelector('form[action="/contact"]');
    
    if (!contactForm) {
        return; // No contact form on this page
    }
    
    console.log('Initializing contact form functionality');
    
    // Get form elements
    const nameField = contactForm.querySelector('#name');
    const emailField = contactForm.querySelector('#email');
    const subjectField = contactForm.querySelector('#subject');
    const messageField = contactForm.querySelector('#message');
    const privacyField = contactForm.querySelector('#privacy');
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    
    // Store original button text
    const originalBtnText = submitBtn.innerHTML;
    
    // Add real-time validation
    if (nameField) {
        nameField.addEventListener('blur', () => validateContactField(nameField, 'name'));
        nameField.addEventListener('input', () => clearFieldError(nameField));
    }
    
    if (emailField) {
        emailField.addEventListener('blur', () => validateContactField(emailField, 'email'));
        emailField.addEventListener('input', () => clearFieldError(emailField));
    }
    
    if (subjectField) {
        subjectField.addEventListener('blur', () => validateContactField(subjectField, 'subject'));
        subjectField.addEventListener('change', () => {
            clearFieldError(subjectField);
            handleSubjectChange(subjectField);
        });
    }
    
    if (messageField) {
        messageField.addEventListener('blur', () => validateContactField(messageField, 'message'));
        messageField.addEventListener('input', () => {
            clearFieldError(messageField);
            updateCharacterCounter(messageField, 5000);
        });
        
        // Initialize character counter
        addCharacterCounter(messageField, 5000);
    }
    
    if (privacyField) {
        privacyField.addEventListener('change', () => validateContactField(privacyField, 'privacy'));
    }
    
    // Handle form submission
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        console.log('Contact form submitted');
        
        // Validate all fields
        const isValid = validateContactForm();
        
        if (!isValid) {
            showNotification('Please fix the errors below and try again.', 'error');
            return;
        }
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Sending Message...';
        
        // Prepare form data
        const formData = new FormData(contactForm);
        
        // Submit form via fetch
        fetch('/contact', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            // Parse response to check for success/error messages
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            const successAlert = doc.querySelector('.alert-success');
            const errorAlert = doc.querySelector('.alert-danger');
            
            if (successAlert) {
                // Success - show success message and reset form
                showNotification('Thank you! Your message has been sent successfully.', 'success');
                contactForm.reset();
                clearAllFieldErrors();
                
                // Scroll to top to show success message
                window.scrollTo({ top: 0, behavior: 'smooth' });
                
                // Update the page content with the success message
                const currentAlerts = document.querySelectorAll('.alert');
                currentAlerts.forEach(alert => alert.remove());
                
                const cardBody = contactForm.closest('.card-body');
                if (cardBody) {
                    const successDiv = document.createElement('div');
                    successDiv.className = 'alert alert-success';
                    successDiv.setAttribute('role', 'alert');
                    successDiv.textContent = successAlert.textContent;
                    cardBody.insertBefore(successDiv, contactForm);
                }
                
            } else if (errorAlert) {
                // Error - show error message
                const errorMessage = errorAlert.textContent.trim();
                showNotification(errorMessage, 'error');
                
                // Update the page content with the error message
                const currentAlerts = document.querySelectorAll('.alert');
                currentAlerts.forEach(alert => alert.remove());
                
                const cardBody = contactForm.closest('.card-body');
                if (cardBody) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger';
                    errorDiv.setAttribute('role', 'alert');
                    errorDiv.textContent = errorMessage;
                    cardBody.insertBefore(errorDiv, contactForm);
                }
                
                // Highlight fields with errors if possible
                highlightFieldsWithErrors(errorMessage);
                
            } else {
                // Unexpected response
                showNotification('An unexpected error occurred. Please try again.', 'error');
            }
        })
        .catch(error => {
            console.error('Contact form submission error:', error);
            showNotification('Network error. Please check your connection and try again.', 'error');
        })
        .finally(() => {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
    });
}

/**
 * Validate entire contact form
 */
function validateContactForm() {
    const nameField = document.querySelector('#name');
    const emailField = document.querySelector('#email');
    const subjectField = document.querySelector('#subject');
    const messageField = document.querySelector('#message');
    const privacyField = document.querySelector('#privacy');
    const customSubjectField = document.querySelector('#customSubject');
    
    let isValid = true;
    
    // Validate each field
    if (nameField && !validateContactField(nameField, 'name')) {
        isValid = false;
    }
    
    if (emailField && !validateContactField(emailField, 'email')) {
        isValid = false;
    }
    
    if (subjectField && !validateContactField(subjectField, 'subject')) {
        isValid = false;
    }
    
    // Validate custom subject if "Other" is selected
    if (subjectField && subjectField.value === 'Other' && customSubjectField && customSubjectField.required) {
        if (!validateContactField(customSubjectField, 'customSubject')) {
            isValid = false;
        }
    }
    
    if (messageField && !validateContactField(messageField, 'message')) {
        isValid = false;
    }
    
    if (privacyField && !validateContactField(privacyField, 'privacy')) {
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate individual contact form field
 */
function validateContactField(field, fieldType) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Clear previous errors
    clearFieldError(field);
    
    switch (fieldType) {
        case 'name':
            if (!value) {
                errorMessage = 'Name is required';
                isValid = false;
            } else if (value.length < 2) {
                errorMessage = 'Name must be at least 2 characters long';
                isValid = false;
            } else if (value.length > 100) {
                errorMessage = 'Name must be less than 100 characters';
                isValid = false;
            } else if (!/^[a-zA-Z\s\-_.,!?()]+$/.test(value)) {
                errorMessage = 'Name contains invalid characters';
                isValid = false;
            }
            break;
            
        case 'email':
            if (!value) {
                errorMessage = 'Email is required';
                isValid = false;
            } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)) {
                errorMessage = 'Please enter a valid email address';
                isValid = false;
            } else if (value.length > 254) {
                errorMessage = 'Email address is too long';
                isValid = false;
            }
            break;
            
        case 'subject':
            if (!value || value === '') {
                errorMessage = 'Please select a subject for your inquiry';
                isValid = false;
            }
            break;
            
        case 'message':
            if (!value) {
                errorMessage = 'Message is required';
                isValid = false;
            } else if (value.length < 10) {
                errorMessage = 'Message must be at least 10 characters long';
                isValid = false;
            } else if (value.length > 5000) {
                errorMessage = 'Message must be less than 5000 characters';
                isValid = false;
            }
            break;
            
        case 'privacy':
            if (!field.checked) {
                errorMessage = 'You must agree to the Privacy Policy to send your message';
                isValid = false;
            }
            break;
            
        case 'customSubject':
            if (!value) {
                errorMessage = 'Please specify your topic';
                isValid = false;
            } else if (value.length < 5) {
                errorMessage = 'Topic must be at least 5 characters long';
                isValid = false;
            } else if (value.length > 200) {
                errorMessage = 'Topic must be less than 200 characters';
                isValid = false;
            }
            break;
    }
    
    if (!isValid) {
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

/**
 * Show field validation error
 */
function showFieldError(field, errorMessage) {
    // Add error class to field
    field.classList.add('is-invalid');
    
    // For checkboxes, also add error class to the form-check container
    if (field.type === 'checkbox') {
        const formCheck = field.closest('.form-check');
        if (formCheck) {
            formCheck.classList.add('has-error');
        }
    }
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = errorMessage;
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field validation error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    // For checkboxes, also remove error class from the form-check container
    if (field.type === 'checkbox') {
        const formCheck = field.closest('.form-check');
        if (formCheck) {
            formCheck.classList.remove('has-error');
        }
    }
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Clear all field errors
 */
function clearAllFieldErrors() {
    const contactForm = document.querySelector('form[action="/contact"]');
    if (!contactForm) return;
    
    const fields = contactForm.querySelectorAll('.form-control');
    fields.forEach(field => clearFieldError(field));
}

/**
 * Highlight fields with errors based on server error message
 */
function highlightFieldsWithErrors(errorMessage) {
    const nameField = document.querySelector('#name');
    const emailField = document.querySelector('#email');
    const subjectField = document.querySelector('#subject');
    const messageField = document.querySelector('#message');
    
    // Parse error message to identify problematic fields
    const lowerErrorMessage = errorMessage.toLowerCase();
    
    if (lowerErrorMessage.includes('name')) {
        showFieldError(nameField, 'Please check your name');
    }
    
    if (lowerErrorMessage.includes('email')) {
        showFieldError(emailField, 'Please check your email address');
    }
    
    if (lowerErrorMessage.includes('subject')) {
        showFieldError(subjectField, 'Please check your subject');
    }
    
    if (lowerErrorMessage.includes('message')) {
        showFieldError(messageField, 'Please check your message');
    }
}/**
 * 
Add character counter to a field
 */
function addCharacterCounter(field, maxLength) {
    const counterDiv = document.createElement('div');
    counterDiv.className = 'char-counter';
    counterDiv.id = field.id + '-counter';
    
    // Insert after the field
    field.parentNode.appendChild(counterDiv);
    
    // Update counter initially
    updateCharacterCounter(field, maxLength);
}

/**
 * Update character counter
 */
function updateCharacterCounter(field, maxLength) {
    const counter = document.getElementById(field.id + '-counter');
    if (!counter) return;
    
    const currentLength = field.value.length;
    const remaining = maxLength - currentLength;
    
    counter.textContent = `${currentLength}/${maxLength} characters`;
    
    // Update counter styling based on remaining characters
    counter.classList.remove('warning', 'danger');
    
    if (remaining < maxLength * 0.1) { // Less than 10% remaining
        counter.classList.add('danger');
    } else if (remaining < maxLength * 0.2) { // Less than 20% remaining
        counter.classList.add('warning');
    }
}/**

 * Handle subject dropdown change
 */
function handleSubjectChange(subjectField) {
    const customSubjectField = document.getElementById('customSubjectField');
    const customSubjectInput = document.getElementById('customSubject');
    
    if (!customSubjectField || !customSubjectInput) return;
    
    if (subjectField.value === 'Other') {
        // Show custom subject field
        customSubjectField.style.display = 'block';
        customSubjectInput.required = true;
        
        // Add validation for custom subject
        customSubjectInput.addEventListener('blur', () => validateContactField(customSubjectInput, 'customSubject'));
        customSubjectInput.addEventListener('input', () => clearFieldError(customSubjectInput));
    } else {
        // Hide custom subject field
        customSubjectField.style.display = 'none';
        customSubjectInput.required = false;
        customSubjectInput.value = '';
        clearFieldError(customSubjectInput);
    }
}/**

 * Initialize Image Placeholder System
 */
function initializeImagePlaceholders() {
    // Find all images that might need placeholders
    const images = document.querySelectorAll('img[src*="placeholder.jpg"], img[src=""], img:not([src])');
    
    images.forEach(img => {
        // Skip if already processed
        if (img.classList.contains('placeholder-processed')) {
            return;
        }
        
        // Determine category from context
        const category = getImageCategory(img);
        
        // Create placeholder
        createImagePlaceholder(img, category);
        
        // Mark as processed
        img.classList.add('placeholder-processed');
    });
    
    // Also handle images that fail to load
    const allImages = document.querySelectorAll('img:not(.placeholder-processed)');
    allImages.forEach(img => {
        img.addEventListener('error', function() {
            if (!this.classList.contains('placeholder-processed')) {
                const category = getImageCategory(this);
                createImagePlaceholder(this, category);
                this.classList.add('placeholder-processed');
            }
        });
        
        // Add loading state
        img.addEventListener('loadstart', function() {
            this.classList.add('image-loading');
        });
        
        img.addEventListener('load', function() {
            this.classList.remove('image-loading');
        });
    });
}

/**
 * Determine image category from context
 */
function getImageCategory(img) {
    // Check URL path
    const path = window.location.pathname;
    if (path.includes('/restaurants')) return 'restaurant';
    if (path.includes('/museums')) return 'museum';
    if (path.includes('/archaeological-sites')) return 'archaeological_site';
    if (path.includes('/religious-sites')) return 'religious_site';

    if (path.includes('/cafes')) return 'cafe';
    if (path.includes('/accommodations')) return 'accommodation';
    if (path.includes('/ski-resorts')) return 'ski_resort';

    
    // Check parent elements for category hints
    const card = img.closest('.card');
    if (card) {
        const cardText = card.textContent.toLowerCase();
        if (cardText.includes('restaurant') || cardText.includes('dining')) return 'restaurant';
        if (cardText.includes('museum')) return 'museum';
        if (cardText.includes('church') || cardText.includes('monastery')) return 'religious_site';
        if (cardText.includes('archaeological')) return 'archaeological_site';

        if (cardText.includes('cafe') || cardText.includes('coffee')) return 'cafe';
        if (cardText.includes('hotel') || cardText.includes('accommodation')) return 'accommodation';
        if (cardText.includes('ski')) return 'ski_resort';

    }
    
    // Check data attributes
    const itemType = img.closest('[data-type]')?.dataset.type;
    if (itemType) return itemType;
    
    return 'default';
}

/**
 * Create image placeholder
 */
function createImagePlaceholder(img, category) {
    if (img.classList.contains('detail-related-thumb') || img.closest('.detail-related-thumb-wrap')) {
        img.src = getPlaceholderImageUrl(category);
        img.dataset.placeholderApplied = 'true';
        img.classList.add('placeholder-image');
        return;
    }

    // Store original attributes
    const originalSrc = img.src;
    const originalAlt = img.alt;
    const originalClasses = img.className;
    
    // Create placeholder div
    const placeholder = document.createElement('div');
    placeholder.className = `image-placeholder ${category} ${originalClasses}`;
    
    // Copy relevant styles
    const computedStyle = window.getComputedStyle(img);
    placeholder.style.width = img.offsetWidth ? img.offsetWidth + 'px' : computedStyle.width;
    placeholder.style.height = img.offsetHeight ? img.offsetHeight + 'px' : computedStyle.height;
    placeholder.style.borderRadius = computedStyle.borderRadius;
    
    // Add category-specific styling
    if (img.classList.contains('card-img-top')) {
        placeholder.classList.add('card-img-top');
    }
    if (img.classList.contains('destination-img')) {
        placeholder.classList.add('destination-img');
    }
    if (img.parentElement?.classList.contains('col-md-4')) {
        placeholder.classList.add('list-item-img');
    }
    
    // Add placeholder text
    const placeholderText = document.createElement('span');
    placeholderText.className = 'placeholder-text';
    placeholderText.textContent = getCategoryDisplayName(category);
    placeholder.appendChild(placeholderText);
    
    // Add click handler to try reloading original image
    placeholder.addEventListener('click', function() {
        if (originalSrc && originalSrc !== '' && !originalSrc.includes('placeholder.jpg')) {
            // Try to reload the original image
            const newImg = document.createElement('img');
            newImg.src = originalSrc;
            newImg.alt = originalAlt;
            newImg.className = originalClasses;
            
            newImg.onload = function() {
                placeholder.parentNode.replaceChild(newImg, placeholder);
                // Re-initialize placeholder system for the new image
                initializeImagePlaceholders();
            };
            
            newImg.onerror = function() {
                // If still fails, show a message
                showNotification('Image could not be loaded', 'error');
            };
        }
    });
    
    // Replace image with placeholder
    img.parentNode.replaceChild(placeholder, img);
}

/**
 * Get display name for category
 */
function getCategoryDisplayName(category) {
    const names = {
        'restaurant': 'Restaurant',
        'museum': 'Museum',
        'archaeological_site': 'Archaeological Site',
        'religious_site': 'Religious Site',

        'cafe': 'Café',
        'accommodation': 'Accommodation',
        'ski_resort': 'Ski Resort',

        'default': 'No Image'
    };
    return names[category] || 'No Image';
}

/**
 * Lazy load images with placeholder
 */
function initializeLazyLoadingWithPlaceholders() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Add loading state
                    img.classList.add('image-loading');
                    
                    // Load the actual image
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    
                    img.onload = function() {
                        img.classList.remove('image-loading');
                    };
                    
                    img.onerror = function() {
                        img.classList.remove('image-loading');
                        const category = getImageCategory(img);
                        createImagePlaceholder(img, category);
                    };
                    
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
}/**

 * Get appropriate placeholder image URL for category
 */
function getPlaceholderImageUrl(category) {
    const placeholders = {
        'restaurant': '/static/img/placeholder-restaurant.svg',
        'museum': '/static/img/placeholder-museum.svg',
        'religious_site': '/static/img/placeholder-church.svg',
        'archaeological_site': '/static/img/placeholder-museum.svg',

        'cafe': '/static/img/placeholder-restaurant.svg',
        'accommodation': '/static/img/placeholder-default.svg',
        'ski_resort': '/static/img/placeholder-default.svg',

        'default': '/static/img/placeholder-default.svg'
    };
    
    return placeholders[category] || placeholders['default'];
}

/**
 * Enhanced image error handling with category-specific placeholders
 */
function handleImageError(img) {
    if (img.dataset.placeholderApplied) {
        return;
    }

    const category = img.dataset.category || getImageCategory(img);

    if (img.classList.contains('detail-related-thumb') || img.closest('.detail-related-thumb-wrap')) {
        const placeholderUrl = getPlaceholderImageUrl(category);
        img.src = placeholderUrl;
        img.dataset.placeholderApplied = 'true';
        img.classList.add('placeholder-image');
        return;
    }

    const useGradientPlaceholder = img.classList.contains('directory-listing-card__img')
        || img.classList.contains('homepage-listing-card-img')
        || img.closest('.directory-listing-card__media, .homepage-listing-card-image-link');

    if (useGradientPlaceholder) {
        const placeholder = document.createElement('div');
        placeholder.className = 'category-image-placeholder';
        placeholder.dataset.category = category;
        placeholder.setAttribute('role', 'img');
        placeholder.setAttribute('aria-label', img.alt || getCategoryDisplayName(category));
        img.replaceWith(placeholder);
        img.dataset.placeholderApplied = 'true';
        return;
    }

    const placeholderUrl = getPlaceholderImageUrl(category);
    img.src = placeholderUrl;
    img.dataset.placeholderApplied = 'true';
    img.classList.add('placeholder-image');

    img.addEventListener('mouseenter', function() {
        this.style.opacity = '0.8';
    });

    img.addEventListener('mouseleave', function() {
        this.style.opacity = '1';
    });
}

// Make handleImageError globally available
window.handleImageError = handleImageError;

/**
 * Replace broken detail gallery images with the gradient placeholder
 */
function handleDetailGalleryImageError(img) {
    if (!img || img.dataset.galleryPlaceholderApplied) {
        return;
    }
    img.dataset.galleryPlaceholderApplied = 'true';

    const category = img.dataset.category || 'default';
    const main = img.closest('.detail-gallery__main');

    if (img.closest('.detail-gallery__thumb')) {
        img.closest('.detail-gallery__thumb').style.visibility = 'hidden';
        return;
    }

    if (!main) {
        return;
    }

    const title = img.alt || 'Photo';
    const placeholder = document.createElement('div');
    placeholder.className = 'detail-gallery__main detail-gallery__main--empty';
    placeholder.setAttribute('role', 'img');
    placeholder.setAttribute('aria-label', title);
    placeholder.innerHTML = `
        <div class="detail-gallery__placeholder category-image-placeholder" data-category="${category}">
            <span class="detail-gallery__placeholder-icon" aria-hidden="true"><i class="fas fa-camera"></i></span>
            <span class="detail-gallery__placeholder-label">No photo available</span>
        </div>`;
    main.replaceWith(placeholder);
}

window.handleDetailGalleryImageError = handleDetailGalleryImageError;

/**
 * Initialize enhanced image handling
 */
function initializeEnhancedImageHandling() {
    // Handle existing images with placeholder.jpg
    const placeholderImages = document.querySelectorAll('img[src*="placeholder.jpg"]');
    placeholderImages.forEach(img => {
        const category = getImageCategory(img);
        const placeholderUrl = getPlaceholderImageUrl(category);
        img.src = placeholderUrl;
        img.classList.add('placeholder-image');
    });
    
    // Handle all images for error cases
    const allImages = document.querySelectorAll('img:not([data-placeholder-handled])');
    allImages.forEach(img => {
        img.addEventListener('error', function() {
            handleImageError(this);
        });
        
        // Mark as handled
        img.dataset.placeholderHandled = 'true';
        
        // If image src is empty or invalid, immediately apply placeholder
        if (!img.src || img.src === '' || img.src === window.location.href) {
            handleImageError(img);
        }
    });
}

/**
 * Preload placeholder images for better performance
 */
function preloadPlaceholderImages() {
    const placeholderUrls = [
        '/static/img/placeholder-restaurant.svg',
        '/static/img/placeholder-museum.svg',
        '/static/img/placeholder-church.svg',
        '/static/img/placeholder-default.svg'
    ];
    
    placeholderUrls.forEach(url => {
        const img = new Image();
        img.src = url;
    });
}

function escapeMapHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function buildMapListingPopup(title, excerpt, detailUrl) {
    const excerptShort = excerpt && excerpt.length > 100 ? `${excerpt.substring(0, 100)}...` : excerpt;
    return `
        <div class="map-listing-popup">
            <strong class="map-listing-popup__title">${escapeMapHtml(title)}</strong>
            ${excerptShort ? `<p class="map-listing-popup__excerpt">${escapeMapHtml(excerptShort)}</p>` : ''}
            <a href="${detailUrl}" class="btn btn-sm btn-primary">View Details</a>
        </div>`;
}

/** Shared Leaflet helpers: CARTO light map and consistent detail zoom */
const VeriaGuideMaps = {
    DETAIL_ZOOM: 17,
    TILE_URL: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    TILE_ATTRIBUTION:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',

    addBaseLayer(map) {
        return L.tileLayer(this.TILE_URL, {
            subdomains: 'abcd',
            maxZoom: 20,
            attribution: this.TILE_ATTRIBUTION,
        }).addTo(map);
    },

    initDetailMap(mapId, lat, lng, options = {}) {
        if (typeof L === 'undefined') {
            setTimeout(() => this.initDetailMap(mapId, lat, lng, options), 100);
            return null;
        }

        const mapEl = document.getElementById(mapId);
        if (!mapEl || lat == null || lng == null) {
            return null;
        }

        const zoom = options.zoom && options.zoom >= 16 ? options.zoom : this.DETAIL_ZOOM;

        try {
            const map = L.map(mapId).setView([lat, lng], zoom);
            this.addBaseLayer(map);
            setTimeout(() => map.invalidateSize(), 100);
            const marker = L.marker([lat, lng]).addTo(map);
            if (options.popupHtml) {
                marker.bindPopup(options.popupHtml);
            }
            return map;
        } catch (error) {
            console.error('Error initializing detail map:', error);
            mapEl.innerHTML = "<p class='text-center text-muted p-3'>Error loading map.</p>";
            return null;
        }
    },
};

window.VeriaGuideMaps = VeriaGuideMaps;

function initializeDirectorySidebarMap(options = {}) {
    const {
        mapId = 'sidebar-map',
        listingSelector = '.directory-listing-card',
        categoryPath = '',
        defaultTitle = 'Location',
        center = [40.5246, 22.2022],
        zoom = 12
    } = options;

    if (typeof L === 'undefined') {
        setTimeout(() => initializeDirectorySidebarMap(options), 100);
        return null;
    }

    const mapContainer = document.getElementById(mapId);
    if (!mapContainer) {
        return null;
    }

    const map = L.map(mapId).setView(center, zoom);
    VeriaGuideMaps.addBaseLayer(map);

    setTimeout(() => map.invalidateSize(), 100);

    const bounds = [];
    document.querySelectorAll(listingSelector).forEach(listing => {
        const lat = listing.dataset.lat;
        const lng = listing.dataset.lng;
        if (!lat || !lng) return;

        const position = [parseFloat(lat), parseFloat(lng)];
        bounds.push(position);

        const titleEl = listing.querySelector('.directory-listing-card__title a');
        const excerptEl = listing.querySelector('.directory-listing-card__excerpt');
        const title = titleEl ? titleEl.textContent.trim() : defaultTitle;
        const excerpt = excerptEl ? excerptEl.textContent.trim() : '';

        let path = categoryPath;
        let slug = '';
        if (titleEl) {
            const hrefParts = titleEl.getAttribute('href').split('/').filter(Boolean);
            if (!path && hrefParts.length >= 2) {
                path = hrefParts[hrefParts.length - 2];
            }
            slug = hrefParts[hrefParts.length - 1] || '';
        }

        const marker = L.marker(position).addTo(map);
        marker.bindPopup(buildMapListingPopup(title, excerpt, `/${path}/${slug}`));
    });

    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [20, 20] });
        if (bounds.length === 1) {
            map.setZoom(VeriaGuideMaps.DETAIL_ZOOM);
        }
    }

    return map;
}

let favoritesMapInstance = null;
const favoritesMapMarkers = {};

function initializeFavoritesMapPage() {
    if (typeof L === 'undefined') {
        setTimeout(initializeFavoritesMapPage, 100);
        return;
    }

    const mapElement = document.getElementById('favorites-map');
    if (!mapElement) return;

    favoritesMapInstance = L.map('favorites-map').setView([40.5246, 22.2022], 12);
    VeriaGuideMaps.addBaseLayer(favoritesMapInstance);

    setTimeout(() => favoritesMapInstance.invalidateSize(), 100);

    const bounds = [];
    document.querySelectorAll('[id^="favorite-item-"]').forEach(card => {
        const lat = card.dataset.lat;
        const lng = card.dataset.lng;
        const id = card.id.replace('favorite-item-', '');
        if (!lat || !lng) return;

        const position = [parseFloat(lat), parseFloat(lng)];
        bounds.push(position);

        const titleEl = card.querySelector('.card-title');
        const title = titleEl ? titleEl.textContent.trim() : 'Favorite';
        const categorySlug = card.dataset.categorySlug || '';
        const slug = card.dataset.slug || '';
        const excerpt = card.dataset.excerpt || '';
        const detailUrl = categorySlug && slug ? `/${categorySlug}/${slug}` : '#';

        const marker = L.marker(position).addTo(favoritesMapInstance);
        marker.bindPopup(buildMapListingPopup(title, excerpt, detailUrl));
        favoritesMapMarkers[id] = marker;
    });

    if (bounds.length > 0) {
        favoritesMapInstance.fitBounds(bounds, { padding: [20, 20] });
        if (bounds.length === 1) {
            favoritesMapInstance.setZoom(VeriaGuideMaps.DETAIL_ZOOM);
        }
    }

    document.querySelectorAll('.show-on-favorites-map').forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const marker = favoritesMapMarkers[this.dataset.id];
            if (marker && favoritesMapInstance) {
                favoritesMapInstance.setView(marker.getLatLng(), 16);
                marker.openPopup();
            }
        });
    });
}