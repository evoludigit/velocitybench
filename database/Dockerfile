# PostgreSQL 17 with pg_tviews extension for VelocityBench
#
# pg_tviews provides automatic TVIEW (materialized JSONB table) sync via triggers:
#   - tv_user / tv_post / tv_comment are populated and kept current automatically
#   - Trigger-based cascade: updating tb_user.full_name propagates to tv_post.data
#
# Multi-stage build:
#   Stage 1: Build pg_tviews Rust extension against PostgreSQL 17 headers
#   Stage 2: Clean PostgreSQL 17 image with pg_tviews .so + SQL installed

# ============================================================================
# Stage 1: Build pg_tviews
# ============================================================================
FROM postgres:17 AS pg_tviews_builder

# Install build dependencies (Rust, PostgreSQL dev headers, build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    pkg-config \
    postgresql-server-dev-17 \
    && rm -rf /var/lib/apt/lists/*

# Install Rust stable toolchain (minimal profile)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    --default-toolchain stable \
    --profile minimal \
    --no-modify-path
ENV PATH="/root/.cargo/bin:${PATH}"

# Install cargo-pgrx matching pg_tviews pgrx = "0.16.1"
RUN cargo install --locked cargo-pgrx --version 0.16.1

# Initialize pgrx with the PostgreSQL 17 from the base image
RUN cargo pgrx init --pg17 "$(which pg_config)"

# Copy pg_tviews source (target/ excluded via .dockerignore)
WORKDIR /build/pg_tviews
COPY pg_tviews/ .

# Build and install the extension for pg17
# cargo pgrx install detects the pg17 version from the initialized pgrx environment
RUN cargo pgrx install --release

# Collect all extension files into a single directory for easy COPY in Stage 2
RUN mkdir -p /ext && \
    find /usr/share/postgresql/17/extension/ -name "pg_tviews*" -exec cp {} /ext/ \; && \
    cp /usr/lib/postgresql/17/lib/pg_tviews.so /ext/ && \
    echo "=== Extension files ===" && ls -la /ext/

# ============================================================================
# Stage 2: Production PostgreSQL 17 image with pg_tviews installed
# ============================================================================
FROM postgres:17

# Install pg_tviews extension files from Stage 1
COPY --from=pg_tviews_builder /ext/ /tmp/pg_tviews_ext/
RUN cp /tmp/pg_tviews_ext/*.control /usr/share/postgresql/17/extension/ && \
    cp /tmp/pg_tviews_ext/*.sql     /usr/share/postgresql/17/extension/ && \
    cp /tmp/pg_tviews_ext/*.so      /usr/lib/postgresql/17/lib/         && \
    rm -rf /tmp/pg_tviews_ext

# Verify installation
RUN ls -la /usr/share/postgresql/17/extension/pg_tviews* && \
    ls -la /usr/lib/postgresql/17/lib/pg_tviews.so
