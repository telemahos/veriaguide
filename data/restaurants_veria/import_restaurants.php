<?php
/**
 * Import Restaurants from CSV to WordPress
 *
 * This script imports restaurant data from a CSV file and creates 'restaurant' custom posts.
 * It maps CSV columns to specific ACF (Advanced Custom Fields) as defined for the 'restaurant' post type.
 *
 * Instructions:
 * 1. Place this file in the WordPress root directory.
 * 2. Make sure the CSV file is at /var/www/html/data/restaurants_veria/restaurant_veria.csv inside the container.
 * 3. Execute via WP-CLI: `wp eval-file import_restaurants.php`
 *    or via Docker: `docker exec -u www-data [container_name] php /var/www/html/import_restaurants.php`
 */

// Bootstrap WordPress
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once('/var/www/html/wp-load.php');
}

// Check if ACF plugin is active
if (!function_exists('update_field')) {
    die("❌ Error: Advanced Custom Fields (ACF) plugin is not active or installed.\n");
}

echo "🍴 Starting restaurant import from CSV...\n";

// --- CONFIGURATION ---
$csv_file_path = '/var/www/html/data/restaurants_veria/restaurant_veria.csv';
$post_type = 'restaurant';
$author_id = 1; // Default to admin user ID 1

// --- FILE CHECK ---
if (!file_exists($csv_file_path)) {
    die("❌ Error: CSV file not found at: {$csv_file_path}\n");
}

// --- CSV PROCESSING ---
$csv_data = array_map('str_getcsv', file($csv_file_path));
$headers = array_map('trim', array_shift($csv_data)); // Get headers and trim whitespace

echo "📊 Found " . count($csv_data) . " rows in the CSV file.\n";

// --- IMPORT COUNTERS ---
$imported_count = 0;
$skipped_count = 0;
$error_count = 0;

// --- MAIN IMPORT LOOP ---
foreach ($csv_data as $row_index => $row) {
    // Skip empty rows
    if (count($row) <= 1 && empty($row[0])) {
        continue;
    }

    // Ensure row has the same number of columns as headers
    if (count($row) !== count($headers)) {
        echo "  ⚠️  Warning: Skipping row " . ($row_index + 2) . " due to column mismatch.\n";
        $skipped_count++;
        continue;
    }

    $data = array_combine($headers, $row);
    $item_name = sanitize_text_field($data['name']);

    // Skip if name is empty
    if (empty($item_name)) {
        echo "  ⚠️  Warning: Skipping row " . ($row_index + 2) . " because the 'name' is empty.\n";
        $skipped_count++;
        continue;
    }

    echo "Processing: " . $item_name . "\n";

    try {
        // Check if a post with the same title already exists
        if (get_page_by_title($item_name, OBJECT, $post_type)) {
            echo "  ℹ️  Post already exists. Skipping.\n";
            $skipped_count++;
            continue;
        }

        // --- Create Post Object ---
        $post_data = [
            'post_title'   => $item_name,
            'post_content'  => wp_kses_post($data['description']),
            'post_status'  => 'publish',
            'post_type'    => $post_type,
            'post_author'  => $author_id,
        ];

        $post_id = wp_insert_post($post_data, true); // Pass true to get WP_Error on failure

        if (is_wp_error($post_id)) {
            throw new Exception("Failed to create post: " . $post_id->get_error_message());
        }

        // --- Prepare ACF Fields ---
        $acf_fields = [];

        $acf_fields['seo_title'] = $item_name . ' | Restaurants in Veria Greece';
        $acf_fields['seo_description'] = 'Restaurants in Veria Greece';
        $acf_fields['rating'] = sanitize_text_field($data['rating']);
        $acf_fields['reviews'] = sanitize_text_field($data['review_count']);
        $acf_fields['category'] = sanitize_text_field($data['category']);
        $acf_fields['phone'] = sanitize_text_field($data['phone']);
        $acf_fields['website'] = esc_url_raw($data['website']);
        $email = !empty($data['email']) ? $data['email'] : $data['Emails'];
        $acf_fields['email'] = sanitize_email($email);
        $acf_fields['opening_hours'] = sanitize_text_field($data['open_hours']);
        $acf_fields['address'] = sanitize_text_field($data['address']);
        if (isset($data['City'])) {
            $acf_fields['city'] = sanitize_text_field($data['City']);
        }
        $acf_fields['location_map'] = [
            'address' => sanitize_text_field($data['address']),
            'lat'     => sanitize_text_field($data['latitude']),
            'lng'     => sanitize_text_field($data['longitude']),
        ];
        $acf_fields['latitude'] = sanitize_text_field($data['latitude']);
        $acf_fields['longitude'] = sanitize_text_field($data['longitude']);
        $acf_fields['gmaps_url'] = esc_url_raw($data['url']);

        // --- Update ACF Fields ---
        foreach ($acf_fields as $field_key => $value) {
            if (!empty($value)) {
                update_field($field_key, $value, $post_id);
            }
        }

        echo "  ✅ Successfully imported: " . $item_name . " (ID: $post_id)\n";
        $imported_count++;

    } catch (Exception $e) {
        echo "  ❌ Error importing " . $item_name . ": " . $e->getMessage() . "\n";
        $error_count++;
    }

    usleep(50000); // 0.05 seconds
}

// --- FINAL SUMMARY ---
echo "\n📈 Import Summary:\n";
echo "✅ Imported: $imported_count\n";
echo "ℹ️  Skipped:  $skipped_count\n";
echo "❌ Errors:   $error_count\n";
$total_processed = $imported_count + $skipped_count + $error_count;
echo "📊 Total rows processed: " . $total_processed . "\n";

flush_rewrite_rules();
echo "\n🔄 Rewrite rules flushed.\n";

echo "\n🎉 Import completed!\n";
?>
