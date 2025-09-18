<?php
/**
 * WordPress Setup Script for VeriaGuide
 * This script sets up the custom post types and REST API
 */

// WordPress Bootstrap
define('WP_USE_THEMES', false);
require_once('/var/www/html/wp-load.php');

echo "🔧 Setting up WordPress for VeriaGuide...\n";

// 1. Install WordPress if not installed
if (!is_blog_installed()) {
    echo "📋 Installing WordPress...\n";
    
    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    
    wp_install(
        'VeriaGuide',                    // Blog title
        'admin',                         // Admin username
        'admin@veriaguide.com',         // Admin email
        true,                           // Public
        '',                             // Deprecated
        'VG_admin_secure_2025!'         // Admin password
    );
    
    echo "✅ WordPress installed successfully!\n";
}

// 2. Set up permalinks
echo "🔗 Setting up permalinks...\n";
update_option('permalink_structure', '/%postname%/');

// 3. Register custom post types
echo "📝 Registering custom post types...\n";

$post_types = [
    'religious_site' => 'religious_sites',
    'museum' => 'museums',
    'archaeological_site' => 'archaeological_sites',
    'hiking_trail' => 'hiking_trails',
    'restaurant' => 'restaurants',
    'cafe' => 'cafes',
    'accommodation' => 'accommodations',
    'ski_resort' => 'ski_resorts',
    'tour' => 'tours',
    'hidden_gem' => 'hidden_gems'
];

foreach ($post_types as $post_type => $rest_base) {
    register_post_type($post_type, [
        'public' => true,
        'show_in_rest' => true,
        'rest_base' => $rest_base,
        'supports' => ['title', 'editor', 'thumbnail', 'custom-fields'],
        'labels' => [
            'name' => ucwords(str_replace('_', ' ', $post_type)) . 's',
            'singular_name' => ucwords(str_replace('_', ' ', $post_type)),
        ],
        'menu_position' => 20,
        'has_archive' => true,
        'rewrite' => ['slug' => $rest_base],
    ]);
    
    echo "✅ Registered post type: $post_type -> $rest_base\n";
}

// 4. Create some sample posts if none exist
echo "📄 Creating sample posts...\n";

foreach ($post_types as $post_type => $rest_base) {
    $existing_posts = get_posts([
        'post_type' => $post_type,
        'numberposts' => 1,
        'post_status' => 'any'
    ]);
    
    if (empty($existing_posts)) {
        $sample_post_id = wp_insert_post([
            'post_title' => 'Sample ' . ucwords(str_replace('_', ' ', $post_type)),
            'post_content' => 'This is a sample ' . str_replace('_', ' ', $post_type) . ' for testing purposes.',
            'post_status' => 'publish',
            'post_type' => $post_type,
            'meta_input' => [
                'address' => 'Sample Address, Veria, Greece',
                'location_map' => [
                    'lat' => 40.5246,
                    'lng' => 22.2022,
                    'address' => 'Sample Address, Veria, Greece'
                ]
            ]
        ]);
        
        if ($sample_post_id) {
            echo "✅ Created sample post for $post_type (ID: $sample_post_id)\n";
        }
    } else {
        echo "ℹ️ Posts already exist for $post_type\n";
    }
}

// 5. Flush rewrite rules
flush_rewrite_rules();

echo "🔄 Flushed rewrite rules\n";

// 6. Test REST API
echo "🧪 Testing REST API endpoints...\n";

foreach ($post_types as $post_type => $rest_base) {
    $posts = get_posts([
        'post_type' => $post_type,
        'numberposts' => 1,
        'post_status' => 'publish'
    ]);
    
    echo "📊 $rest_base: " . count($posts) . " posts found\n";
}

echo "\n✅ WordPress setup complete!\n";
echo "🌐 REST API Base: " . rest_url('wp/v2/') . "\n";
echo "🔑 Admin URL: " . admin_url() . "\n";
echo "👤 Admin User: admin\n";
echo "🔐 Admin Pass: VG_admin_secure_2025!\n";

?>