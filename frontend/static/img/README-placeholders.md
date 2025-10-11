# Image Placeholder System

This directory contains SVG-based placeholder images for different content categories in VeriaGuide.

## Available Placeholders

- `placeholder-default.svg` - Generic placeholder with VeriaGuide branding
- `placeholder-restaurant.svg` - Restaurant/dining specific placeholder with utensils icon
- `placeholder-museum.svg` - Museum/cultural site placeholder with building icon
- `placeholder-church.svg` - Religious site placeholder with church icon

## Usage

### In Templates
Use the custom Jinja2 filters:

```html
<!-- Get item image with category-specific fallback -->
<img src="{{ item|item_image('restaurant') }}" alt="{{ item.title.rendered }}">

<!-- Get placeholder directly -->
<img src="{{ 'restaurant'|placeholder_image }}" alt="Restaurant placeholder">
```

### In JavaScript
Use the helper functions:

```javascript
// Get placeholder URL for category
const placeholderUrl = getPlaceholderImageUrl('restaurant');

// Handle image errors automatically
handleImageError(imageElement);
```

## Categories

- `restaurant` - Restaurants and dining establishments
- `museum` - Museums and cultural institutions
- `religious_site` - Churches, monasteries, and religious sites
- `archaeological_site` - Archaeological sites and ruins
- `hiking_trail` - Hiking trails and outdoor activities
- `cafe` - Cafés and coffee shops
- `accommodation` - Hotels and accommodations
- `ski_resort` - Ski resorts and winter sports
- `tour` - Tours and guided experiences
- `hidden_gem` - Hidden gems and special places
- `default` - Generic fallback for any category

## Features

- **Responsive**: SVG format scales perfectly at any size
- **Animated**: Subtle shimmer effect for visual appeal
- **Accessible**: High contrast support and reduced motion options
- **Branded**: Consistent with VeriaGuide visual identity
- **Performance**: Lightweight SVG files with preloading
- **Fallback**: Automatic error handling for failed image loads

## Technical Details

- Format: SVG (Scalable Vector Graphics)
- Size: Optimized for web delivery
- Colors: Uses CSS custom properties for theming
- Animation: CSS-based shimmer effect
- Accessibility: Supports high contrast and reduced motion preferences