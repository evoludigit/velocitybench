# Build stage
FROM hseeberger/scala-sbt:17.0.2_1.6.2_2.13.8 AS builder

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

# Create non-root user
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=4000
ENV APPLICATION_SECRET=changeme

EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:4000/health || exit 1

CMD ["bin/play-graphql", "-Dplay.http.secret.key=${APPLICATION_SECRET}"]
