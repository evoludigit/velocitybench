# FraiseQL Dockerfile for VelocityBench
# Multi-stage build: Python schema gen -> CLI compile -> Debian runtime

# Single source of truth for the FraiseQL version. The copied binaries must
# report exactly this version; the build fails otherwise. Exported as
# FRAISEQL_VERSION in the runtime image so benchmark runs can record it.
ARG FRAISEQL_VERSION=2.11.0

# Build argument: which schema variant to compile.
#   schema.py    -> Variant A (v_* on-the-fly JSONB views) -- default
#   schema_tv.py -> Variant B (tv_* pre-computed JSONB tables)
ARG SCHEMA_FILE=schema.py

# Build argument: which compiler config to use.
#   fraiseql-build.toml          -> default (audit disabled)
#   fraiseql-build-tv.toml       -> TV variant (audit disabled)
#   fraiseql-build-tv-audit.toml -> TV variant (audit enabled)
ARG BUILD_TOML=fraiseql-build.toml

# Build argument: server runtime config (copied into final image).
ARG SERVER_TOML=fraiseql.toml

# ============================================================================
# Stage 1: Python -- generate schema.json from the selected schema variant
# ============================================================================
FROM python:3.13-slim-bookworm AS schema-builder

ARG SCHEMA_FILE

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy selected schema file; always produce schema.json for Stage 2.
# schema.py    -> outputs schema.json    (no rename needed)
# schema_tv.py -> outputs schema_tv.json (rename to schema.json)
COPY ${SCHEMA_FILE} ./schema_source.py
RUN python schema_source.py && \
    (mv schema_tv.json schema.json 2>/dev/null || \
     mv schema_tv_audit.json schema.json 2>/dev/null || true)

# ============================================================================
# Stage 2: Compile schema with fraiseql-cli
# The build directory intentionally has NO fraiseql.toml (server config)
# to avoid auto-discovery conflicts with the CLI's TOML parser.
# ============================================================================
FROM debian:trixie-slim AS builder

ARG FRAISEQL_VERSION

COPY fraiseql-cli /usr/local/bin/fraiseql-cli
RUN chmod +x /usr/local/bin/fraiseql-cli && \
    fraiseql-cli --version | grep -F "${FRAISEQL_VERSION}"

WORKDIR /build

# Copy only schema.json and compile config — no server config here
ARG BUILD_TOML
COPY --from=schema-builder /app/schema.json .
COPY ${BUILD_TOML} ./fraiseql.toml

# Compile schema: legacy JSON workflow (types/queries/mutations in schema.json)
RUN fraiseql-cli compile schema.json --output schema.compiled.json

COPY fraiseql-server /usr/local/bin/fraiseql-server
RUN chmod +x /usr/local/bin/fraiseql-server && \
    fraiseql-server --version | grep -F "${FRAISEQL_VERSION}"

# ============================================================================
# Stage 3: Runtime image
# ============================================================================
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/bin/fraiseql-server /usr/local/bin/
COPY --from=builder /build/schema.compiled.json .

ARG SERVER_TOML
COPY ${SERVER_TOML} ./fraiseql.toml

RUN useradd -r -s /bin/false fraiseql
USER fraiseql

ARG FRAISEQL_VERSION
ENV FRAISEQL_VERSION=${FRAISEQL_VERSION}
ENV RUST_LOG=info
ENV FRAISEQL_CONFIG=fraiseql.toml
ENV DATABASE_URL=postgresql://benchmark:benchmark123@postgres:5432/velocitybench_benchmark

EXPOSE 8815

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8815/health || exit 1

CMD ["fraiseql-server"]
