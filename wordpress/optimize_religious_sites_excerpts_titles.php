<?php
/**
 * Optimize all Religious Sites: custom SEO excerpts + shorter titles.
 *
 * Run on VPS:
 *   php $WP_DOCUMENT_ROOT/wordpress/optimize_religious_sites_excerpts_titles.php
 */
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once dirname(__DIR__) . '/wp-load.php';
}

const TITLE_MAX_LEN = 75;
const EXCERPT_MAX_LEN = 158;
const VERIA_PHRASE = 'Veria (Veroia), Imathia, Greece';

function needs_custom_excerpt(string $raw_excerpt, string $plain_excerpt): bool
{
    if ($plain_excerpt === '') {
        return true;
    }
    if (strpos($raw_excerpt, '&hellip;') !== false || strpos($raw_excerpt, '&#8230;') !== false) {
        return true;
    }
    if (str_ends_with($plain_excerpt, '…') || str_ends_with($plain_excerpt, '...')) {
        return true;
    }
    return false;
}

function build_seo_excerpt(string $content, string $title): string
{
    $text = '';
    if (preg_match('/<p[^>]*>(.*?)<\/p>/is', $content, $match)) {
        $text = wp_strip_all_tags($match[1]);
    } else {
        $text = wp_strip_all_tags($content);
    }

    $text = preg_replace('/\s+/u', ' ', trim($text));

    if (mb_strlen($text) < 40) {
        $name = trim(explode(':', $title)[0]);
        $text = "Visit {$name} in " . VERIA_PHRASE . '. Byzantine church guide with visiting hours and travel tips.';
    }

    if (mb_strlen($text) > EXCERPT_MAX_LEN) {
        $text = mb_substr($text, 0, EXCERPT_MAX_LEN);
        $text = preg_replace('/\s+\S*$/u', '', $text);
    }

    if (!preg_match('/veria|veroia|imathia|greece/iu', $text)) {
        $suffix = ' Located in ' . VERIA_PHRASE . '.';
        if (mb_strlen($text . $suffix) <= EXCERPT_MAX_LEN + 2) {
            $text .= $suffix;
        }
    }

    $text = rtrim($text, '.… ');
    return $text . '.';
}

function extract_church_name(string $main_raw): array
{
    $prefix = 'Holy Church of ';

    $rules = [
        '/^Exploring the Holy Church of the\s+/iu' => ['Holy Church of ', ''],
        '/^Exploring the Holy Church of\s+/iu' => ['Holy Church of ', ''],
        '/^Holy Metropolitan Church of the\s+/iu' => ['Holy Metropolitan Church of ', ''],
        '/^Holy Metropolitan Church of\s+/iu' => ['Holy Metropolitan Church of ', ''],
        '/^New Holy Church of the\s+/iu' => ['New Holy Church of the ', ''],
        '/^New Holy Church of\s+/iu' => ['New Holy Church of ', ''],
        '/^The Holy Church of the\s+/iu' => ['Holy Church of ', ''],
        '/^The Holy Church of\s+/iu' => ['Holy Church of ', ''],
        '/^Holy Church of the\s+/iu' => ['Holy Church of ', ''],
        '/^Holy Church of\s+/iu' => ['Holy Church of ', ''],
        '/^Holy Chapel of the\s+/iu' => ['Holy Chapel of ', ''],
        '/^Holy Chapel of\s+/iu' => ['Holy Chapel of ', ''],
        '/^Chapel of the\s+/iu' => ['Chapel of ', ''],
        '/^Chapel of\s+/iu' => ['Chapel of ', ''],
        '/^Metochion of the\s+/iu' => ['Metochion of ', ''],
        '/^Metochion of\s+/iu' => ['Metochion of ', ''],
    ];

    foreach ($rules as $pattern => $result) {
        if (preg_match($pattern, $main_raw)) {
            $prefix = $result[0];
            $name = preg_replace($pattern, '', $main_raw);
            return [$prefix, trim($name)];
        }
    }

    return [$prefix, $main_raw];
}

