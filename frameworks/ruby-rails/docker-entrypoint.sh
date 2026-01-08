#!/bin/bash

# Docker entrypoint script for Rails application
echo "Starting Rails Application..."

# Wait for database to be ready
echo "Waiting for database connection..."
sleep 5

# Run database migrations
echo "Running database migrations..."
bundle exec rake db:migrate

# Create database if it doesn't exist (in case migrations fail)
bundle exec rake db:create 2>/dev/null || true

# Run migrations again
bundle exec rake db:migrate

# Precompile assets (though minimal for API)
echo "Precompiling assets..."
RAILS_ENV=production SECRET_KEY_BASE=dummy bundle exec rake assets:precompile

# Clear cache
echo "Clearing cache..."
bundle exec rake tmp:clear
bundle exec rake tmp:create

echo "Rails application ready!"

# Execute the main command
exec "$@"
