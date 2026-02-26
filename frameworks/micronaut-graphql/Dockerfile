# Build stage
FROM gradle:8.5-jdk21-alpine AS builder

WORKDIR /app

# Copy Gradle files
COPY build.gradle settings.gradle ./

# Copy source
COPY src ./src

# Build and normalise the fat JAR name to app.jar
RUN gradle clean shadowJar -x test --no-daemon

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/build/libs/app.jar app.jar

# Create non-root user
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=4000
ENV MICRONAUT_SERVER_PORT=4000

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD wget -qO- http://localhost:4000/health || exit 1

CMD ["java", "-jar", "app.jar"]
