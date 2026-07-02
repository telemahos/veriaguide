<?php
/**
 * Update WordPress homepage hero and about text for heritage-focused SEO.
 *
 * Run on VPS:
 *   php /home/veriaguide.gr/public_html/wordpress/update_homepage_seo_content.php
 */
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once dirname(__DIR__) . '/wp-load.php';
}

if (!function_exists('update_field')) {
    fwrite(STDERR, "ACF plugin required.\n");
    exit(1);
}

$hero_title = 'Veria, Greece: Byzantine Churches & Macedonian Heritage';
$hero_subtitle = 'Explore Veria (Veroia) in Imathia — 60+ Byzantine churches, museums, Royal Tombs of Vergina and the Vema where Apostle Paul preached.';
$about_text = '<p>Discover Veria (Veroia), a historic city in Imathia, northern Greece, where Byzantine churches, museums and archaeological treasures meet Macedonian heritage. Use Veria Guide to explore churches linked to Apostle Paul, the Royal Tombs of Vergina and hidden gems across the region.</p>';

$slides = get_field('hero_slides', 'option');
if (!is_array($slides) || empty($slides)) {
    $slides = array(
        array(
            'image_url' => '/static/img/veria-hero2.webp',
            'title' => $hero_title,
            'subtitle' => $hero_subtitle,
        ),
    );
} else {
    foreach ($slides as $index => $slide) {
        $slides[$index]['title'] = $hero_title;
        $slides[$index]['subtitle'] = $hero_subtitle;
        if (empty($slides[$index]['image_url'])) {
            $slides[$index]['image_url'] = '/static/img/veria-hero2.webp';
        }
    }
}

update_field('hero_slides', $slides, 'option');
update_field('about_text', $about_text, 'option');

echo "Updated homepage hero and about text for SEO.\n";
echo "Hero title: {$hero_title}\n";
