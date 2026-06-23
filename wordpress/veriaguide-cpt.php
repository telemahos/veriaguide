<?php
/**
 * Plugin Name: VeriaGuide Custom Post Types
 * Description: Custom post types and REST API for VeriaGuide tourism directory
 * Version: 1.1
 * Author: VeriaGuide Team
 */

if (!defined('ABSPATH')) {
    exit;
}

class VeriaGuideCustomPostTypes {

    public function __construct() {
        add_action('init', array($this, 'register_post_types'));
        add_action('rest_api_init', array($this, 'register_rest_fields'));
        add_action('rest_api_init', array($this, 'register_custom_routes'));
    }

    public function register_post_types() {
        $post_types = array(
            'religious_site' => array('name' => 'Religious Sites', 'singular' => 'Religious Site', 'rest_base' => 'religious_sites'),
            'museum' => array('name' => 'Museums', 'singular' => 'Museum', 'rest_base' => 'museums'),
            'archaeological_site' => array('name' => 'Archaeological Sites', 'singular' => 'Archaeological Site', 'rest_base' => 'archaeological_sites'),
            'hiking_trail' => array('name' => 'Hiking Trails', 'singular' => 'Hiking Trail', 'rest_base' => 'hiking_trails'),
            'restaurant' => array('name' => 'Restaurants', 'singular' => 'Restaurant', 'rest_base' => 'restaurants'),
            'cafe' => array('name' => 'Cafes', 'singular' => 'Cafe', 'rest_base' => 'cafes'),
            'accommodation' => array('name' => 'Accommodations', 'singular' => 'Accommodation', 'rest_base' => 'accommodations'),
            'ski_resort' => array('name' => 'Ski Resorts', 'singular' => 'Ski Resort', 'rest_base' => 'ski_resorts'),
            'tour' => array('name' => 'Tours', 'singular' => 'Tour', 'rest_base' => 'tours'),
            'hidden_gem' => array('name' => 'Hidden Gems', 'singular' => 'Hidden Gem', 'rest_base' => 'hidden_gems'),
        );

        foreach ($post_types as $post_type => $config) {
            register_post_type($post_type, array(
                'labels' => array(
                    'name' => $config['name'],
                    'singular_name' => $config['singular'],
                    'add_new' => 'Add New',
                    'add_new_item' => 'Add New ' . $config['singular'],
                    'edit_item' => 'Edit ' . $config['singular'],
                    'new_item' => 'New ' . $config['singular'],
                    'view_item' => 'View ' . $config['singular'],
                    'search_items' => 'Search ' . $config['name'],
                    'not_found' => 'No ' . strtolower($config['name']) . ' found',
                    'not_found_in_trash' => 'No ' . strtolower($config['name']) . ' found in trash',
                ),
                'public' => true,
                'publicly_queryable' => true,
                'show_ui' => true,
                'show_in_menu' => true,
                'show_in_rest' => true,
                'rest_base' => $config['rest_base'],
                'query_var' => true,
                'rewrite' => array('slug' => $config['rest_base']),
                'capability_type' => 'post',
                'has_archive' => true,
                'hierarchical' => false,
                'menu_position' => 20,
                'supports' => array('title', 'editor', 'thumbnail', 'excerpt', 'custom-fields'),
                'menu_icon' => 'dashicons-location-alt',
            ));
        }

        if (get_option('veriaguide_cpt_flush_rewrite_rules') !== 'done') {
            flush_rewrite_rules();
            update_option('veriaguide_cpt_flush_rewrite_rules', 'done');
        }
    }

    public function register_rest_fields() {
        $post_types = array(
            'religious_site', 'museum', 'archaeological_site', 'hiking_trail',
            'restaurant', 'cafe', 'accommodation', 'ski_resort', 'tour', 'hidden_gem',
        );

        foreach ($post_types as $post_type) {
            register_rest_field($post_type, 'acf', array(
                'get_callback' => array($this, 'get_acf_fields'),
                'schema' => null,
            ));
        }
    }

    public function register_custom_routes() {
        register_rest_route('veriaguide/v1', '/homepage-settings', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_homepage_settings'),
            'permission_callback' => '__return_true',
        ));

