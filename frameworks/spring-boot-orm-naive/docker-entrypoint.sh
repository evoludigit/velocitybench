#!/bin/sh

# Docker entrypoint script for Java Spring Boot application
# Sets up environment and starts the application

echo "Starting FraiseQL Spring Boot Benchmark Application..."
echo "Java Version: $(java -version 2>&1 | head -n 1)"
echo "Java Options: $JAVA_OPTS"

# Wait for database to be ready (optional, handled by Spring Boot retry)
echo "Waiting for database connection..."

# Execute the application
exec java $JAVA_OPTS -jar app.jar