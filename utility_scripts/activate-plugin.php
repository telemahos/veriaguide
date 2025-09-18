<?php
/**
 * Activate VeriaGuide Custom Post Types Plugin
 */

define('WP_USE_THEMES', false);
require_once('/var/www/html/wp-load.php');

echo "🔌 Activating VeriaGuide Custom Post Types plugin...\n";

// Activate the plugin
$plugin_file = 'veriaguide-cpt.php';
$result = activate_plugin($plugin_file);

if (is_wp_error($result)) {
    echo "❌ Error activating plugin: " . $result->get_error_message() . "\n";
} else {
    echo "✅ Plugin activated successfully!\n";
    
    // Flush rewrite rules
    flush_rewrite_rules();
    echo "🔄 Rewrite rules flushed\n";
    
    // Test the REST API endpoints
    echo "🧪 Testing REST API endpoints...\n";
    
    $post_types = array(
        'religious_sites', 'museums', 'archaeological_sites', 'hiking_trails',
        'restaurants', 'cafes', 'accommodations', 'ski_resorts', 'tours', 'hidden_gems'
    );
    
    foreach ($post_types as $rest_base) {
        $posts = get_posts(array(
            'post_type' => str_replace('s', '', $rest_base), // Remove 's' for post type
            'numberposts' => -1,
            'post_status' => 'publish'
        ));
        
        echo "📊 $rest_base: " . count($posts) . " posts\n";
    }
    
    echo "\n✅ Setup complete!\n";
    echo "🌐 Test REST API: http://localhost:8086/wp-json/wp/v2/religious_sites\n";
}

?>