        register_rest_route('veriaguide/v1', '/menus', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_menus'),
            'permission_callback' => '__return_true',
        ));
    }

    public function get_acf_fields($object) {
        if (function_exists('get_fields')) {
            return get_fields($object['id']);
        }
        return array();
    }

    public function get_homepage_settings($request) {
        $default_sections = array(
            array('category' => 'museums', 'post_type' => 'museum', 'title' => 'Museums', 'enabled' => true, 'items_count' => 4, 'order' => 1, 'view_all_link' => '/museums'),
            array('category' => 'archaeological_sites', 'post_type' => 'archaeological_site', 'title' => 'Archaeological Sites', 'enabled' => true, 'items_count' => 4, 'order' => 2, 'view_all_link' => '/archaeological_sites'),
            array('category' => 'religious_sites', 'post_type' => 'religious_site', 'title' => 'Churches & Monasteries', 'enabled' => true, 'items_count' => 4, 'order' => 3, 'view_all_link' => '/religious_sites'),
            array('category' => 'restaurants', 'post_type' => 'restaurant', 'title' => 'Restaurants', 'enabled' => true, 'items_count' => 4, 'order' => 4, 'view_all_link' => '/restaurants'),
            array('category' => 'cafes', 'post_type' => 'cafe', 'title' => 'Cafés', 'enabled' => true, 'items_count' => 4, 'order' => 5, 'view_all_link' => '/cafes'),
            array('category' => 'accommodations', 'post_type' => 'accommodation', 'title' => 'Accommodations', 'enabled' => true, 'items_count' => 4, 'order' => 6, 'view_all_link' => '/accommodations'),
            array('category' => 'ski_resorts', 'post_type' => 'ski_resort', 'title' => 'Ski Resorts', 'enabled' => true, 'items_count' => 4, 'order' => 7, 'view_all_link' => '/ski_resorts'),
        );

        $default_hero = array(
            'slides' => array(
                array('image_url' => '/static/img/veria-hero2.webp', 'title' => '', 'subtitle' => ''),
            ),
            'speed' => 6,
        );

        $sections = $default_sections;
        $hero = $default_hero;
        $about_text = '';

        if (function_exists('get_field')) {
            $acf_sections = get_field('homepage_sections', 'option');
            if (is_array($acf_sections) && !empty($acf_sections)) {
                $sections = $acf_sections;
            }

            $acf_slides = get_field('hero_slides', 'option');
            $acf_speed = get_field('hero_speed', 'option');
            if (is_array($acf_slides) && !empty($acf_slides)) {
                $slides = array();
                foreach ($acf_slides as $slide) {
                    $image_url = '';
                    if (!empty($slide['image'])) {
                        if (is_array($slide['image']) && !empty($slide['image']['url'])) {
                            $image_url = $slide['image']['url'];
                        } elseif (is_numeric($slide['image'])) {
                            $image_url = wp_get_attachment_url($slide['image']);
                        } elseif (is_string($slide['image'])) {
                            $image_url = $slide['image'];
                        }
                    }
                    $slides[] = array(
                        'image_url' => $image_url ?: '/static/img/veria-hero2.webp',
                        'title' => isset($slide['title']) ? $slide['title'] : '',
                        'subtitle' => isset($slide['subtitle']) ? $slide['subtitle'] : '',
                    );
                }
                $hero = array(
                    'slides' => $slides,
                    'speed' => is_numeric($acf_speed) ? (int) $acf_speed : 6,
                );
            }

            $acf_about = get_field('about_text', 'option');
            if (is_string($acf_about) && $acf_about !== '') {
                $about_text = $acf_about;
            }
        }

        return rest_ensure_response(array(
            'sections' => $sections,
            'hero' => $hero,
            'about_text' => $about_text,
        ));
    }

    public function get_menus($request) {
        $menus = array();
        $locations = get_nav_menu_locations();

        if (empty($locations)) {
            return rest_ensure_response($menus);
        }

        foreach ($locations as $location => $menu_id) {
            $menu_obj = wp_get_nav_menu_object($menu_id);
            if (!$menu_obj) {
                continue;
            }

            $items = wp_get_nav_menu_items($menu_id);
            if (!$items) {
                continue;
            }

            $menus[] = array(
                'name' => $menu_obj->name,
                'slug' => $menu_obj->slug,
                'location' => $location,
                'items' => $this->build_menu_tree($items),
            );
        }

        return rest_ensure_response($menus);
    }

    private function build_menu_tree($items, $parent_id = 0) {
        $branch = array();

        foreach ($items as $item) {
            if ((int) $item->menu_item_parent !== (int) $parent_id) {
                continue;
            }

            $children = $this->build_menu_tree($items, $item->ID);
            $entry = array(
                'title' => $item->title,
                'url' => $item->url,
            );

            if (!empty($children)) {
                $entry['children'] = $children;
            }

            $branch[] = $entry;
        }

        return $branch;
    }
}

new VeriaGuideCustomPostTypes();

register_activation_hook(__FILE__, function () {
    delete_option('veriaguide_cpt_flush_rewrite_rules');
});
