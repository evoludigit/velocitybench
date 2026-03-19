FROM golang:1.24-alpine AS builder

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp

WORKDIR /app
COPY go.mod go.sum ./
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /server ./cmd/server

FROM alpine:3.19

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp && apk --no-cache add ca-certificates curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /server /server
WORKDIR /

USER appuser

EXPOSE 4009

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:4009/health || exit 1

CMD ["/server"]
