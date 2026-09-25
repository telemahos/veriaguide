<?php
/**
 * Plugin Name: VeriaGuide Custom Post Types
 * Description: Custom post types and REST API for VeriaGuide tourism directory
 * Version: 1.4
 * Author: VeriaGuide Team
 */

if (!defined('ABSPATH')) {
    exit;
}

class VeriaGuideCustomPostTypes {

    public function __construct() {
        add_action('init', array($this, 'register_post_types'));
        add_action('init', array($this, 'register_translation_meta'));
        add_action('phpmailer_init', array($this, 'use_domain_sender'));
        add_action('rest_api_init', array($this, 'register_rest_fields'));
        add_action('rest_api_init', array($this, 'register_custom_routes'));
        add_action('acf/init', array($this, 'register_acf_options'));
        add_action('after_setup_theme', array($this, 'register_nav_menus'));
        add_action('init', array($this, 'fix_site_name'), 20);
        add_action('init', array($this, 'seed_homepage_defaults'), 21);
        add_action('init', array($this, 'seed_navigation_menu'), 22);
    }

    public function register_nav_menus() {
        register_nav_menus(array(
            'primary' => 'Primary Navigation',
        ));
    }

    public function fix_site_name() {
        if (get_option('blogname') === 'Veoia Guide') {
            update_option('blogname', 'Veria Guide');
        }
    }

    public function register_acf_options() {
        if (!function_exists('acf_add_options_page')) {
            return;
        }

        acf_add_options_page(array(
            'page_title' => 'Homepage Settings',
            'menu_title' => 'Homepage Settings',
            'menu_slug' => 'veriaguide-homepage',
            'capability' => 'edit_posts',
            'redirect' => false,
            'icon_url' => 'dashicons-admin-home',
            'position' => 25,
        ));

        acf_add_local_field_group(array(
            'key' => 'group_veriaguide_homepage',
            'title' => 'Homepage Settings',
            'fields' => array(
                array(
                    'key' => 'field_veriaguide_hero_slides',
                    'label' => 'Hero Slides',
                    'name' => 'hero_slides',
                    'type' => 'repeater',
                    'layout' => 'block',
                    'button_label' => 'Add Slide',
                    'sub_fields' => array(
                        array(
                            'key' => 'field_veriaguide_slide_image_url',
                            'label' => 'Image URL',
                            'name' => 'image_url',
                            'type' => 'text',
                            'instructions' => 'e.g. /static/img/veria-hero2.webp or a full image URL',
                        ),
                        array(
                            'key' => 'field_veriaguide_slide_title',
                            'label' => 'Title',
                            'name' => 'title',
                            'type' => 'text',
                        ),
                        array(
                            'key' => 'field_veriaguide_slide_subtitle',
                            'label' => 'Subtitle',
                            'name' => 'subtitle',
                            'type' => 'textarea',
                            'rows' => 3,
                        ),
                    ),
                ),
                array(
                    'key' => 'field_veriaguide_hero_speed',
                    'label' => 'Hero Slide Speed (seconds)',
                    'name' => 'hero_speed',
                    'type' => 'number',
                    'default_value' => 6,
                    'min' => 3,
                    'max' => 30,
                ),
                array(
                    'key' => 'field_veriaguide_about_text',
                    'label' => 'About Veria Text',
                    'name' => 'about_text',
                    'type' => 'wysiwyg',
                    'tabs' => 'visual',
                    'toolbar' => 'basic',
                    'media_upload' => 0,
                ),
                array(
                    'key' => 'field_veriaguide_homepage_sections',
                    'label' => 'Homepage Sections',
                    'name' => 'homepage_sections',
                    'type' => 'repeater',
                    'layout' => 'block',
                    'button_label' => 'Add Section',
                    'instructions' => 'Configure which content sections appear on the homepage and in what order.',
                    'sub_fields' => array(
                        array(
                            'key' => 'field_veriaguide_section_category',
                            'label' => 'Category Key',
                            'name' => 'category',
                            'type' => 'text',
                            'instructions' => 'e.g. museums, restaurants',
                        ),
                        array(
                            'key' => 'field_veriaguide_section_post_type',
                            'label' => 'Post Type',
                            'name' => 'post_type',
                            'type' => 'select',
                            'choices' => array(
                                'museum' => 'Museum',
                                'archaeological_site' => 'Archaeological Site',
                                'religious_site' => 'Religious Site',
                                'restaurant' => 'Restaurant',
                                'cafe' => 'Cafe',
                                'accommodation' => 'Accommodation',
                                'ski_resort' => 'Ski Resort',
                                'hiking_trail' => 'Hiking Trail',
                                'hidden_gem' => 'Hidden Gem',
                                'tour' => 'Tour',
                            ),
                        ),
                        array(
                            'key' => 'field_veriaguide_section_title',
                            'label' => 'Section Title',
                            'name' => 'title',
                            'type' => 'text',
                        ),
                        array(
                            'key' => 'field_veriaguide_section_enabled',
                            'label' => 'Enabled',
                            'name' => 'enabled',
                            'type' => 'true_false',
                            'default_value' => 1,
                            'ui' => 1,
                        ),
                        array(
                            'key' => 'field_veriaguide_section_items_count',
                            'label' => 'Items to Show',
                            'name' => 'items_count',
                            'type' => 'number',
                            'default_value' => 4,
                            'min' => 1,
                            'max' => 20,
                        ),
                        array(
                            'key' => 'field_veriaguide_section_order',
                            'label' => 'Display Order',
                            'name' => 'order',
                            'type' => 'number',
                            'default_value' => 1,
                            'min' => 1,
                        ),
                        array(
                            'key' => 'field_veriaguide_section_view_all',
                            'label' => 'View All Link',
                            'name' => 'view_all_link',
                            'type' => 'text',
                            'instructions' => 'e.g. /museums',
                        ),
                    ),
                ),
            ),
            'location' => array(
                array(
                    array(
                        'param' => 'options_page',
                        'operator' => '==',
                        'value' => 'veriaguide-homepage',
                    ),
                ),
            ),
        ));
    }

