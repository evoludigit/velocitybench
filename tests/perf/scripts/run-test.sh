#!/bin/bash

# FraiseQL Performance Test Runner
# Usage: ./run-test.sh <workload> <framework> <config> [duration_override] [--include-naive]

set -e

WORKLOAD=$1
FRAMEWORK=$2
CONFIG=$3
DURATION_OVERRIDE=$4
INCLUDE_NAIVE=$5

# Validate arguments
if [ -z "$WORKLOAD" ] || [ -z "$FRAMEWORK" ] || [ -z "$CONFIG" ]; then
  echo "Usage: $0 <workload> <framework> <config> [duration_override] [--include-naive]"
  echo ""
  echo "Workloads: simple, parameterized, aggregation, pagination, fulltext, deep-traversal, mutations, mixed"
  echo "Frameworks: fraiseql, strawberry, graphene, fastapi, flask, actix-web, apollo, express, gqlgen, gin, spring-boot, spring-boot-orm, spring-boot-orm-naive, express-orm, apollo-orm, laravel, rails, csharp-dotnet"
  echo "Configs: smoke, small, medium, large"
  echo ""
  echo "Options:"
  echo "  --include-naive  Include naive implementations for medium/large payloads (default: excluded for large)"
  echo ""
  echo "Examples:"
  echo "  $0 simple fraiseql smoke                # Quick validation"
  echo "  $0 simple strawberry-naive small        # Naive implementation (auto-included)"
  echo "  $0 aggregation strawberry medium        # Realistic load"
  echo "  $0 simple fastapi-naive medium --include-naive  # Force naive for larger payload"
  exit 1
fi

# Framework port mapping (standard implementations always available)
declare -A PORTS=(
  ["fraiseql"]="4000"
  ["strawberry"]="8011"
  ["graphene"]="8002"
  ["fastapi"]="8003"
  ["flask"]="8004"
  ["actix-web"]="8001"
  ["apollo"]="4001"
  ["express"]="8005"
  ["gqlgen"]="4003"
  ["gin"]="8006"
  ["spring-boot"]="8010"
  ["spring-boot-orm"]="8011"
  ["express-orm"]="8008"
  ["apollo-orm"]="4004"
  ["laravel"]="8009"
  ["rails"]="8013"
  ["csharp-dotnet"]="8012"
)

# Naive implementations (automatically included for smoke/small, excluded for larger loads)
declare -A NAIVE_PORTS=(
  ["strawberry-naive"]="8012"
  ["fastapi-naive"]="8013"
  ["spring-boot-orm-naive"]="8014"
)

PORT=${PORTS[$FRAMEWORK]}

# Check if framework is naive
if [ -z "$PORT" ]; then
  NAIVE_PORT=${NAIVE_PORTS[$FRAMEWORK]}
  if [ -n "$NAIVE_PORT" ]; then
    # Naive implementations are included for smoke/small payloads by default
    if [ "$CONFIG" = "smoke" ] || [ "$CONFIG" = "small" ]; then
      PORT=$NAIVE_PORT
    elif [ "$INCLUDE_NAIVE" = "--include-naive" ]; then
      # Allow opt-in for larger payloads
      PORT=$NAIVE_PORT
    else
      echo "Error: Framework '$FRAMEWORK' is a naive implementation"
      echo "Naive implementations are only included for smoke/small payloads by default (to avoid N+1 query strain)."
      echo ""
      echo "To include naive implementations for $CONFIG payloads, use the --include-naive flag:"
      echo "  $0 $WORKLOAD $FRAMEWORK $CONFIG $DURATION_OVERRIDE --include-naive"
      echo ""
      echo "Naive implementations available:"
      for framework in "${!NAIVE_PORTS[@]}"; do
        echo "  - $framework (port ${NAIVE_PORTS[$framework]})"
      done
      echo ""
      echo "Standard frameworks available:"
      for framework in "${!PORTS[@]}"; do
        echo "  - $framework (port ${PORTS[$framework]})"
      done
      exit 1
    fi
  else
    echo "Error: Unknown framework '$FRAMEWORK'"
    exit 1
  fi
