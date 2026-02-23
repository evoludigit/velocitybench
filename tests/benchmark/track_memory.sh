#!/usr/bin/env bash
# VelocityBench — Docker container memory tracker
#
# Samples `docker stats` every 5 seconds and writes a CSV.
# Designed to run alongside k6 during the sustained load phase.
#
# Usage:
#   ./benchmarks/track_memory.sh go-gqlgen 300
#   ./benchmarks/track_memory.sh fraiseql-tv 300
#
# Arguments:
#   $1  Container name pattern (partial match, e.g. "go-gqlgen")
#   $2  Sampling duration in seconds (default: 300)
#
# Output: reports/memory-<pattern>-<timestamp>.csv

set -euo pipefail

CONTAINER_PATTERN="${1:?Usage: $0 <container-pattern> [duration-secs]}"
DURATION="${2:-300}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="reports/memory-${CONTAINER_PATTERN}-${TIMESTAMP}.csv"

mkdir -p reports

echo "timestamp,container,mem_mb,cpu_pct" > "$OUTPUT"
echo "Tracking memory for '${CONTAINER_PATTERN}' (${DURATION}s) → ${OUTPUT}"

END_TIME=$(( SECONDS + DURATION ))
SAMPLES=0

while [ "$SECONDS" -lt "$END_TIME" ]; do
  docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.CPUPerc}}' \
    | grep -i "$CONTAINER_PATTERN" \
    | while read -r name mem_raw _slash _limit cpu_raw; do
        # Parse memory: "123.4MiB / 7.8GiB" → MB float
        mem_mb=$(echo "$mem_raw" | awk '{
          val = $1
          if ($1 ~ /GiB/) { sub(/GiB/, "", val); val = val * 1024 }
          else if ($1 ~ /MiB/) { sub(/MiB/, "", val) }
          else if ($1 ~ /KiB/) { sub(/KiB/, "", val); val = val / 1024 }
          printf "%.1f", val
        }')
        # Strip % from cpu
        cpu="${cpu_raw//%/}"
        printf "%s,%s,%s,%s\n" "$(date -Iseconds)" "$name" "$mem_mb" "$cpu"
      done >> "$OUTPUT" 2>/dev/null || true
  SAMPLES=$(( SAMPLES + 1 ))
  sleep 5
done

echo "Done. ${SAMPLES} samples written to ${OUTPUT}"
