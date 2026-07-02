<?php
/**
 * Reorder homepage sections: Churches & Monasteries first.
 *
 * Run on VPS:
 *   php /home/veriaguide.gr/public_html/wordpress/update_homepage_section_order.php
 */
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once dirname(__DIR__) . '/wp-load.php';
}

if (!function_exists('update_field')) {
    fwrite(STDERR, "ACF plugin required.\n");
    exit(1);
}

$order_map = array(
    'religious_sites' => 1,
    'museums' => 2,
    'archaeological_sites' => 3,
);

$sections = get_field('homepage_sections', 'option');
if (!is_array($sections) || empty($sections)) {
    fwrite(STDERR, "No homepage sections found.\n");
    exit(1);
}

foreach ($sections as $index => $section) {
    $category = $section['category'] ?? '';
    if (isset($order_map[$category])) {
        $sections[$index]['order'] = $order_map[$category];
    }
}

usort($sections, function ($a, $b) {
    return ($a['order'] ?? 99) - ($b['order'] ?? 99);
});

update_field('homepage_sections', $sections, 'option');

echo "Homepage section order updated:\n";
foreach ($sections as $section) {
    $title = $section['title'] ?? ($section['category'] ?? 'unknown');
    $order = $section['order'] ?? '?';
    echo "  {$order}. {$title}\n";
}
