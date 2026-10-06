<?php
/**
 * Fix Religious Sites SEO content in WordPress:
 * - Replace broken Grok placeholder links
 * - Fill empty critical posts (194, 188)
 * - Expand Veria Synagogue (88)
 *
 * Run on VPS:
 *   php $WP_DOCUMENT_ROOT/wordpress/fix_religious_sites_seo_content.php
 */
if (!defined('WP_USE_THEMES')) {
    define('WP_USE_THEMES', false);
    require_once dirname(__DIR__) . '/wp-load.php';
}

if (!function_exists('update_field')) {
    fwrite(STDERR, "ACF plugin required.\n");
    exit(1);
}

function fix_grok_links(string $html): string
{
    $pattern = '/<a\s+([^>]*href=["\'])https:\/\/artifacts\.grokusercontent\.com[^"\']*(["\'][^>]*>)(.*?)<\/a>/is';
    return preg_replace_callback($pattern, function (array $m): string {
        $text = strtolower(wp_strip_all_tags($m[3]));
        if (strpos($text, 'map') !== false) {
            $url = 'https://veriaguide.gr/map';
        } elseif (strpos($text, 'museum') !== false) {
            $url = 'https://www.byzantine-museum-veria.gr/';
        } elseif (
            strpos($text, 'religious') !== false
            || strpos($text, 'byzantine') !== false
            || strpos($text, 'church') !== false
        ) {
            $url = 'https://veriaguide.gr/religious_sites';
        } elseif (strpos($text, 'veria') !== false) {
            $url = 'https://veriaguide.gr/';
        } else {
            $url = 'https://veriaguide.gr/religious_sites';
        }
        return '<a ' . $m[1] . esc_url($url) . $m[2] . $m[3] . '</a>';
    }, $html);
}

function update_religious_post(int $post_id, string $content, string $excerpt, ?array $location_map = null): void
{
    $result = wp_update_post([
        'ID' => $post_id,
        'post_content' => $content,
        'post_excerpt' => $excerpt,
    ], true);

    if (is_wp_error($result)) {
        echo "  ERROR updating post {$post_id}: " . $result->get_error_message() . "\n";
        return;
    }

    if ($location_map !== null) {
        update_field('location_map', $location_map, $post_id);
    }

    echo "  Updated post {$post_id}\n";
}

$peribleptos_content = <<<'HTML'
<p class="wp-block-paragraph">In the historic castle quarter of Veria (Veroia), Imathia, the <strong>Holy Church of the Virgin Mary Peribleptos</strong> is one of the town's most important Byzantine monuments. Dating from the 14th century, this three-aisled basilica preserves remarkable mural paintings from the 15th to 18th centuries and reflects Veria's deep Orthodox heritage. It belongs among the essential <a href="https://veriaguide.gr/religious_sites">Byzantine churches in Veria</a> for visitors exploring Macedonia, Greece.</p>

<h2 class="wp-block-heading">Architecture and Frescoes</h2>

<p class="wp-block-paragraph">The church follows the type of a three-aisled wooden-roofed basilica with a narthex. In the late 18th and early 19th centuries the building was extended westward and a timber gallery was added along the south side. Fifteenth-century frescoes survive in the central nave, while 18th-century wall paintings decorate the sanctuary and the east wall of the south aisle. A fine Palaeologan epistyle that once crowned the iconostasis is now preserved in the Relic Repository of the Holy Metropolis of Veria.</p>

<h2 class="wp-block-heading">Why Visit Peribleptos in Veria</h2>

<p class="wp-block-paragraph">Peribleptos offers a quiet, authentic encounter with Byzantine art away from the busiest tourist routes. Pair your visit with the <a href="https://www.byzantine-museum-veria.gr/" target="_blank" rel="noopener noreferrer">Byzantine Museum of Veria</a> to deepen your understanding of the region's Christian history, or continue to nearby churches on our <a href="https://veriaguide.gr/map">interactive map of Veria</a>.</p>

<h2 class="wp-block-heading">Practical Information</h2>

<ul class="wp-block-list">
<li><strong>Location:</strong> Thomaidi 26, Veria, Imathia, Greece. <a href="https://veriaguide.gr/map">View on map</a></li>
<li><strong>Visiting:</strong> Free access; respect ongoing worship and restoration work.</li>
<li><strong>More churches:</strong> Browse all <a href="https://veriaguide.gr/religious_sites">religious sites in Veria</a>.</li>
</ul>
HTML;

$peribleptos_excerpt = 'Visit the Holy Church of the Virgin Mary Peribleptos in Veria (Veroia), Imathia — a 14th-century Byzantine basilica with remarkable frescoes and a key stop on any church tour of Greece.';

$timothy_content = <<<'HTML'
<p class="wp-block-paragraph">On A. Kemintze Street in Veria (Veroia), Imathia, the <strong>Holy Church of Saint Timothy</strong> serves the local Greek Orthodox community as a place of prayer and pilgrimage. Dedicated to the apostolic saint, it stands among the living <a href="https://veriaguide.gr/religious_sites">religious sites in Veria</a> that connect visitors with the town's enduring faith and Macedonian heritage.</p>

