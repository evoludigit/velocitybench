# Stage 1: Builder
FROM rustlang/rust:nightly-alpine AS builder

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp && apk add --no-cache musl-dev postgresql-dev

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build the application
RUN cargo build --release

# Stage 2: Runtime
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache libpq ca-certificates curl

# Create a non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appuser -g appuser appuser

# Set working directory
WORKDIR /app

# Copy the binary from builder stage
COPY --from=builder /app/target/release/actix-web-rest /app/actix-web-rest

# Change ownership to non-root user
RUN chown appuser:appuser /app/actix-web-rest

# Switch to non-root user
USER appuser

# Expose port (matches main.rs configuration)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start the application
CMD ["/app/actix-web-rest"]