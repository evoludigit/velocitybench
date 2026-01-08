<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class MetricsMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        // Metrics collection disabled for benchmarking
        // This middleware is a passthrough to avoid Prometheus setup complexity
        return $next($request);
    }
}
