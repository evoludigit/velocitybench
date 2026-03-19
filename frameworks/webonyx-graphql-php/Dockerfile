# Build stage
FROM composer:2 AS builder

WORKDIR /app

# Copy composer files
COPY composer.json composer.lock ./

# Install dependencies
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Copy application code
COPY . .

# Production stage
FROM php:8.3-fpm-alpine

WORKDIR /app

# Install nginx and PostgreSQL extension; enable opcache for persistent static vars
RUN apk add --no-cache nginx postgresql-dev \
    && docker-php-ext-install pdo pdo_pgsql opcache \
    && mkdir -p /run/nginx /var/log/nginx /var/run/php

# Configure opcache for production
RUN printf 'opcache.enable=1\nopcache.enable_cli=0\nopcache.memory_consumption=128\nopcache.interned_strings_buffer=8\nopcache.max_accelerated_files=10000\nopcache.validate_timestamps=0\n' \
    > /usr/local/etc/php/conf.d/opcache.ini

# Configure php-fpm: Unix socket, static PM with 50 workers
RUN sed -i \
    -e 's|^pm = dynamic|pm = static|' \
    -e 's|^pm\.max_children = [0-9]*$|pm.max_children = 50|' \
    /usr/local/etc/php-fpm.d/www.conf \
    && printf '\n[www]\nlisten = /var/run/php/php-fpm.sock\nlisten.owner = nginx\nlisten.group = nginx\nlisten.mode = 0660\n' \
    >> /usr/local/etc/php-fpm.d/www.conf

# Copy application from builder
COPY --from=builder /app /app

# Copy nginx config
COPY nginx.conf /etc/nginx/http.d/default.conf

# Copy and configure entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PORT=4000

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:4000/health || exit 1

CMD ["/docker-entrypoint.sh"]