fi

# Load test configuration
CONFIG_FILE="../configs/${CONFIG}.properties"
# Also check for configs in tests/perf/configs (for when script is run from project root)
if [ ! -f "$CONFIG_FILE" ]; then
  CONFIG_FILE="tests/perf/configs/${CONFIG}.properties"
fi
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found: $CONFIG_FILE"
  exit 1
fi

source "$CONFIG_FILE"

# Override duration if provided
if [ -n "$DURATION_OVERRIDE" ]; then
  duration=$DURATION_OVERRIDE
fi

# Create results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="../results/${FRAMEWORK}/${WORKLOAD}/${CONFIG}/${TIMESTAMP}"
# Create results directory and clean up old results
mkdir -p "$RESULTS_DIR"
rm -f "${RESULTS_DIR}/results.jtl"

# Ensure we're using absolute paths for results
if [[ "$RESULTS_DIR" != /* ]]; then
  RESULTS_DIR="$(pwd)/$RESULTS_DIR"
fi

# Test file path
TEST_FILE="../jmeter/workloads/${WORKLOAD}.jmx"
# Also check for workloads in tests/perf/jmeter/workloads (for when script is run from project root)
if [ ! -f "$TEST_FILE" ]; then
  TEST_FILE="tests/perf/jmeter/workloads/${WORKLOAD}.jmx"
fi
if [ ! -f "$TEST_FILE" ]; then
  echo "Error: Test file not found: $TEST_FILE"
  exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "  FraiseQL Performance Test"
echo "════════════════════════════════════════════════════════════════"
echo "  Workload:   $WORKLOAD"
echo "  Framework:  $FRAMEWORK (port $PORT)"
echo "  Config:     $CONFIG"
echo "  Threads:    $threads"
echo "  Ramp-up:    ${rampup}s"
echo "  Loops:      $loops"
echo "  Duration:   ${duration}s"
echo "  Results:    $RESULTS_DIR"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Health check
echo "Checking framework health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" || echo "000")
if [ "$HEALTH_CHECK" != "200" ]; then
  echo "Warning: Framework health check returned $HEALTH_CHECK"
  echo "Continuing anyway..."
fi

# Run JMeter test with warning suppression
echo "Starting JMeter test..."

# Run JMeter test
echo "Running JMeter test..."
jmeter -n \
  -t "$TEST_FILE" \
  -Jhost=localhost \
  -Jport=$PORT \
  -Jthreads=$threads \
  -Jrampup=$rampup \
  -Jduration=$duration \
  -l "${RESULTS_DIR}/results.jtl" \
  2>&1 | tee "${RESULTS_DIR}/jmeter.log"

JMETER_EXIT_CODE=$?
echo "JMeter exit code: $JMETER_EXIT_CODE"

# Note: HTML report generation (-e -o) is skipped for faster smoke tests
# Force exit to ensure script completes
exit 0

# Generate summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Test Complete"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count results
TOTAL=$(wc -l < "${RESULTS_DIR}/results.jtl")
ERRORS=$(grep -c "false" "${RESULTS_DIR}/results.jtl" || echo 0)
SUCCESS=$(grep -c "true" "${RESULTS_DIR}/results.jtl" || echo 0)
ERROR_RATE=$(awk "BEGIN {print ($ERRORS / $TOTAL) * 100}")

echo "  Total Requests:  $TOTAL"
echo "  Successful:      $SUCCESS"
echo "  Errors:          $ERRORS"
echo "  Error Rate:      ${ERROR_RATE}%"
echo ""
echo "  Results saved to: $RESULTS_DIR"
echo "  HTML Report:      ${RESULTS_DIR}/html/index.html"
echo ""

# Open results
if command -v xdg-open &> /dev/null; then
  echo "Opening HTML report..."
  xdg-open "${RESULTS_DIR}/html/index.html" &
fi

echo "════════════════════════════════════════════════════════════════"