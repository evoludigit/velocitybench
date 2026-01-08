FROM ruby:3.3-slim AS base

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp

# Install system dependencies
RUN apt-get update && apt-get install -y     build-essential     postgresql-client     libpq-dev     libyaml-dev     curl     git     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install bundler
RUN gem install bundler --no-document

# Copy Gemfile and install dependencies
COPY Gemfile Gemfile.lock ./
RUN bundle install --jobs 4 --retry 3

# Copy application code
COPY . .

# Precompile assets (for API app, this is minimal)
# Asset precompilation not needed for API-only Rails app

# Create non-root user
RUN useradd -m -s /bin/bash rails && chown -R rails:rails /app
USER rails

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3     CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Start the application
CMD ["bundle", "exec", "puma", "-b", "tcp://0.0.0.0:8000"]