    public function seed_homepage_defaults() {
        if (!function_exists('update_field')) {
            return;
        }

        $existing_sections = get_field('homepage_sections', 'option');
        if (empty($existing_sections)) {
            update_field('homepage_sections', $this->get_default_sections(), 'option');
        }

        if (get_option('veriaguide_homepage_seeded') === 'done') {
            return;
        }

        $existing_slides = get_field('hero_slides', 'option');
        if (empty($existing_slides)) {
            update_field('hero_slides', array(
                array(
                    'image_url' => '/static/img/veria-hero2.webp',
                    'title' => 'Veria, Greece: Byzantine Churches & Macedonian Heritage',
                    'subtitle' => 'Explore Veria (Veroia) in Imathia — 60+ Byzantine churches, museums, Royal Tombs of Vergina and the Vema where Apostle Paul preached.',
                ),
            ), 'option');
        }

        if (!get_field('hero_speed', 'option')) {
            update_field('hero_speed', 6, 'option');
        }

        if (!get_field('about_text', 'option')) {
            update_field('about_text', '<p>Discover Veria (Veroia), a historic city in Imathia, northern Greece, where Byzantine churches, museums and archaeological treasures meet Macedonian heritage. Use Veria Guide to explore churches linked to Apostle Paul, the Royal Tombs of Vergina and hidden gems across the region.</p>', 'option');
        }

        update_option('veriaguide_homepage_seeded', 'done');
    }

    private function get_default_sections() {
        return array(
            array('category' => 'religious_sites', 'post_type' => 'religious_site', 'title' => 'Churches & Monasteries', 'enabled' => true, 'items_count' => 4, 'order' => 1, 'view_all_link' => '/religious-sites'),
            array('category' => 'museums', 'post_type' => 'museum', 'title' => 'Museums', 'enabled' => true, 'items_count' => 4, 'order' => 2, 'view_all_link' => '/museums'),
            array('category' => 'archaeological_sites', 'post_type' => 'archaeological_site', 'title' => 'Archaeological Sites', 'enabled' => true, 'items_count' => 4, 'order' => 3, 'view_all_link' => '/archaeological-sites'),
        );
    }

    public function seed_navigation_menu() {
        if (get_option('veriaguide_nav_seeded') === 'done') {
            return;
        }

        $menu_name = 'Primary Navigation';
        $menu_obj = wp_get_nav_menu_object($menu_name);

        if (!$menu_obj) {
            $menu_id = wp_create_nav_menu($menu_name);
            if (is_wp_error($menu_id)) {
                return;
            }
        } else {
            $menu_id = $menu_obj->term_id;
        }

        $existing_items = wp_get_nav_menu_items($menu_id);
        if (empty($existing_items)) {
            $this->create_default_menu_items($menu_id);
        }

        $locations = get_theme_mod('nav_menu_locations');
        if (!is_array($locations)) {
            $locations = array();
        }
        if (empty($locations['primary'])) {
            $locations['primary'] = $menu_id;
            set_theme_mod('nav_menu_locations', $locations);
        }

        update_option('veriaguide_nav_seeded', 'done');
    }

