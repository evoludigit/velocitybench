#!/bin/bash
set -e

echo "Starting FraiseQL Spring Boot Application..."
echo "========================================"

# Environment variables with defaults
export SPRING_PROFILES_ACTIVE=${SPRING_PROFILES_ACTIVE:-development}
export SERVER_PORT=${SERVER_PORT:-8018}
export DB_HOST=${DB_HOST:-postgres}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-fraiseql_benchmark}
export DB_USER=${DB_USER:-benchmark}
export DB_PASSWORD=${DB_PASSWORD:-benchmark123}

# JVM tuning based on container resources
if [ -n "$JVM_MEMORY_LIMIT" ]; then
    echo "JVM Memory Limit detected: $JVM_MEMORY_LIMIT"
    export JAVA_OPTS="${JAVA_OPTS} -XX:MaxRAMPercentage=75.0 -XX:+UseContainerSupport"
else
    # Default JVM tuning for development
    export JAVA_OPTS="${JAVA_OPTS} -Xms512m -Xmx1024m"
fi

# Production JVM tuning
if [ "$SPRING_PROFILES_ACTIVE" = "production" ]; then
    echo "Applying production JVM tuning..."
    export JAVA_OPTS="${JAVA_OPTS} \
        -XX:+UseG1GC \
        -XX:MaxGCPauseMillis=200 \
        -XX:+UseStringDeduplication \
        -XX:+OptimizeStringConcat \
        -XX:+UseCompressedOops \
        -XX:+UseCompressedClassPointers \
        -Djava.security.egd=file:/dev/./urandom"
fi

# Wait for database to be ready
echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
timeout=60
while ! nc -z ${DB_HOST} ${DB_PORT}; do
    timeout=$((timeout - 1))
    if [ $timeout -le 0 ]; then
        echo "Database connection timeout"
        exit 1
    fi
    echo "Waiting for database... ($timeout seconds remaining)"
    sleep 1
done

echo "Database is ready!"

# Create log directory
mkdir -p logs

# Print configuration
echo "Configuration:"
echo "  Profile: ${SPRING_PROFILES_ACTIVE}"
echo "  Port: ${SERVER_PORT}"
echo "  Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "  JVM Options: ${JAVA_OPTS}"
echo ""

# Start the application
echo "Starting Spring Boot application..."
exec java ${JAVA_OPTS} -jar app.jar "$@"