<h2 class="wp-block-heading">A Sacred Tribute to Saint Timothy</h2>

<p class="wp-block-paragraph">Saint Timothy is honoured in the Orthodox tradition as a companion of the Apostle Paul and a foundational figure of the early Church. In Veria — a city closely linked to Paul's missionary journey through Macedonia — churches such as this one keep that legacy present in daily worship and community life. The Holy Church of Saint Timothy offers a welcoming space for quiet reflection in the heart of Imathia.</p>

<h2 class="wp-block-heading">Visiting the Church</h2>

<p class="wp-block-paragraph">The church is located in central Veria and is open for visitors who wish to attend services or explore the town's network of Byzantine and post-Byzantine churches. Combine your visit with the nearby <a href="https://veriaguide.gr/map">map of Veria's sacred sites</a> to plan a walking route through the old town.</p>

<h2 class="wp-block-heading">Practical Information</h2>

<ul class="wp-block-list">
<li><strong>Location:</strong> Holy Church of Saint Timothy, A. Kemintze, Veria, Imathia, Greece. <a href="https://veriaguide.gr/map">View on map</a></li>
<li><strong>Visiting:</strong> Free access without ticket; dress respectfully.</li>
<li><strong>Explore more:</strong> See all <a href="https://veriaguide.gr/religious_sites">churches and monasteries in Veria</a>.</li>
</ul>
HTML;

$timothy_excerpt = 'Visit the Holy Church of Saint Timothy in Veria (Veroia), Imathia, Greece — a Greek Orthodox church linked to the apostolic legacy of Saint Paul\'s Macedonia.';

$synagogue_content = <<<'HTML'
<p class="wp-block-paragraph">In the historic Barbouta quarter of Veria (Veroia), Imathia, the <strong>Veria Synagogue</strong> preserves one of the most important traces of the city's Jewish heritage in northern Greece. This restored synagogue reflects centuries of cultural life in Veria and offers visitors a moving counterpart to the town's celebrated <a href="https://veriaguide.gr/religious_sites">Byzantine churches</a> and museums.</p>

<h2 class="wp-block-heading">Jewish Heritage in Veria</h2>

<p class="wp-block-paragraph">Veria was home to a vibrant Jewish community for many centuries. The synagogue in Barbouta, with its ornate interior and restrained exterior, is a reminder of that shared history and of the traditions that shaped the town alongside its Orthodox monuments. Cultural visits and remembrance events are organised with respect for the site's significance.</p>

<h2 class="wp-block-heading">Planning Your Visit</h2>

<p class="wp-block-paragraph">Access is often by appointment; check opening hours before you travel. The synagogue sits within walking distance of other landmarks in Veria's old town. Use our <a href="https://veriaguide.gr/map">interactive map</a> to combine your visit with museums, churches and archaeological sites across Imathia.</p>

<h2 class="wp-block-heading">Practical Information</h2>

<ul class="wp-block-list">
<li><strong>Location:</strong> Jewish Synagogue of Veria, Olganou, Veria, Imathia, Greece. <a href="https://veriaguide.gr/map">View on map</a></li>
<li><strong>Hours:</strong> Typically 10:00–16:00 by appointment; confirm locally.</li>
<li><strong>Guidelines:</strong> Respectful behaviour; check for event schedules.</li>
<li><strong>More in Veria:</strong> <a href="https://veriaguide.gr/religious_sites">Religious and sacred sites</a> · <a href="https://veriaguide.gr/archaeological_sites">Archaeological sites</a></li>
</ul>
HTML;

$synagogue_excerpt = 'Visit the Veria Synagogue in Barbouta, Veria (Veroia), Imathia — a preserved Jewish heritage site reflecting centuries of cultural history in northern Greece.';

echo "=== Fixing Religious Sites SEO content ===\n\n";

echo "1. Critical / weak posts\n";
update_religious_post(194, $peribleptos_content, $peribleptos_excerpt, [
    'address' => 'Holy Church of the Virgin Mary Peribleptos, Thomaidi 26, Veria, Greece',
    'lat' => 40.52385,
    'lng' => 22.20142,
    'zoom' => 16,
    'place_id' => '',
    'name' => 'Holy Church of the Virgin Mary Peribleptos',
]);
update_religious_post(188, $timothy_content, $timothy_excerpt);
update_religious_post(88, $synagogue_content, $synagogue_excerpt);

echo "\n2. Fixing Grok links in all religious_site posts\n";
$posts = get_posts([
    'post_type' => 'religious_site',
    'post_status' => 'publish',
    'numberposts' => -1,
    'fields' => 'ids',
]);

$fixed = 0;
foreach ($posts as $post_id) {
    $post = get_post($post_id);
    if (!$post) {
        continue;
    }
    $original = $post->post_content;
    if (strpos($original, 'grokusercontent') === false) {
        continue;
    }
    $updated = fix_grok_links($original);
    if ($updated !== $original) {
        wp_update_post([
            'ID' => $post_id,
            'post_content' => $updated,
        ]);
        echo "  Fixed links in post {$post_id} ({$post->post_name})\n";
        $fixed++;
    }
}

echo "\nDone. Updated content: 3 posts. Fixed Grok links: {$fixed} posts.\n";
