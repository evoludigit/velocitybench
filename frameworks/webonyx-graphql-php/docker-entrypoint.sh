#!/bin/sh
set -e

# Start php-fpm in background
php-fpm -D

# Wait for php-fpm to start
sleep 0.5

# Start nginx in foreground
exec nginx -g 'daemon off;'
