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
    curl

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

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -u 1001 -S appuser -G appuser

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8009/api/health || exit 1

# Start Laravel with built-in server
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8009"]