<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\UserController;
use App\Http\Controllers\PostController;
use App\Http\Controllers\HealthController;

Route::get('/user', function (Request $request) {
    return 'API';
});

// API Routes
Route::get('/users/{id}', [UserController::class, 'show']);
Route::get('/users', [UserController::class, 'index']);

Route::get('/posts/{id}', [PostController::class, 'show']);
Route::get('/posts', [PostController::class, 'index']);
Route::get('/posts/by-author/{authorId}', [PostController::class, 'getPostsByAuthor']);

Route::get('/health', [HealthController::class, 'index']);

Route::get('/metrics', function () {
    $registry = new Prometheus\CollectorRegistry();
    
    // Request counter
    $counter = $registry->getOrRegisterCounter(
        'laravel_requests_total',
        'Total number of requests',
        ['method', 'endpoint']
    );
    
    // Memory usage gauge
    $memoryGauge = $registry->getOrRegisterGauge(
        'laravel_memory_usage_bytes',
        'Current memory usage in bytes'
    );
    $memoryGauge->set(memory_get_usage(true));
    
    // Response time histogram
    $histogram = $registry->getOrRegisterHistogram(
        'laravel_request_duration_seconds',
        'Request duration in seconds',
        ['method', 'endpoint'],
        [0.1, 0.5, 1.0, 2.0, 5.0]
    );
    
    // Export metrics
    $renderer = new Prometheus\RenderTextFormat();
    return response($renderer->render($registry->getMetricFamilySamples()))
        ->header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
});
