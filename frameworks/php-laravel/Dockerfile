# Multi-stage build for Laravel with Octane and Swoole
FROM php:8.4-fpm-alpine AS base

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    libpq \
    composer \
    git \
    unzip \
    libxml2-dev \
    curl \
    nginx \
    && mkdir -p /run/nginx /var/log/nginx

# Install PHP extensions
RUN docker-php-ext-install pdo pdo_pgsql session fileinfo dom

# Set working directory
WORKDIR /app

# Copy composer files
COPY composer.json composer.lock ./

# Install PHP dependencies (ignore platform requirements for build)
RUN composer install --no-dev --optimize-autoloader --no-scripts \
    --ignore-platform-req=ext-session \
    --ignore-platform-req=ext-fileinfo \
    --ignore-platform-req=ext-tokenizer \
    --ignore-platform-req=ext-dom

# Copy application code
COPY . .

# Create .env file if it doesn't exist
RUN cp .env.example .env || true

# Generate application key if not exists
RUN php artisan key:generate --no-interaction || true

# Cache configuration for faster startup
RUN php artisan config:cache --no-interaction || true

# Build stage complete
FROM base AS production

# Copy nginx config
COPY nginx.conf /etc/nginx/http.d/default.conf

# Copy entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8009/api/health || exit 1

CMD ["/docker-entrypoint.sh"]