    private function create_default_menu_items($menu_id) {
        $site_url = home_url('/');

        $home_id = wp_update_nav_menu_item($menu_id, 0, array(
            'menu-item-title' => 'Home',
            'menu-item-url' => $site_url,
            'menu-item-status' => 'publish',
        ));

        $destinations_id = wp_update_nav_menu_item($menu_id, 0, array(
            'menu-item-title' => 'Destinations',
            'menu-item-url' => '#',
            'menu-item-status' => 'publish',
        ));

        $destination_children = array(
            array('Museums', '/museums'),
            array('Archaeological Sites', '/archaeological-sites'),
            array('Religious Sites', '/religious-sites'),
            array('Ski Resorts', '/ski-resorts'),
            array('Interactive Map', '/map'),
        );

        foreach ($destination_children as $child) {
            wp_update_nav_menu_item($menu_id, 0, array(
                'menu-item-title' => $child[0],
                'menu-item-url' => home_url($child[1]),
                'menu-item-parent-id' => $destinations_id,
                'menu-item-status' => 'publish',
            ));
        }

        $food_id = wp_update_nav_menu_item($menu_id, 0, array(
            'menu-item-title' => 'Food & Drink',
            'menu-item-url' => '#',
            'menu-item-status' => 'publish',
        ));

        foreach (array(array('Restaurants', '/restaurants'), array('Cafés', '/cafes')) as $child) {
            wp_update_nav_menu_item($menu_id, 0, array(
                'menu-item-title' => $child[0],
                'menu-item-url' => home_url($child[1]),
                'menu-item-parent-id' => $food_id,
                'menu-item-status' => 'publish',
            ));
        }

        wp_update_nav_menu_item($menu_id, 0, array(
            'menu-item-title' => 'Accommodations',
            'menu-item-url' => home_url('/accommodations'),
            'menu-item-status' => 'publish',
        ));

        wp_update_nav_menu_item($menu_id, 0, array(
            'menu-item-title' => 'Contact',
            'menu-item-url' => home_url('/contact'),
            'menu-item-status' => 'publish',
        ));
    }

    private function normalize_sections($sections) {
        if (!is_array($sections)) {
            return $this->get_default_sections();
        }

        $normalized = array();
        foreach ($sections as $section) {
            if (!is_array($section) || empty($section['post_type'])) {
                continue;
            }

            $category = !empty($section['category'])
                ? $section['category']
                : str_replace('-', '_', $section['post_type']) . 's';

            $normalized[] = array(
                'category' => $category,
                'post_type' => $section['post_type'],
                'title' => isset($section['title']) ? $section['title'] : '',
                'enabled' => !empty($section['enabled']),
                'items_count' => isset($section['items_count']) ? (int) $section['items_count'] : 4,
                'order' => isset($section['order']) ? (int) $section['order'] : 99,
                'view_all_link' => !empty($section['view_all_link'])
                    ? $section['view_all_link']
                    : '/' . $category,
            );
        }

        if (empty($normalized)) {
            return $this->get_default_sections();
        }

        usort($normalized, function ($a, $b) {
            return $a['order'] - $b['order'];
        });

        return $normalized;
    }

    private function get_default_hero() {
        return array(
            'slides' => array(
                array(
                    'image_url' => '/static/img/veria-hero2.webp',
                    'title' => 'Veria, Greece: Byzantine Churches & Macedonian Heritage',
                    'subtitle' => 'Explore Veria (Veroia) in Imathia — 60+ Byzantine churches, museums, Royal Tombs of Vergina and the Vema where Apostle Paul preached.',
                ),
            ),
            'speed' => 6,
        );
    }

    private function get_default_about_text() {
        return '<p>Discover Veria (Veroia), a historic city in Imathia, northern Greece, where Byzantine churches, museums and archaeological treasures meet Macedonian heritage. Use Veria Guide to explore churches linked to Apostle Paul, the Royal Tombs of Vergina and hidden gems across the region.</p>';
    }

