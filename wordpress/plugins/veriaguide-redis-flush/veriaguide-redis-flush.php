<?php
/**
 * Plugin Name: VeriaGuide Redis Flush
 * Description: Flush the FastAPI frontend Redis cache from wp-admin (veriaguide_redis).
 * Version: 1.0.0
 * Author: VeriaGuide Team
 * Requires at least: 5.8
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 *
 * @package VeriaGuide_Redis_Flush
 */

if (!defined('ABSPATH')) {
    exit;
}

define('VG_REDIS_FLUSH_FILE', __FILE__);
define('VG_REDIS_FLUSH_DIR', plugin_dir_path(__FILE__));

require_once VG_REDIS_FLUSH_DIR . 'includes/class-vg-redis-client.php';

class VeriaGuide_Redis_Flush {

    const CAPABILITY      = 'manage_options';
    const OPTION_GROUP    = 'vg_redis_flush';
    const OPTION_HOST     = 'vg_redis_host';
    const OPTION_PORT     = 'vg_redis_port';
    const OPTION_PASSWORD = 'vg_redis_password';
    const OPTION_DB       = 'vg_redis_db';
    const OPTION_MODE     = 'vg_redis_flush_mode';
    const NONCE_FLUSH     = 'vg_redis_flush_action';
    const NONCE_SAVE      = 'vg_redis_flush_save';
    const NOTICE_KEY      = 'vg_redis_flush_notice';

