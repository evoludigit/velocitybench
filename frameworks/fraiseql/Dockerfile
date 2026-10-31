# FraiseQL Dockerfile for VelocityBench
# Multi-stage build: Python schema gen -> FraiseQL binaries -> Debian runtime, which
# compiles the schema against the database at start (entrypoint.sh).

# Single source of truth for the FraiseQL version. The binaries must report
# exactly this version; the build fails otherwise. Exported as FRAISEQL_VERSION
# in the runtime image so benchmark runs can record it.
#
# By default the build downloads the published release asset for this version
# (fraiseql-full-x86_64-unknown-linux-gnu.tar.gz: the asset that carries
# fraiseql-server) and checks it against FRAISEQL_SHA256, the digest GitHub
# lists for it. Binaries placed at frameworks/fraiseql/fraiseql-cli and
# frameworks/fraiseql/fraiseql-server (gitignored) are used instead: FraiseQL's
# release benchmark injects the build of the commit it measures there.
ARG FRAISEQL_VERSION=2.18.0
ARG FRAISEQL_SHA256=68cf218fd82f521fc7e298eb8ea735c4696f4a78be9c58672d9f1ad98b1ce677

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
# Stage 2: FraiseQL binaries (the release, or the injected build)
# ============================================================================
FROM debian:trixie-slim AS builder

ARG FRAISEQL_VERSION
ARG FRAISEQL_SHA256

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Dockerfile is always present, so the COPY holds whether or not binaries were injected.
COPY Dockerfile fraiseql-cl[i] fraiseql-serve[r] /tmp/injected/
RUN set -eu; \
    if [ -f /tmp/injected/fraiseql-cli ] && [ -f /tmp/injected/fraiseql-server ]; then \
        echo "fraiseql binaries: injected"; \
        install -m 0755 /tmp/injected/fraiseql-cli /tmp/injected/fraiseql-server /usr/local/bin/; \
    elif [ -f /tmp/injected/fraiseql-cli ] || [ -f /tmp/injected/fraiseql-server ]; then \
        echo "only one of fraiseql-cli / fraiseql-server was injected" >&2; exit 1; \
    else \
        echo "fraiseql binaries: release v${FRAISEQL_VERSION}"; \
        curl -fsSL -o /tmp/fraiseql.tar.gz \
            "https://github.com/fraiseql/fraiseql/releases/download/v${FRAISEQL_VERSION}/fraiseql-full-x86_64-unknown-linux-gnu.tar.gz"; \
        echo "${FRAISEQL_SHA256}  /tmp/fraiseql.tar.gz" | sha256sum -c -; \
        tar -xzf /tmp/fraiseql.tar.gz -C /tmp; \
        install -m 0755 /tmp/fraiseql /usr/local/bin/fraiseql-cli; \
        install -m 0755 /tmp/fraiseql-server /usr/local/bin/fraiseql-server; \
        rm -f /tmp/fraiseql.tar.gz /tmp/fraiseql /tmp/fraiseql-server; \
    fi; \
    rm -rf /tmp/injected; \
    fraiseql-cli --version | grep -F "${FRAISEQL_VERSION}"; \
    fraiseql-server --version | grep -F "${FRAISEQL_VERSION}"


# ============================================================================
# Stage 3: Runtime image
# ============================================================================
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/bin/fraiseql-server /usr/local/bin/fraiseql-cli /usr/local/bin/
COPY entrypoint.sh /usr/local/bin/fraiseql-entrypoint

# The compile inputs, apart from the server's config: the compiler reads the
# fraiseql.toml beside schema.json, the server the one in /app.
ARG BUILD_TOML
COPY --from=schema-builder /app/schema.json compile/schema.json
COPY ${BUILD_TOML} compile/fraiseql.toml

ARG SERVER_TOML
COPY ${SERVER_TOML} ./fraiseql.toml

RUN useradd -r -s /bin/false fraiseql && chown fraiseql /app
USER fraiseql

ARG FRAISEQL_VERSION
ENV FRAISEQL_VERSION=${FRAISEQL_VERSION}
ENV RUST_LOG=info
ENV FRAISEQL_CONFIG=fraiseql.toml
ENV DATABASE_URL=postgresql://benchmark:benchmark123@postgres:5432/velocitybench_benchmark

EXPOSE 8815

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8815/health || exit 1

ENTRYPOINT ["fraiseql-entrypoint"]
