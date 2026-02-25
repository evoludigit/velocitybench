#!/bin/bash

# Docker entrypoint script for Rails application
echo "Starting Rails Application..."

# Schema is managed by the postgres container — skip db:create and db:migrate.
# Just ensure tmp directories exist.
bundle exec rake tmp:create 2>/dev/null || true

echo "Rails application ready!"

# Execute the main command
exec "$@"
