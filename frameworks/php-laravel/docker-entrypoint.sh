#!/bin/sh

# Docker entrypoint script for Laravel with Octane
# Sets up environment and starts the application

echo "Starting Laravel Octane Benchmark Application..."
echo "PHP Version: $(php --version | head -n 1)"

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

echo "Starting Octane server on port 8009..."
# Execute the application
exec "$@"