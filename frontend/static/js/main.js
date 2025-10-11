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
    
    // Initialize mobile menu behavior (legacy - now handled in initializeNavigation)
    initializeMobileMenu();
    
    // Initialize scroll animations
    initializeScrollAnimations();
    
    // Initialize hero search form
    initializeHeroSearchForm();
    
    // Initialize destination cards
    initializeDestinationCards();
    
    // Initialize search functionality
    initializeSearchFunctionality();
    
    // Initialize results per page selector
    initializeResultsPerPage();
    
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
 * Initialize Hero Search Form
 */
function initializeHeroSearchForm() {
    // Initialize search tabs
    initializeSearchTabs();
    
    // Initialize browse categories form
    const heroForm = document.getElementById('heroSearchForm');
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
 * Initialize Search Tabs
 */
function initializeSearchTabs() {
    const searchTabs = document.querySelectorAll('.search-tab');
    const searchForms = document.querySelectorAll('.search-form-content');
    
    searchTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all tabs and forms
            searchTabs.forEach(t => t.classList.remove('active'));
            searchForms.forEach(f => f.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show corresponding form
            const targetForm = document.querySelector(`[data-form="${targetTab}"]`);
            if (targetForm) {
                targetForm.classList.add('active');
            }
        });
    });
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
        'hiking', 'local', 'restaurant', 'cafe', 'accommodation'
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
}/*
*
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