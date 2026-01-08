#!/bin/bash
# JMeter CLI execution wrapper for benchmark testing
# Usage: ./run-headless.sh <test_plan> <results_dir> [threads] [loops] [ramp_up]

set -e

JMETER_HOME="${JMETER_HOME:-/opt/jmeter}"
TEST_PLAN="$1"
RESULTS_DIR="$2"
THREADS="${3:-100}"
LOOPS="${4:-1000}"
RAMP_UP="${5:-30}"

if [ -z "$TEST_PLAN" ] || [ -z "$RESULTS_DIR" ]; then
    echo "Usage: $0 <test_plan> <results_dir> [threads] [loops] [ramp_up]"
    echo "Example: $0 comparative-test-plan.jmx results/fraiseql 100 1000 30"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

# Verify JMeter is available
if ! command -v jmeter &> /dev/null; then
    echo "❌ JMeter not found. Please install JMeter or set JMETER_HOME"
    exit 1
fi

# Verify test plan exists
if [ ! -f "$TEST_PLAN" ]; then
    echo "❌ Test plan not found: $TEST_PLAN"
    exit 1
fi

echo "🚀 Starting JMeter test execution..."
echo "   Test Plan: $TEST_PLAN"
echo "   Results Dir: $RESULTS_DIR"
echo "   Threads: $THREADS"
echo "   Loops: $LOOPS"
echo "   Ramp Up: $RAMP_UP seconds"
echo "   Expected Requests: $((THREADS * LOOPS))"
echo

# Execute JMeter test
START_TIME=$(date +%s)
jmeter -n \
    -t "$TEST_PLAN" \
    -l "$RESULTS_DIR/results.jtl" \
    -e -o "$RESULTS_DIR/html" \
    -Jthreads="$THREADS" \
    -Jloops="$LOOPS" \
    -Jrampup="$RAMP_UP" \
    -Jresults.dir="$RESULTS_DIR"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Verify results were generated
if [ ! -f "$RESULTS_DIR/results.jtl" ]; then
    echo "❌ JMeter test failed - no results file generated"
    exit 1
fi

# Count successful requests
SUCCESS_COUNT=$(grep -c "true" "$RESULTS_DIR/results.jtl" 2>/dev/null || echo "0")
TOTAL_COUNT=$(wc -l < "$RESULTS_DIR/results.jtl")

if [ "$TOTAL_COUNT" -gt 0 ]; then
    SUCCESS_RATE=$((SUCCESS_COUNT * 100 / TOTAL_COUNT))
else
    SUCCESS_RATE=0
fi

echo
echo "✅ JMeter test completed successfully"
echo "   Duration: ${DURATION}s"
echo "   Total Requests: $TOTAL_COUNT"
echo "   Successful Requests: $SUCCESS_COUNT"
echo "   Success Rate: ${SUCCESS_RATE}%"
echo "   Results: $RESULTS_DIR/results.jtl"
echo "   HTML Report: $RESULTS_DIR/html/index.html"