function shorten_religious_title(string $title): string
{
    if (mb_strlen($title) <= TITLE_MAX_LEN) {
        return $title;
    }

    $parts = explode(':', $title, 2);
    $main_raw = trim($parts[0]);
    $sub_raw = isset($parts[1]) ? trim($parts[1]) : '';

    [$prefix, $name] = extract_church_name($main_raw);

    $subtitle = 'Byzantine church in Veria, Greece';
    if (preg_match('/(\d{1,2}(?:th|st|nd|rd))(?:\s*[-–]\s*\d{1,2}(?:th|st|nd|rd))?\s*-?\s*century/iu', $sub_raw, $century)) {
        $subtitle = strtolower($century[0]) . ' church in Veria, Greece';
    } elseif (preg_match('/\b(modern|metropolitan|monastery|retreat|sanctuary|shrine|gem|jewel|treasure|beacon|oasis|haven|devotion|harmony)\b/iu', $sub_raw, $word)) {
        $subtitle = ucfirst(strtolower($word[0])) . ' in Veria, Greece';
    } elseif (preg_match('/veria|veroia|imathia|greece/iu', $sub_raw) && mb_strlen($sub_raw) <= 48) {
        $subtitle = $sub_raw;
    } elseif (preg_match('/veria|veroia/iu', $sub_raw)) {
        $subtitle = 'Historic church in Veria, Greece';
    }

    $short = $prefix . $name . ': ' . $subtitle;
    if (mb_strlen($short) > TITLE_MAX_LEN) {
        $short = $prefix . $name . ': Veria, Imathia';
    }
    if (mb_strlen($short) > TITLE_MAX_LEN) {
        $short = $name . ' – Veria, Greece';
    }
    if (mb_strlen($short) > TITLE_MAX_LEN) {
        $max_name = TITLE_MAX_LEN - mb_strlen(' – Veria, Greece');
        $trimmed = mb_substr($name, 0, max(20, $max_name));
        $trimmed = preg_replace('/\s+\S*$/u', '', $trimmed);
        $short = $trimmed . ' – Veria, Greece';
    }

    return $short;
}

echo "=== Optimizing Religious Sites excerpts and titles ===\n\n";

$restore_file = __DIR__ . '/religious_sites_title_restore.json';
$restore_titles = [];
if (is_readable($restore_file)) {
    $decoded = json_decode((string) file_get_contents($restore_file), true);
    if (is_array($decoded)) {
        $restore_titles = $decoded;
    }
}

$posts = get_posts([
    'post_type' => 'religious_site',
    'post_status' => 'publish',
    'numberposts' => -1,
]);

$excerpt_updates = 0;
$title_updates = 0;
$titles_only = in_array('--titles-only', $argv ?? [], true);

foreach ($posts as $post) {
    $plain_excerpt = trim(wp_strip_all_tags($post->post_excerpt));
    $update = [];

    if (!$titles_only && needs_custom_excerpt($post->post_excerpt, $plain_excerpt)) {
        $new_excerpt = build_seo_excerpt($post->post_content, $post->post_title);
        if ($new_excerpt !== $plain_excerpt) {
            $update['post_excerpt'] = $new_excerpt;
            $excerpt_updates++;
        }
    }

    $title_source = null;
    if (isset($restore_titles[(string) $post->ID])) {
        $title_source = $restore_titles[(string) $post->ID];
    } elseif (mb_strlen($post->post_title) > TITLE_MAX_LEN) {
        $title_source = $post->post_title;
    }

    if ($title_source !== null) {
        $new_title = shorten_religious_title($title_source);
        if ($new_title !== $post->post_title) {
            $update['post_title'] = $new_title;
            $title_updates++;
            echo "  Title [{$post->ID}]: " . mb_strlen($post->post_title) . " -> " . mb_strlen($new_title) . " chars\n";
            echo "    Was: {$post->post_title}\n";
            echo "    Now: {$new_title}\n";
        }
    }

    if (!empty($update)) {
        $update['ID'] = $post->ID;
        $result = wp_update_post($update, true);
        if (is_wp_error($result)) {
            echo "  ERROR post {$post->ID}: " . $result->get_error_message() . "\n";
        }
    }
}

echo "\nDone. Excerpts updated: {$excerpt_updates}. Titles shortened: {$title_updates}.\n";
