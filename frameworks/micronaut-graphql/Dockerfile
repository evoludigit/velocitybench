# Build stage
FROM gradle:8.5-jdk21-alpine AS builder

WORKDIR /app

# Copy Gradle files
COPY build.gradle settings.gradle ./

# Copy source
COPY src ./src

# Build
RUN gradle build -x test --no-daemon

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/build/libs/*-all.jar app.jar

# Create non-root user
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=4000
ENV MICRONAUT_SERVER_PORT=4000

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:4000/health || exit 1

CMD ["java", "-jar", "app.jar"]
