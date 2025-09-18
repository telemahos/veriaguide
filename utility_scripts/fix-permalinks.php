<?php
/**
 * Fix WordPress permalinks and flush rewrite rules
 */

define('WP_USE_THEMES', false);
require_once('/var/www/html/wp-load.php');

echo "🔧 Fixing WordPress permalinks...\n\n";

// Set permalink structure to pretty URLs
update_option('permalink_structure', '/%postname%/');

// Flush rewrite rules
flush_rewrite_rules(true);

echo "✅ Permalinks updated and rewrite rules flushed\n";

// Test REST API endpoint
echo "\n🧪 Testing REST API endpoint...\n";

// Make internal request to REST API
$request = new WP_REST_Request('GET', '/wp/v2/religious_sites');
$request->set_param('per_page', 1);

$response = rest_do_request($request);
$data = $response->get_data();

if (is_wp_error($data)) {
    echo "❌ REST API Error: " . $data->get_error_message() . "\n";
} else {
    echo "✅ REST API working! Found " . count($data) . " religious sites\n";
    if (!empty($data)) {
        echo "   Sample: " . $data[0]['title']['rendered'] . "\n";
    }
}

echo "\n✅ Permalink fix complete!\n";
?>