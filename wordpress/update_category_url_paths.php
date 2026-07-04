<?php
/**
 * One-time update: hyphenated public URLs in homepage sections, menus, and post content.
 *
 * Run on VPS:
 *   php $WP_DOCUMENT_ROOT/wordpress/update_category_url_paths.php
 */
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once dirname(__DIR__) . '/wp-load.php';
}

$replacements = array(
    'https://veriaguide.gr/religious_sites' => 'https://veriaguide.gr/religious-sites',
    'https://www.veriaguide.gr/religious_sites' => 'https://veriaguide.gr/religious-sites',
    'http://veriaguide.gr/religious_sites' => 'https://veriaguide.gr/religious-sites',
    '/religious_sites' => '/religious-sites',
    'https://veriaguide.gr/archaeological_sites' => 'https://veriaguide.gr/archaeological-sites',
    'https://www.veriaguide.gr/archaeological_sites' => 'https://veriaguide.gr/archaeological-sites',
    'http://veriaguide.gr/archaeological_sites' => 'https://veriaguide.gr/archaeological-sites',
    '/archaeological_sites' => '/archaeological-sites',
    'https://veriaguide.gr/ski_resorts' => 'https://veriaguide.gr/ski-resorts',
    'https://www.veriaguide.gr/ski_resorts' => 'https://veriaguide.gr/ski-resorts',
    'http://veriaguide.gr/ski_resorts' => 'https://veriaguide.gr/ski-resorts',
    '/ski_resorts' => '/ski-resorts',
);

function apply_url_replacements($value, array $replacements) {
    if (!is_string($value) || $value === '') {
        return $value;
    }
    return str_replace(array_keys($replacements), array_values($replacements), $value);
}

// Homepage sections (ACF)
if (function_exists('get_field')) {
    $sections = get_field('homepage_sections', 'option');
    if (is_array($sections)) {
        $changed = false;
        foreach ($sections as &$section) {
            if (!empty($section['view_all_link'])) {
                $updated = apply_url_replacements($section['view_all_link'], $replacements);
                if ($updated !== $section['view_all_link']) {
                    $section['view_all_link'] = $updated;
                    $changed = true;
                }
            }
        }
        unset($section);
        if ($changed) {
            update_field('homepage_sections', $sections, 'option');
            echo "Updated homepage section view_all_link URLs.\n";
        }
    }
}

// Navigation menus
$locations = get_nav_menu_locations();
if (!empty($locations)) {
    foreach ($locations as $location => $menu_id) {
        $items = wp_get_nav_menu_items($menu_id);
        if (!$items) {
            continue;
        }
        foreach ($items as $item) {
            $updated = apply_url_replacements($item->url, $replacements);
            if ($updated === $item->url) {
                continue;
            }
            wp_update_nav_menu_item($menu_id, $item->ID, array(
                'menu-item-title' => $item->title,
                'menu-item-url' => $updated,
                'menu-item-status' => 'publish',
                'menu-item-parent-id' => (int) $item->menu_item_parent,
            ));
            echo "Updated menu item ({$location}): {$item->title}\n";
        }
    }
}

// Post content internal links
$post_types = array(
    'religious_site',
    'archaeological_site',
    'museum',
    'ski_resort',
    'page',
    'post',
);
$posts = get_posts(array(
    'post_type' => $post_types,
    'post_status' => 'publish',
    'numberposts' => -1,
    'fields' => 'ids',
));
$content_updates = 0;
foreach ($posts as $post_id) {
    $post = get_post($post_id);
    if (!$post || empty($post->post_content)) {
        continue;
    }
    $updated = apply_url_replacements($post->post_content, $replacements);
    if ($updated === $post->post_content) {
        continue;
    }
    wp_update_post(array(
        'ID' => $post_id,
        'post_content' => $updated,
    ));
    $content_updates++;
}
if ($content_updates > 0) {
    echo "Updated post content in {$content_updates} posts.\n";
}

echo "Done.\n";
