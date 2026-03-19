# Build stage
FROM eclipse-temurin:21-jdk-alpine AS builder

RUN apk add --no-cache bash curl && \
    curl -L "https://github.com/sbt/sbt/releases/download/v1.9.9/sbt-1.9.9.tgz" -o /tmp/sbt.tgz && \
    tar xzf /tmp/sbt.tgz -C /usr/local && \
    ln -sf /usr/local/sbt/bin/sbt /usr/local/bin/sbt && \
    rm /tmp/sbt.tgz

WORKDIR /app

# Copy build files
COPY build.sbt .
COPY project ./project

# Download dependencies
RUN sbt update

# Copy source
COPY app ./app
COPY conf ./conf

# Build
RUN sbt stage

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy staged application
COPY --from=builder /app/target/universal/stage /app

# Install bash (required by sbt stage startup scripts) and wget for healthcheck
RUN apk add --no-cache bash wget

# Create non-root user
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=4000
ENV APPLICATION_SECRET=velocitybench-benchmark-secret-key-256bit

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:4000/health || exit 1

CMD ["sh", "-c", "bin/play-graphql -Dplay.http.secret.key=${APPLICATION_SECRET:-benchmark-secret-key}"]
