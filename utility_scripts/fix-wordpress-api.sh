#!/bin/bash

echo "🔧 Fixing WordPress REST API..."

# WordPress Container ID
WP_CONTAINER="wp_veriaguide"

echo "📋 Checking WordPress status..."
docker exec $WP_CONTAINER wp --allow-root core is-installed 2>/dev/null || {
    echo "❌ WordPress not installed. Installing now..."
    docker exec $WP_CONTAINER wp --allow-root core install \
        --url="http://localhost:8086" \
        --title="VeriaGuide" \
        --admin_user="${WP_ADMIN_USER:-admin}" \
        --admin_password="${WP_ADMIN_PASSWORD:?Set WP_ADMIN_PASSWORD}" \
        --admin_email="${WP_ADMIN_EMAIL:-admin@example.com}" \
        --skip-email
}

echo "🔗 Setting up permalinks..."
docker exec $WP_CONTAINER wp --allow-root rewrite structure '/%postname%/'
docker exec $WP_CONTAINER wp --allow-root rewrite flush

echo "🔌 Installing required plugins..."
# Install Custom Post Type UI
docker exec $WP_CONTAINER wp --allow-root plugin install custom-post-type-ui --activate

# Install Advanced Custom Fields
docker exec $WP_CONTAINER wp --allow-root plugin install advanced-custom-fields --activate

# Install JWT Authentication (if needed)
docker exec $WP_CONTAINER wp --allow-root plugin install jwt-authentication-for-wp-rest-api --activate 2>/dev/null || echo "JWT plugin not available via repository"

echo "📝 Creating custom post types..."
# Create religious_sites post type
docker exec $WP_CONTAINER wp --allow-root eval '
register_post_type("religious_site", array(
    "public" => true,
    "show_in_rest" => true,
    "rest_base" => "religious_sites",
    "supports" => array("title", "editor", "thumbnail", "custom-fields")
));
flush_rewrite_rules();
'

# Create other post types
for post_type in museum archaeological_site hiking_trail restaurant cafe accommodation ski_resort tour hidden_gem; do
    echo "Creating post type: $post_type"
    docker exec $WP_CONTAINER wp --allow-root eval "
    register_post_type('${post_type}', array(
        'public' => true,
        'show_in_rest' => true,
        'rest_base' => '${post_type}s',
        'supports' => array('title', 'editor', 'thumbnail', 'custom-fields')
    ));
    "
done

echo "🔄 Flushing rewrite rules..."
docker exec $WP_CONTAINER wp --allow-root rewrite flush

echo "✅ WordPress REST API should now be working!"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8086/wp-json/wp/v2/"
echo "   curl http://localhost:8086/wp-json/wp/v2/religious_sites"
echo ""
echo "🔑 WordPress Admin:"
echo "   URL: http://localhost:8086/wp-admin"
echo "   User: \$WP_ADMIN_USER"
echo "   Pass: (from WP_ADMIN_PASSWORD env)"