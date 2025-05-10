- docker-compose down && docker-compose up --build
- Bei Google Maps und ACF musst du im theme/functions.php das einstellen:
'''
// Add Google Maps API key for ACF Free
function my_acf_google_map_api($api) {
    $api['key'] = '***REMOVED***'; // Dein Google Maps API-Schlüssel
    return $api;
}
add_filter('acf/fields/google_map/api', 'my_acf_google_map_api');
'''