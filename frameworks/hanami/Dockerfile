# Build stage
FROM ruby:3.3-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Gemfile and install dependencies
COPY Gemfile Gemfile.lock* ./
RUN bundle config set --local path 'vendor/bundle' && \
    bundle config set --local without 'development test' && \
    bundle install --jobs 4

# Copy application code
COPY . .

# Production stage
FROM ruby:3.3-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy bundle from builder
COPY --from=builder /app/vendor/bundle /app/vendor/bundle
COPY --from=builder /usr/local/bundle/config /usr/local/bundle/config

# Copy application
COPY . .

# Configure bundler for production
RUN bundle config set --local without 'development test' && \
    bundle config set --local path 'vendor/bundle'

# Create non-root user
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

ENV RACK_ENV=production
ENV PORT=4000
ENV BUNDLE_WITHOUT="development:test"

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
