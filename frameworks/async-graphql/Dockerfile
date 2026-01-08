# Use Rust nightly Alpine for edition2024 support
FROM rustlang/rust:nightly-alpine AS builder

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

# Install required packages for compilation
RUN apk add --no-cache musl-dev pkgconfig openssl-dev

# Create app directory
WORKDIR /app

# Copy Cargo files (Cargo.lock may not exist initially)
COPY Cargo.toml* Cargo.lock* ./

# Create dummy src/main.rs and module files to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    echo "mod db; mod models; mod schema;" >> src/main.rs && \
    touch src/db.rs src/models.rs src/schema.rs

# Build dependencies only (for caching)
RUN cargo build --release && rm -rf src/

# Copy source code
COPY src/ src/

# Build the actual application
RUN touch src/main.rs && cargo build --release

# Runtime stage
FROM alpine:latest

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -D -s /bin/sh -u 1000 -G appgroup appuser

WORKDIR /app

# Copy the compiled binary from builder
COPY --from=builder /app/target/release/async-graphql /app/async-graphql

# Change ownership to non-root user
RUN chown appuser:appgroup /app/async-graphql

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Run the application
CMD ["./async-graphql"]