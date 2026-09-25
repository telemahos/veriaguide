<?php
/**
 * Plugin Name: VeriaGuide Authorization Header
 * Description: Restore HTTP Authorization for Application Passwords when OpenLiteSpeed/CGI omits it from PHP.
 * Version: 1.0.0
 * Author: VeriaGuide Team
 *
 * Must-use: copy to wp-content/mu-plugins/ (loads before regular plugins).
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Copy Authorization into $_SERVER so WP Application Passwords can authenticate.
 *
 * WordPress wp_validate_application_password() (priority 20 on determine_current_user)
 * requires PHP_AUTH_USER and PHP_AUTH_PW. OLS often drops Authorization before PHP,
 * leaving only getallheaders() / REDIRECT_HTTP_AUTHORIZATION / CGI_* variants.
 */
function veriaguide_restore_http_authorization() {
    $existing = isset($_SERVER['HTTP_AUTHORIZATION']) ? trim((string) $_SERVER['HTTP_AUTHORIZATION']) : '';
    if ($existing === '') {
        $candidates = array();

        if (!empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
            $candidates[] = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
        }
        if (!empty($_SERVER['Authorization'])) {
            $candidates[] = $_SERVER['Authorization'];
        }
        if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
            $candidates[] = $_SERVER['HTTP_AUTHORIZATION'];
        }
        if (!empty($_SERVER['CGI_HTTP_AUTHORIZATION'])) {
            $candidates[] = $_SERVER['CGI_HTTP_AUTHORIZATION'];
        }
        if (!empty($_SERVER['REMOTE_AUTHORIZATION'])) {
            $candidates[] = $_SERVER['REMOTE_AUTHORIZATION'];
        }

        if (function_exists('getallheaders')) {
            $headers = getallheaders();
            if (is_array($headers)) {
                foreach ($headers as $name => $value) {
                    if (is_string($name) && strcasecmp($name, 'Authorization') === 0) {
                        $candidates[] = $value;
                        break;
                    }
                }
            }
        }

        if (function_exists('apache_request_headers')) {
            $headers = apache_request_headers();
            if (is_array($headers)) {
                foreach ($headers as $name => $value) {
                    if (is_string($name) && strcasecmp($name, 'Authorization') === 0) {
                        $candidates[] = $value;
                        break;
                    }
                }
            }
        }

        foreach ($candidates as $value) {
            if (!is_string($value)) {
                continue;
            }
            $value = trim($value);
            if ($value !== '') {
                $_SERVER['HTTP_AUTHORIZATION'] = $value;
                $existing = $value;
                break;
            }
        }
    }

    if ($existing === '' || (isset($_SERVER['PHP_AUTH_USER']) && $_SERVER['PHP_AUTH_USER'] !== '')) {
        return;
    }

    if (stripos($existing, 'basic ') !== 0) {
        return;
    }

    $decoded = base64_decode(substr($existing, 6), true);
    if ($decoded === false || $decoded === '' || strpos($decoded, ':') === false) {
        return;
    }

    list($user, $password) = explode(':', $decoded, 2);
    if ($user === '') {
        return;
    }

    $_SERVER['PHP_AUTH_USER'] = $user;
    $_SERVER['PHP_AUTH_PW'] = $password;
}

veriaguide_restore_http_authorization();

add_action('plugins_loaded', 'veriaguide_restore_http_authorization', 0);
add_filter('determine_current_user', function ($user_id) {
    veriaguide_restore_http_authorization();
    return $user_id;
}, 0);
