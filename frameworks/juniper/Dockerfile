# Build stage
FROM rust:1.88-alpine AS builder

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

# Install required packages for compilation
RUN apk add --no-cache musl-dev pkgconfig openssl-dev

# Create app directory
WORKDIR /app

# Copy Cargo files
COPY Cargo.toml Cargo.lock* ./

# Create dummy src to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    echo "mod db; mod models; mod schema; mod loaders;" >> src/main.rs && \
    touch src/db.rs src/models.rs src/schema.rs src/loaders.rs

# Build dependencies only (for caching)
RUN cargo build --release && rm -rf src/

# Copy source code
COPY src/ src/

# Build the actual application
RUN touch src/main.rs && cargo build --release

# Runtime stage
FROM alpine:3.19

# Set TMPDIR
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

# Install ca-certificates and wget for health checks
RUN apk --no-cache add ca-certificates wget

# Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -D -s /bin/sh -u 1000 -G appgroup appuser

WORKDIR /app

# Copy the compiled binary from builder
COPY --from=builder /app/target/release/juniper-graphql /app/juniper-graphql

# Change ownership to non-root user
RUN chown appuser:appgroup /app/juniper-graphql

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO /dev/null http://localhost:4000/health || exit 1

# Run the application
CMD ["./juniper-graphql"]
