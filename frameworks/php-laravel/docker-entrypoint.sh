#!/bin/sh
set -e

echo "Starting Laravel Benchmark Application (nginx + php-fpm)..."

# Wait for database to be ready
echo "Waiting for database connection..."
sleep 5

# Generate application key if not exists
php artisan key:generate --no-interaction --force

# Run database migrations
php artisan migrate --force

# Cache configuration for performance
php artisan config:cache
php artisan route:cache
php artisan view:cache

echo "Starting php-fpm..."
php-fpm -D

echo "Starting nginx on port 8009..."
exec nginx -g 'daemon off;'