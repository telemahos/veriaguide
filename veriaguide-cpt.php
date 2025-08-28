<?php
/**
 * Plugin Name: VeriaGuide Custom Post Types
 * Description: Custom post types for VeriaGuide tourism directory
 * Version: 1.0
 * Author: VeriaGuide Team
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class VeriaGuideCustomPostTypes {
    
    public function __construct() {
        add_action('init', array($this, 'register_post_types'));
        add_action('rest_api_init', array($this, 'register_rest_fields'));
    }
    
    public function register_post_types() {
        $post_types = array(
            'religious_site' => array(
                'name' => 'Religious Sites',
                'singular' => 'Religious Site',
                'rest_base' => 'religious_sites'
            ),
            'museum' => array(
                'name' => 'Museums',
                'singular' => 'Museum',
                'rest_base' => 'museums'
            ),
            'archaeological_site' => array(
                'name' => 'Archaeological Sites',
                'singular' => 'Archaeological Site',
                'rest_base' => 'archaeological_sites'
            ),
            'hiking_trail' => array(
                'name' => 'Hiking Trails',
                'singular' => 'Hiking Trail',
                'rest_base' => 'hiking_trails'
            ),
            'restaurant' => array(
                'name' => 'Restaurants',
                'singular' => 'Restaurant',
                'rest_base' => 'restaurants'
            ),
            'cafe' => array(
                'name' => 'Cafes',
                'singular' => 'Cafe',
                'rest_base' => 'cafes'
            ),
            'accommodation' => array(
                'name' => 'Accommodations',
                'singular' => 'Accommodation',
                'rest_base' => 'accommodations'
            ),
            'ski_resort' => array(
                'name' => 'Ski Resorts',
                'singular' => 'Ski Resort',
                'rest_base' => 'ski_resorts'
            ),
            'tour' => array(
                'name' => 'Tours',
                'singular' => 'Tour',
                'rest_base' => 'tours'
            ),
            'hidden_gem' => array(
                'name' => 'Hidden Gems',
                'singular' => 'Hidden Gem',
                'rest_base' => 'hidden_gems'
            )
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
                    'not_found_in_trash' => 'No ' . strtolower($config['name']) . ' found in trash'
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
                'menu_icon' => 'dashicons-location-alt'
            ));
        }
        
        // Flush rewrite rules on activation
        if (get_option('veriaguide_cpt_flush_rewrite_rules') !== 'done') {
            flush_rewrite_rules();
            update_option('veriaguide_cpt_flush_rewrite_rules', 'done');
        }
    }
    
    public function register_rest_fields() {
        $post_types = array('religious_site', 'museum', 'archaeological_site', 'hiking_trail', 
                           'restaurant', 'cafe', 'accommodation', 'ski_resort', 'tour', 'hidden_gem');
        
        foreach ($post_types as $post_type) {
            // Register ACF fields in REST API
            register_rest_field($post_type, 'acf', array(
                'get_callback' => array($this, 'get_acf_fields'),
                'schema' => null,
            ));
        }
    }
    
    public function get_acf_fields($object) {
        if (function_exists('get_fields')) {
            return get_fields($object['id']);
        }
        return array();
    }
}

// Initialize the plugin
new VeriaGuideCustomPostTypes();

// Activation hook
register_activation_hook(__FILE__, function() {
    // Trigger rewrite rules flush
    delete_option('veriaguide_cpt_flush_rewrite_rules');
});

?>