    public function __construct() {
        add_action('admin_menu', array($this, 'register_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('admin_init', array($this, 'handle_post'));
        add_action('admin_notices', array($this, 'render_notices'));
    }

    public function register_menu() {
        add_management_page(
            __('VeriaGuide Redis cache', 'veriaguide-redis-flush'),
            __('Redis cache', 'veriaguide-redis-flush'),
            self::CAPABILITY,
            'veriaguide-redis-flush',
            array($this, 'render_page')
        );
    }

    public function register_settings() {
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_HOST,
            array(
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_text_field',
                'default'           => '127.0.0.1',
            )
        );
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_PORT,
            array(
                'type'              => 'integer',
                'sanitize_callback' => array($this, 'sanitize_port'),
                'default'           => 6379,
            )
        );
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_PASSWORD,
            array(
                'type'              => 'string',
                'sanitize_callback' => array($this, 'sanitize_password'),
                'default'           => '',
            )
        );
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_DB,
            array(
                'type'              => 'integer',
                'sanitize_callback' => array($this, 'sanitize_db'),
                'default'           => 0,
            )
        );
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_MODE,
            array(
                'type'              => 'string',
                'sanitize_callback' => array($this, 'sanitize_mode'),
                'default'           => 'FLUSHDB',
            )
        );
    }

    /**
     * Handle flush / ping / settings save with nonce + capability checks.
     */
    public function handle_post() {
        if (!is_admin() || !current_user_can(self::CAPABILITY)) {
            return;
        }

        if (empty($_POST['vg_redis_action'])) {
            return;
        }

        $action = sanitize_key(wp_unslash($_POST['vg_redis_action']));

        if ('save' === $action) {
            check_admin_referer(self::NONCE_SAVE);
            $this->save_settings_from_post();
            $this->store_notice('success', __('Redis settings saved.', 'veriaguide-redis-flush'));
            wp_safe_redirect($this->page_url());
            exit;
        }

        if ('flush' === $action || 'ping' === $action) {
            check_admin_referer(self::NONCE_FLUSH);
            $settings = $this->get_settings();
            $client   = new VG_Redis_Client(
                $settings['host'],
                $settings['port'],
                $settings['password'],
                $settings['db']
            );

            try {
                if ('ping' === $action) {
                    $pong = $client->ping();
                    $this->store_notice(
                        'success',
                        sprintf(
                            /* translators: %s: Redis PING reply */
                            __('Redis responded: %s', 'veriaguide-redis-flush'),
                            esc_html($pong)
                        )
                    );
                } else {
                    $client->flush($settings['mode']);
                    $this->store_notice(
                        'success',
                        sprintf(
                            /* translators: 1: command, 2: host:port, 3: db index */
                            __('Ran %1$s on %2$s (database %3$d). New WordPress content should appear after a hard refresh. Restarting the frontend container is optional and separate.', 'veriaguide-redis-flush'),
                            $settings['mode'],
                            $settings['host'] . ':' . $settings['port'],
                            $settings['db']
                        )
                    );
                }
            } catch (Exception $e) {
                $this->store_notice('error', $e->getMessage());
            }

            wp_safe_redirect($this->page_url());
            exit;
        }
    }

    public function render_notices() {
        if (!current_user_can(self::CAPABILITY)) {
            return;
        }

        $screen = function_exists('get_current_screen') ? get_current_screen() : null;
        if (!$screen || 'tools_page_veriaguide-redis-flush' !== $screen->id) {
            return;
        }

        $notice = get_transient(self::NOTICE_KEY . '_' . get_current_user_id());
        if (!$notice || empty($notice['message'])) {
            return;
        }

        delete_transient(self::NOTICE_KEY . '_' . get_current_user_id());
        $class = ('error' === $notice['type']) ? 'notice-error' : 'notice-success';
        printf(
            '<div class="notice %s is-dismissible"><p>%s</p></div>',
            esc_attr($class),
            esc_html($notice['message'])
        );
    }

    public function render_page() {
        if (!current_user_can(self::CAPABILITY)) {
            wp_die(esc_html__('You do not have permission to flush Redis.', 'veriaguide-redis-flush'));
        }

        $settings        = $this->get_settings();
        $locked          = $this->locked_by_constants();
        $phpredis        = class_exists('Redis');
        $is_flushall     = ('FLUSHALL' === $settings['mode']);
        ?>
        <div class="wrap">
            <h1><?php esc_html_e('VeriaGuide Redis cache', 'veriaguide-redis-flush'); ?></h1>
            <p>
                <?php esc_html_e('The FastAPI frontend caches listing content in Redis (container veriaguide_redis). Flush that cache here instead of SSH: docker exec veriaguide_redis redis-cli FLUSHALL', 'veriaguide-redis-flush'); ?>
            </p>

            <h2><?php esc_html_e('Flush Redis cache', 'veriaguide-redis-flush'); ?></h2>
            <?php if ($is_flushall) : ?>
                <div class="notice notice-warning inline">
                    <p>
                        <?php esc_html_e('FLUSHALL clears the entire Redis instance, not only database 0. Use this only if this Redis is dedicated to VeriaGuide (as on the VPS). Prefer FLUSHDB when other data might share the instance.', 'veriaguide-redis-flush'); ?>
                    </p>
                </div>
            <?php else : ?>
                <p>
                    <?php
                    printf(
                        /* translators: %d: Redis DB index */
                        esc_html__('FLUSHDB will wipe only database index %d (production default is 0, REDIS_URL …/0).', 'veriaguide-redis-flush'),
                        (int) $settings['db']
                    );
                    ?>
                </p>
            <?php endif; ?>

            <form method="post" action="">
                <?php wp_nonce_field(self::NONCE_FLUSH); ?>
                <p>
                    <button type="submit" name="vg_redis_action" value="flush" class="button button-primary">
                        <?php esc_html_e('Flush Redis cache', 'veriaguide-redis-flush'); ?>
                    </button>
                    <button type="submit" name="vg_redis_action" value="ping" class="button">
                        <?php esc_html_e('Test connection (PING)', 'veriaguide-redis-flush'); ?>
                    </button>
                </p>
            </form>

            <hr />

            <h2><?php esc_html_e('Connection settings', 'veriaguide-redis-flush'); ?></h2>
            <p>
                <?php esc_html_e('WordPress on the VPS is native (CyberPanel). Redis runs in Docker and is not published by default. Map Redis to 127.0.0.1:6379 on the host, then keep host 127.0.0.1 here. Do not put passwords in the git repo — use wp-config.php constants or this form.', 'veriaguide-redis-flush'); ?>
            </p>
            <p>
                <code>define('VERIAGUIDE_REDIS_HOST', '127.0.0.1');</code><br />
                <code>define('VERIAGUIDE_REDIS_PORT', 6379);</code><br />
                <code>define('VERIAGUIDE_REDIS_PASSWORD', '…');</code><br />
                <code>define('VERIAGUIDE_REDIS_DB', 0);</code><br />
                <code>define('VERIAGUIDE_REDIS_FLUSH_MODE', 'FLUSHDB');</code>
            </p>
            <p>
                <?php
                echo $phpredis
                    ? esc_html__('PHP Redis extension (phpredis) is available and will be used.', 'veriaguide-redis-flush')
                    : esc_html__('phpredis is not installed. The plugin uses a built-in TCP RESP client (no Composer). Installing php-redis is optional.', 'veriaguide-redis-flush');
                ?>
            </p>

            <form method="post" action="">
                <?php wp_nonce_field(self::NONCE_SAVE); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="vg_redis_host"><?php esc_html_e('Host', 'veriaguide-redis-flush'); ?></label></th>
                        <td>
                            <input name="vg_redis_host" id="vg_redis_host" type="text" class="regular-text" value="<?php echo esc_attr($settings['host']); ?>" <?php disabled(!empty($locked['host'])); ?> />
                            <?php $this->constant_hint('host', $locked); ?>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="vg_redis_port"><?php esc_html_e('Port', 'veriaguide-redis-flush'); ?></label></th>
                        <td>
                            <input name="vg_redis_port" id="vg_redis_port" type="number" class="small-text" min="1" max="65535" value="<?php echo esc_attr((string) $settings['port']); ?>" <?php disabled(!empty($locked['port'])); ?> />
                            <?php $this->constant_hint('port', $locked); ?>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="vg_redis_password"><?php esc_html_e('Password', 'veriaguide-redis-flush'); ?></label></th>
                        <td>
                            <input name="vg_redis_password" id="vg_redis_password" type="password" class="regular-text" value="" autocomplete="new-password" placeholder="<?php echo $settings['password'] !== '' ? esc_attr__('(unchanged)', 'veriaguide-redis-flush') : ''; ?>" <?php disabled(!empty($locked['password'])); ?> />
                            <p class="description"><?php esc_html_e('Leave blank to keep the stored password. Current docker-compose.vps.yml Redis has no password by default.', 'veriaguide-redis-flush'); ?></p>
                            <?php $this->constant_hint('password', $locked); ?>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="vg_redis_db"><?php esc_html_e('Database index', 'veriaguide-redis-flush'); ?></label></th>
                        <td>
                            <input name="vg_redis_db" id="vg_redis_db" type="number" class="small-text" min="0" max="15" value="<?php echo esc_attr((string) $settings['db']); ?>" <?php disabled(!empty($locked['db'])); ?> />
                            <p class="description"><?php esc_html_e('Matches REDIS_URL …/0 on the frontend (FLUSHDB target).', 'veriaguide-redis-flush'); ?></p>
                            <?php $this->constant_hint('db', $locked); ?>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><?php esc_html_e('Flush command', 'veriaguide-redis-flush'); ?></th>
                        <td>
                            <fieldset <?php disabled(!empty($locked['mode'])); ?>>
                                <label>
                                    <input type="radio" name="vg_redis_flush_mode" value="FLUSHDB" <?php checked($settings['mode'], 'FLUSHDB'); ?> />
                                    <?php esc_html_e('FLUSHDB (recommended — only the configured database)', 'veriaguide-redis-flush'); ?>
                                </label>
                                <br />
                                <label>
                                    <input type="radio" name="vg_redis_flush_mode" value="FLUSHALL" <?php checked($settings['mode'], 'FLUSHALL'); ?> />
                                    <?php esc_html_e('FLUSHALL (entire Redis instance — same as the SSH command)', 'veriaguide-redis-flush'); ?>
                                </label>
                            </fieldset>
                            <?php $this->constant_hint('mode', $locked); ?>
                        </td>
                    </tr>
                </table>
                <p>
                    <button type="submit" name="vg_redis_action" value="save" class="button button-secondary">
                        <?php esc_html_e('Save settings', 'veriaguide-redis-flush'); ?>
                    </button>
                </p>
            </form>
        </div>
        <?php
    }

    /**
     * @return array{host:string,port:int,password:string,db:int,mode:string}
     */
    public function get_settings() {
        $host = defined('VERIAGUIDE_REDIS_HOST') ? VERIAGUIDE_REDIS_HOST : get_option(self::OPTION_HOST, '127.0.0.1');
        $port = defined('VERIAGUIDE_REDIS_PORT') ? VERIAGUIDE_REDIS_PORT : get_option(self::OPTION_PORT, 6379);
        $db   = defined('VERIAGUIDE_REDIS_DB') ? VERIAGUIDE_REDIS_DB : get_option(self::OPTION_DB, 0);
        $mode = defined('VERIAGUIDE_REDIS_FLUSH_MODE') ? VERIAGUIDE_REDIS_FLUSH_MODE : get_option(self::OPTION_MODE, 'FLUSHDB');

        if (defined('VERIAGUIDE_REDIS_PASSWORD')) {
            $password = VERIAGUIDE_REDIS_PASSWORD;
        } else {
            $password = (string) get_option(self::OPTION_PASSWORD, '');
        }

        return array(
            'host'     => $host ? (string) $host : '127.0.0.1',
            'port'     => $this->sanitize_port($port),
            'password' => (string) $password,
            'db'       => $this->sanitize_db($db),
            'mode'     => $this->sanitize_mode($mode),
        );
    }

    /**
     * @return array<string,bool>
     */
    private function locked_by_constants() {
        return array(
            'host'     => defined('VERIAGUIDE_REDIS_HOST'),
            'port'     => defined('VERIAGUIDE_REDIS_PORT'),
            'password' => defined('VERIAGUIDE_REDIS_PASSWORD'),
            'db'       => defined('VERIAGUIDE_REDIS_DB'),
            'mode'     => defined('VERIAGUIDE_REDIS_FLUSH_MODE'),
        );
    }

    private function save_settings_from_post() {
        $locked = $this->locked_by_constants();

        if (empty($locked['host']) && isset($_POST['vg_redis_host'])) {
            update_option(self::OPTION_HOST, sanitize_text_field(wp_unslash($_POST['vg_redis_host'])));
        }
        if (empty($locked['port']) && isset($_POST['vg_redis_port'])) {
            update_option(self::OPTION_PORT, $this->sanitize_port(wp_unslash($_POST['vg_redis_port'])));
        }
        if (empty($locked['db']) && isset($_POST['vg_redis_db'])) {
            update_option(self::OPTION_DB, $this->sanitize_db(wp_unslash($_POST['vg_redis_db'])));
        }
        if (empty($locked['mode']) && isset($_POST['vg_redis_flush_mode'])) {
            update_option(self::OPTION_MODE, $this->sanitize_mode(wp_unslash($_POST['vg_redis_flush_mode'])));
        }
        if (empty($locked['password']) && isset($_POST['vg_redis_password'])) {
            $incoming = (string) wp_unslash($_POST['vg_redis_password']);
            if ($incoming !== '') {
                update_option(self::OPTION_PASSWORD, $incoming);
            }
        }
    }

    /**
     * @param mixed $value
     * @return int
     */
    public function sanitize_port($value) {
        $port = (int) $value;
        if ($port < 1 || $port > 65535) {
            return 6379;
        }
        return $port;
    }

    /**
     * @param mixed $value
     * @return int
     */
    public function sanitize_db($value) {
        $db = (int) $value;
        if ($db < 0 || $db > 15) {
            return 0;
        }
        return $db;
    }

    /**
     * @param mixed $value
     * @return string
     */
    public function sanitize_mode($value) {
        $value = strtoupper((string) $value);
        return ('FLUSHALL' === $value) ? 'FLUSHALL' : 'FLUSHDB';
    }

    /**
     * @param mixed $value
     * @return string
     */
    public function sanitize_password($value) {
        return is_string($value) ? $value : '';
    }

    /**
     * @param string               $field
     * @param array<string,bool>   $locked
     */
    private function constant_hint($field, $locked) {
        if (!empty($locked[$field])) {
            echo '<p class="description">' . esc_html__('Locked by wp-config.php constant.', 'veriaguide-redis-flush') . '</p>';
        }
    }

    /**
     * @param string $type
     * @param string $message
     */
    private function store_notice($type, $message) {
        set_transient(
            self::NOTICE_KEY . '_' . get_current_user_id(),
            array(
                'type'    => $type,
                'message' => $message,
            ),
            60
        );
    }

    /**
     * @return string
     */
    private function page_url() {
        return admin_url('tools.php?page=veriaguide-redis-flush');
    }
}

new VeriaGuide_Redis_Flush();
