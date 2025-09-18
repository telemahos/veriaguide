<?php
/**
 * Debug religious_sites post type registration
 */

define('WP_USE_THEMES', false);
require_once('/var/www/html/wp-load.php');

echo "🔍 Debugging religious_sites post type...\n\n";

// Check if post type exists
$post_type = get_post_type_object('religious_site');
if ($post_type) {
    echo "✅ Post type 'religious_site' is registered\n";
    echo "   Label: {$post_type->label}\n";
    echo "   Show in REST: " . ($post_type->show_in_rest ? 'Yes' : 'No') . "\n";
    echo "   REST Base: " . ($post_type->rest_base ?: 'Not set') . "\n";
    echo "   REST Controller: " . ($post_type->rest_controller_class ?: 'Default') . "\n";
} else {
    echo "❌ Post type 'religious_site' is NOT registered\n";
}

// Check posts count
$posts = get_posts(array(
    'post_type' => 'religious_site',
    'numberposts' => -1,
    'post_status' => array('publish', 'draft', 'private')
));

echo "\n📊 Posts count: " . count($posts) . "\n";

if (count($posts) > 0) {
    echo "   Sample posts:\n";
    foreach (array_slice($posts, 0, 3) as $post) {
        echo "     - {$post->post_title} (ID: {$post->ID}, Status: {$post->post_status})\n";
    }
}

// Check active plugins
echo "\n🔌 Active plugins:\n";
$active_plugins = get_option('active_plugins');
foreach ($active_plugins as $plugin) {
    echo "   - $plugin\n";
}

// Check REST API routes
echo "\n🌐 REST API routes for religious_sites:\n";
$rest_server = rest_get_server();
$routes = $rest_server->get_routes();

foreach ($routes as $route => $handlers) {
    if (strpos($route, 'religious') !== false) {
        echo "   - $route\n";
    }
}

echo "\n✅ Debug complete!\n";
?>