    private function resolve_slide_image_url($slide) {
        if (!empty($slide['image_url']) && is_string($slide['image_url'])) {
            return $slide['image_url'];
        }
        if (!empty($slide['image'])) {
            if (is_array($slide['image']) && !empty($slide['image']['url'])) {
                return $slide['image']['url'];
            }
            if (is_numeric($slide['image'])) {
                $url = wp_get_attachment_url($slide['image']);
                if ($url) {
                    return $url;
                }
            }
            if (is_string($slide['image'])) {
                return $slide['image'];
            }
        }
        return '/static/img/veria-hero2.webp';
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

    public function register_translation_meta() {
        $post_types = array(
            'religious_site', 'museum', 'archaeological_site', 'hiking_trail',
            'restaurant', 'cafe', 'accommodation', 'ski_resort', 'tour', 'hidden_gem',
        );
        $fields = array(
            'title_el' => 'sanitize_text_field',
            'excerpt_el' => 'wp_kses_post',
            'content_el' => 'wp_kses_post',
        );

        foreach ($post_types as $post_type) {
            foreach ($fields as $field => $sanitize) {
                register_post_meta($post_type, $field, array(
                    'type' => 'string',
                    'single' => true,
                    'show_in_rest' => true,
                    'sanitize_callback' => $sanitize,
                    'auth_callback' => function () {
                        return current_user_can('edit_posts');
                    },
                ));
            }
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

        register_rest_route('veriaguide/v1', '/contact', array(
            'methods' => 'POST',
            'callback' => array($this, 'send_contact_message'),
            'permission_callback' => function () {
                return current_user_can('edit_posts');
            },
            'args' => array(
                'name' => array('required' => true, 'type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
                'email' => array('required' => true, 'type' => 'string', 'validate_callback' => 'is_email', 'sanitize_callback' => 'sanitize_email'),
                'subject' => array('required' => true, 'type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
                'message' => array('required' => true, 'type' => 'string', 'sanitize_callback' => 'sanitize_textarea_field'),
            ),
        ));

        register_rest_route('veriaguide/v1', '/translation', array(
            'methods' => 'POST',
            'callback' => array($this, 'save_translation'),
            'permission_callback' => function () {
                return current_user_can('edit_posts');
            },
            'args' => array(
                'id' => array('required' => true, 'type' => 'integer'),
                'title_el' => array('required' => false, 'type' => 'string'),
                'excerpt_el' => array('required' => false, 'type' => 'string'),
                'content_el' => array('required' => false, 'type' => 'string'),
            ),
        ));
    }

    public function save_translation($request) {
        $post = get_post((int) $request['id']);
        if (!$post) {
            return new WP_Error('not_found', 'Post not found', array('status' => 404));
        }
        $allowed = array(
            'religious_site', 'museum', 'archaeological_site', 'hiking_trail',
            'restaurant', 'cafe', 'accommodation', 'ski_resort', 'tour', 'hidden_gem',
        );
        if (!in_array($post->post_type, $allowed, true)) {
            return new WP_Error('invalid_type', 'Unsupported post type', array('status' => 400));
        }

        if ($request->get_param('title_el') !== null) {
            update_post_meta($post->ID, 'title_el', sanitize_text_field($request['title_el']));
        }
        if ($request->get_param('excerpt_el') !== null) {
            update_post_meta($post->ID, 'excerpt_el', wp_kses_post($request['excerpt_el']));
        }
        if ($request->get_param('content_el') !== null) {
            update_post_meta($post->ID, 'content_el', wp_kses_post($request['content_el']));
        }
        return array('success' => true, 'id' => $post->ID);
    }

    public function use_domain_sender($phpmailer) {
        // Gmail rejects or spam-files mail whose envelope sender is the server hostname (SPF fails).
        $phpmailer->setFrom('info@veriaguide.gr', 'VeriaGuide', false);
        $phpmailer->Sender = 'info@veriaguide.gr';
    }

    public function send_contact_message($request) {
        $name = str_replace(array("\r", "\n"), '', $request['name']);
        $email = $request['email'];
        $subject = str_replace(array("\r", "\n"), '', $request['subject']);

        $body = "Name: {$name}\nE-Mail: {$email}\n\n" . $request['message'];
        $headers = array('Reply-To: ' . $name . ' <' . $email . '>');

        $sent = wp_mail(get_option('admin_email'), '[VeriaGuide] ' . $subject, $body, $headers);
        if (!$sent) {
            return new WP_Error('mail_failed', 'Message could not be sent', array('status' => 502));
        }
        return array('success' => true);
    }

    public function get_acf_fields($object) {
        if (function_exists('get_fields')) {
            return get_fields($object['id']);
        }
        return array();
    }

    public function get_homepage_settings($request) {
        $default_sections = $this->get_default_sections();
        $default_hero = $this->get_default_hero();
        $sections = $default_sections;
        $hero = $default_hero;
        $about_text = $this->get_default_about_text();

        if (function_exists('get_field')) {
            $acf_sections = get_field('homepage_sections', 'option');
            if (is_array($acf_sections) && !empty($acf_sections)) {
                $sections = $this->normalize_sections($acf_sections);
            }

            $acf_slides = get_field('hero_slides', 'option');
            $acf_speed = get_field('hero_speed', 'option');
            if (is_array($acf_slides) && !empty($acf_slides)) {
                $slides = array();
                foreach ($acf_slides as $slide) {
                    $slides[] = array(
                        'image_url' => $this->resolve_slide_image_url($slide),
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
    delete_option('veriaguide_homepage_seeded');
    delete_option('veriaguide_nav_seeded');
    if (get_option('blogname') === 'Veoia Guide') {
        update_option('blogname', 'Veria Guide');
    }
});
