<?php
/**
 * Import ACF Fields for Restaurants from JSON export
 */

// Prevent direct access
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once('/home/veriaguide.gr/public_html/wp-load.php');
}

// Check if ACF is available
if (!function_exists('acf_import_field_group')) {
    die("❌ Advanced Custom Fields plugin is not active!\n");
}

echo "🔧 Starting ACF field import for Restaurants...\n";

// JSON file path
$json_file = '/home/veriaguide.gr/public_html/data/restaurants_veria/acf-export-2025-09-15.json';

if (!file_exists($json_file)) {
    die("❌ ACF JSON file not found: $json_file\n");
}

// Read and decode JSON
$json_content = file_get_contents($json_file);
$field_groups = json_decode($json_content, true);

if (!$field_groups) {
    die("❌ Failed to decode JSON file\n");
}

echo "📊 Found " . count($field_groups) . " field groups to import\n";

$imported = 0;
$errors = 0;

foreach ($field_groups as $field_group) {
    try {
        // Check if field group already exists
        $existing = acf_get_field_group($field_group['key']);
        if ($existing) {
            echo "  ⚠️  Field group '{$field_group['title']}' already exists, updating...\n";
        } else {
            echo "  ➕ Creating field group '{$field_group['title']}'...\n";
        }
        
        // Import/update the field group
        $result = acf_import_field_group($field_group);
        
        if ($result) {
            echo "  ✅ Successfully imported: {$field_group['title']}\n";
            $imported++;
        } else {
            throw new Exception("Failed to import field group");
        }
        
    } catch (Exception $e) {
        echo "  ❌ Error importing {$field_group['title']}: " . $e->getMessage() . "\n";
        $errors++;
    }
}

echo "\n📈 Import Summary:\n";
echo "✅ Imported: $imported\n";
echo "❌ Errors: $errors\n";

echo "\n🎉 ACF Restaurant field import completed!\n";

?>