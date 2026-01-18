<?php
declare(strict_types=1);

require_once __DIR__ . '/../vendor/autoload.php';

use Nyholm\Psr7\Factory\Psr17Factory;
use Nyholm\Psr7Server\ServerRequestCreator;
use VelocityBench\GraphQL\Schema;
use VelocityBench\Database\Connection;
use VelocityBench\DataLoader\DataLoaderRegistry;
use GraphQL\GraphQL;
use GraphQL\Error\DebugFlag;

// Handle routing
$uri = $_SERVER['REQUEST_URI'] ?? '/';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

// Parse URI (remove query string)
$path = parse_url($uri, PHP_URL_PATH);

// Health check endpoint
if ($path === '/health') {
    $healthy = Connection::isHealthy();
    http_response_code($healthy ? 200 : 503);
    header('Content-Type: application/json');
    echo json_encode([
        'status' => $healthy ? 'healthy' : 'unhealthy',
        'framework' => 'webonyx-graphql-php'
    ]);
    exit;
}

// Metrics endpoint
if ($path === '/metrics') {
    header('Content-Type: text/plain; charset=utf-8');
    $poolSize = Connection::getPoolSize();
    echo <<<METRICS
# HELP php_requests_total Total number of GraphQL requests
# TYPE php_requests_total counter
php_requests_total 0
# HELP php_db_pool_size Database connection pool size
# TYPE php_db_pool_size gauge
php_db_pool_size {$poolSize}
METRICS;
    exit;
}

// GraphQL endpoint
if ($path === '/graphql') {
    // Create PSR-7 request
    $psr17Factory = new Psr17Factory();
    $creator = new ServerRequestCreator(
        $psr17Factory,
        $psr17Factory,
        $psr17Factory,
        $psr17Factory
    );
    $request = $creator->fromGlobals();

    // Parse request body
    $input = [];
    if ($method === 'POST') {
        $body = (string)$request->getBody();
        $input = json_decode($body, true) ?? [];
    } elseif ($method === 'GET') {
        $input = $request->getQueryParams();
    }

    $query = $input['query'] ?? '';
    $variables = $input['variables'] ?? null;
    $operationName = $input['operationName'] ?? null;

    // Create fresh DataLoaders for this request
    $loaders = new DataLoaderRegistry();

    // Execute GraphQL query
    try {
        $schema = Schema::build();
        $result = GraphQL::executeQuery(
            $schema,
            $query,
            null,
            ['loaders' => $loaders],
            $variables,
            $operationName
        );
        $output = $result->toArray(DebugFlag::INCLUDE_DEBUG_MESSAGE);
    } catch (\Exception $e) {
        $output = [
            'errors' => [
                ['message' => $e->getMessage()]
            ]
        ];
    }

    header('Content-Type: application/json');
    echo json_encode($output);
    exit;
}

// 404 for unknown routes
http_response_code(404);
header('Content-Type: application/json');
echo json_encode(['error' => 'Not Found']);
