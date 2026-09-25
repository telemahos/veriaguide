<?php
/**
 * Minimal Redis client (RESP over TCP). No Composer / Predis.
 *
 * @package VeriaGuide_Redis_Flush
 */

if (!defined('ABSPATH')) {
    exit;
}

class VG_Redis_Client {

    /** @var string */
    private $host;

    /** @var int */
    private $port;

    /** @var string */
    private $password;

    /** @var int */
    private $db;

    /** @var int */
    private $timeout;

    /**
     * @param string $host
     * @param int    $port
     * @param string $password
     * @param int    $db
     * @param int    $timeout
     */
    public function __construct($host, $port, $password = '', $db = 0, $timeout = 3) {
        $this->host     = $host;
        $this->port     = (int) $port;
        $this->password = (string) $password;
        $this->db       = (int) $db;
        $this->timeout  = (int) $timeout;
    }

    /**
     * Prefer phpredis when available; otherwise raw RESP.
     *
     * @param string $command FLUSHDB or FLUSHALL
     * @return true
     * @throws Exception
     */
    public function flush($command) {
        $command = strtoupper($command);
        if (!in_array($command, array('FLUSHDB', 'FLUSHALL'), true)) {
            throw new Exception('Unsupported Redis command.');
        }

        if (class_exists('Redis')) {
            $this->flush_with_phpredis($command);
            return true;
        }

        $this->flush_with_resp($command);
        return true;
    }

    /**
     * @return string
     * @throws Exception
     */
    public function ping() {
        if (class_exists('Redis')) {
            $redis = $this->connect_phpredis();
            $pong  = $redis->ping();
            $redis->close();
            return is_string($pong) ? $pong : 'PONG';
        }

        $fp = $this->open_socket();
        try {
            $this->handshake($fp);
            $reply = $this->command($fp, array('PING'));
        } finally {
            fclose($fp);
        }

        return is_string($reply) ? $reply : 'PONG';
    }

    /**
     * @param string $command
     * @throws Exception
     */
    private function flush_with_phpredis($command) {
        $redis = $this->connect_phpredis();
        try {
            if ('FLUSHALL' === $command) {
                $ok = $redis->flushAll();
            } else {
                $ok = $redis->flushDB();
            }
            if (!$ok) {
                throw new Exception('Redis flush returned a failure status.');
            }
        } finally {
            $redis->close();
        }
    }

    /**
     * @return Redis
     * @throws Exception
     */
    private function connect_phpredis() {
        $redis = new Redis();
        $connected = @$redis->connect($this->host, $this->port, $this->timeout);
        if (!$connected) {
            throw new Exception($this->connection_error());
        }
        if ($this->password !== '') {
            if (!$redis->auth($this->password)) {
                throw new Exception('Redis AUTH failed. Check the password.');
            }
        }
        if ($this->db > 0 && !$redis->select($this->db)) {
            throw new Exception('Redis SELECT failed for database index ' . $this->db . '.');
        }
        return $redis;
    }

    /**
     * @param string $command
     * @throws Exception
     */
    private function flush_with_resp($command) {
        $fp = $this->open_socket();
        try {
            $this->handshake($fp);
            $this->command($fp, array($command));
        } finally {
            fclose($fp);
        }
    }

    /**
     * @return resource
     * @throws Exception
     */
    private function open_socket() {
        $errno  = 0;
        $errstr = '';
        $fp     = @stream_socket_client(
            'tcp://' . $this->host . ':' . $this->port,
            $errno,
            $errstr,
            $this->timeout
        );

        if (!$fp) {
            throw new Exception($this->connection_error($errstr, $errno));
        }

        stream_set_timeout($fp, $this->timeout);
        return $fp;
    }

    /**
     * @param resource $fp
     * @throws Exception
     */
    private function handshake($fp) {
        if ($this->password !== '') {
            $this->command($fp, array('AUTH', $this->password));
        }
        if ($this->db > 0) {
            $this->command($fp, array('SELECT', (string) $this->db));
        }
    }

    /**
     * @param resource $fp
     * @param array    $args
     * @return mixed
     * @throws Exception
     */
    private function command($fp, array $args) {
        $payload = '*' . count($args) . "\r\n";
        foreach ($args as $arg) {
            $arg      = (string) $arg;
            $payload .= '$' . strlen($arg) . "\r\n" . $arg . "\r\n";
        }

        $written = fwrite($fp, $payload);
        if (false === $written) {
            throw new Exception('Failed to write to Redis.');
        }

        return $this->read_reply($fp);
    }

    /**
     * @param resource $fp
     * @return mixed
     * @throws Exception
     */
    private function read_reply($fp) {
        $line = fgets($fp);
        if (false === $line) {
            throw new Exception('No reply from Redis (timeout or closed connection).');
        }

        $prefix = $line[0];
        $data   = substr($line, 1, -2);

        switch ($prefix) {
            case '+':
                return $data;
            case '-':
                throw new Exception('Redis error: ' . $data);
            case ':':
                return (int) $data;
            case '$':
                $len = (int) $data;
                if ($len < 0) {
                    return null;
                }
                $bulk = stream_get_contents($fp, $len + 2);
                if (false === $bulk) {
                    throw new Exception('Failed to read Redis bulk reply.');
                }
                return substr($bulk, 0, $len);
            case '*':
                $count = (int) $data;
                if ($count < 0) {
                    return null;
                }
                $items = array();
                for ($i = 0; $i < $count; $i++) {
                    $items[] = $this->read_reply($fp);
                }
                return $items;
            default:
                throw new Exception('Unexpected Redis protocol prefix.');
        }
    }

    /**
     * @param string $detail
     * @param int    $errno
     * @return string
     */
    private function connection_error($detail = '', $errno = 0) {
        $msg = sprintf(
            'Could not connect to Redis at %s:%d.',
            $this->host,
            $this->port
        );
        if ($detail) {
            $msg .= ' ' . $detail;
        }
        if ($errno) {
            $msg .= ' (#' . $errno . ')';
        }
        $msg .= ' On CyberPanel, WordPress runs on the host while Redis is Docker-only unless you publish 127.0.0.1:6379.';
        return $msg;
    }
}
