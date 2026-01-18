# Build stage
FROM composer:2 AS builder

WORKDIR /app

# Copy composer files
COPY composer.json ./

# Install dependencies
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Copy application code
COPY . .

# Production stage
FROM php:8.3-cli-alpine

WORKDIR /app

# Install PostgreSQL extension
RUN apk add --no-cache postgresql-dev \
    && docker-php-ext-install pdo pdo_pgsql

# Copy application from builder
COPY --from=builder /app /app

# Create non-root user
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=4000

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:4000/health || exit 1

CMD ["php", "-S", "0.0.0.0:4000", "-t", "public"]
