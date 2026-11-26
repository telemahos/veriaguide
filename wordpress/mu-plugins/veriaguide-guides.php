<?php
/**
 * Plugin Name: VeriaGuide Guides
 * Description: Guide CPT plus English SEO meta for listing post types. Drop-in mu-plugin; does not replace veriaguide-cpt.php.
 * Version: 1.0.0
 *
 * Install on the server (live WordPress is not this repo file):
 *   cp wordpress/mu-plugins/veriaguide-guides.php /path/to/wp-content/mu-plugins/veriaguide-guides.php
 * mu-plugins load automatically. No plugin screen activation. The first request flushes rewrite rules once.
 *
 * The live copy of wp-content/plugins/veriaguide-cpt.php already registers seo_title_en /
 * seo_description_en and the EL/DE SEO meta. This file registers the English SEO keys only
 * when they are missing, and always registers the guide post type.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Listing CPTs that share the directory, plus guide.
 *
 * @return string[]
 */
function veriaguide_guide_post_types() {
    return array(
        'museum',
        'archaeological_site',
        'religious_site',
        'hiking_trail',
        'restaurant',
        'cafe',
        'accommodation',
        'ski_resort',
        'tour',
        'hidden_gem',
        'guide',
    );
}

/**
 * Editors (and anyone who can edit posts) may write these keys over REST.
 */
function veriaguide_guide_meta_auth() {
    return current_user_can('edit_posts');
}

/**
 * @param string $post_type
 * @param string $field
 * @param callable $sanitize
 */
function veriaguide_register_meta_once($post_type, $field, $sanitize) {
    $existing = get_registered_meta_keys('post', $post_type);
    if (isset($existing[$field])) {
        return;
    }
    register_post_meta($post_type, $field, array(
        'type' => 'string',
        'single' => true,
        'show_in_rest' => true,
        'sanitize_callback' => $sanitize,
        'auth_callback' => 'veriaguide_guide_meta_auth',
    ));
}

function veriaguide_register_guide_post_type() {
    register_post_type('guide', array(
        'labels' => array(
            'name' => 'Guides',
            'singular_name' => 'Guide',
            'add_new' => 'Add New',
            'add_new_item' => 'Add New Guide',
            'edit_item' => 'Edit Guide',
            'new_item' => 'New Guide',
            'view_item' => 'View Guide',
            'search_items' => 'Search Guides',
            'not_found' => 'No guides found',
            'not_found_in_trash' => 'No guides found in trash',
        ),
        'public' => true,
        'publicly_queryable' => true,
        'show_ui' => true,
        'show_in_menu' => true,
        'show_in_rest' => true,
        'rest_base' => 'guides',
        'query_var' => true,
        'rewrite' => array('slug' => 'guides'),
        'capability_type' => 'post',
        'has_archive' => false,
        'hierarchical' => false,
        'menu_position' => 21,
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail', 'custom-fields'),
        'menu_icon' => 'dashicons-book-alt',
    ));
}

function veriaguide_register_guide_meta() {
    $guide_fields = array(
        'title_el' => 'sanitize_text_field',
        'excerpt_el' => 'wp_kses_post',
        'content_el' => 'wp_kses_post',
        'title_de' => 'sanitize_text_field',
        'excerpt_de' => 'wp_kses_post',
        'content_de' => 'wp_kses_post',
        'seo_title_el' => 'sanitize_text_field',
        'seo_description_el' => 'sanitize_textarea_field',
        'seo_title_de' => 'sanitize_text_field',
        'seo_description_de' => 'sanitize_textarea_field',
        'seo_title_en' => 'sanitize_text_field',
        'seo_description_en' => 'sanitize_textarea_field',
    );
    foreach ($guide_fields as $field => $sanitize) {
        veriaguide_register_meta_once('guide', $field, $sanitize);
    }

    $english_seo = array(
        'seo_title_en' => 'sanitize_text_field',
        'seo_description_en' => 'sanitize_textarea_field',
    );
    foreach (veriaguide_guide_post_types() as $post_type) {
        if ($post_type === 'guide') {
            continue;
        }
        foreach ($english_seo as $field => $sanitize) {
            veriaguide_register_meta_once($post_type, $field, $sanitize);
        }
    }
}

function veriaguide_guides_init() {
    veriaguide_register_guide_post_type();
    veriaguide_register_guide_meta();

    if (get_option('veriaguide_guide_cpt_rewrite') !== '1') {
        flush_rewrite_rules(false);
        update_option('veriaguide_guide_cpt_rewrite', '1');
    }
}

add_action('init', 'veriaguide_guides_init', 11);
