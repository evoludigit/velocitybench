# FraiseQL v2.0.0-beta.4 Dockerfile for VelocityBench
# Multi-stage build: Rust builder -> Python schema gen -> Debian runtime
#
# NOTE: fraiseql-server v2.0.0-beta.4 is not yet published to crates.io.
# The server binary is copied from the local build at ~/code/fraiseql/target/release/.
# When the server is published, replace the COPY with:
#   RUN cargo install fraiseql-server --version 2.0.0-beta.4 --locked
#
# beta.4 includes fix for issue #27 (nested Object projection using -> instead
# of ->>) — the "stream" strategy workaround in fraiseql.toml is no longer needed.

# Build argument: which schema variant to compile.
#   schema.py    → Variant A (v_* on-the-fly JSONB views) — default
#   schema_tv.py → Variant B (tv_* pre-computed JSONB tables)
ARG SCHEMA_FILE=schema.py

# ============================================================================
# Stage 1: Python — generate schema.json from the selected schema variant
# ============================================================================
FROM python:3.12-slim-bookworm AS schema-builder

ARG SCHEMA_FILE

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy selected schema file; always produce schema.json for Stage 2.
# schema.py    → outputs schema.json    (no rename needed)
# schema_tv.py → outputs schema_tv.json (rename to schema.json)
COPY ${SCHEMA_FILE} ./schema_source.py
RUN python schema_source.py && \
    mv schema_tv.json schema.json 2>/dev/null || true

# ============================================================================
# Stage 2: Rust — install fraiseql-cli and compile schema
# (runs on same OS as the cli so glibc versions match)
# ============================================================================
FROM rust:latest AS builder

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install fraiseql-cli from crates.io (beta.3 published)
# fraiseql-cli beta.4 not yet on crates.io — use local build copied alongside fraiseql-server
COPY fraiseql-cli /usr/local/bin/fraiseql-cli
RUN chmod +x /usr/local/bin/fraiseql-cli

WORKDIR /app

# Copy schema artifacts and config for compilation
COPY --from=schema-builder /app/schema.json .
COPY fraiseql.toml .

# Compile schema: TOML mode with Python SDK types
RUN fraiseql-cli compile fraiseql.toml --types schema.json

# Copy fraiseql-server binary (local beta.3 build — not yet on crates.io)
COPY fraiseql-server /usr/local/bin/fraiseql-server
RUN chmod +x /usr/local/bin/fraiseql-server

# ============================================================================
# Stage 3: Runtime image (bookworm-slim)
# NOTE: fraiseql-server is a local build linked against bookworm glibc
# ============================================================================
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/bin/fraiseql-server /usr/local/bin/
COPY --from=builder /app/schema.compiled.json .
COPY fraiseql.toml .

RUN useradd -r -s /bin/false fraiseql
USER fraiseql

ENV RUST_LOG=info
ENV FRAISEQL_CONFIG=fraiseql.toml
ENV DATABASE_URL=postgresql://benchmark:benchmark123@postgres:5432/velocitybench_benchmark

EXPOSE 8815

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8815/health || exit 1

CMD ["fraiseql-server"]
