<?php
declare(strict_types=1);

namespace VelocityBench\Database;

use PDO;
use PDOException;

class Connection
{
    private static ?PDO $pdo = null;

    private static function createConnection(): PDO
    {
        $host = getenv('DB_HOST') ?: 'localhost';
        $port = getenv('DB_PORT') ?: '5432';
        $dbname = getenv('DB_NAME') ?: 'velocitybench_benchmark';
        $user = getenv('DB_USER') ?: 'benchmark';
        $password = getenv('DB_PASSWORD') ?: 'benchmark123';

        $dsn = "pgsql:host={$host};port={$port};dbname={$dbname}";

        $pdo = new PDO($dsn, $user, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_PERSISTENT => true,
        ]);

        // Set search path to benchmark schema
        $pdo->exec("SET search_path TO benchmark, public");

        return $pdo;
    }

    public static function get(): PDO
    {
        if (self::$pdo === null) {
            self::$pdo = self::createConnection();
        }

        return self::$pdo;
    }

    public static function reconnect(): void
    {
        self::$pdo = self::createConnection();
    }

    public static function isHealthy(): bool
    {
        try {
            $pdo = self::get();
            $stmt = $pdo->query('SELECT 1');
            return $stmt !== false;
        } catch (PDOException $e) {
            return false;
        }
    }

    public static function getPoolSize(): int
    {
        // PHP doesn't have connection pooling in the traditional sense
        // Return 1 if connected, 0 otherwise
        return self::$pdo !== null ? 1 : 0;
    }
}
