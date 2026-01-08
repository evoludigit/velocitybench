#!/bin/bash
# Phase 7: Run all advanced workload scenarios with JMeter
# Usage: ./run-workloads.sh [framework] [port] [threads] [duration]

set -euo pipefail

WORKLOADS_DIR="tests/perf/jmeter/workloads"
RESULTS_DIR="tests/perf/results"
FRAMEWORK="${1:-fraiseql}"
PORT="${2:-4000}"
THREADS="${3:-50}"
LOOPS="${4:-100}"

# Create timestamped results directory
timestamp=$(date +%Y%m%d_%H%M%S)
results_path="${RESULTS_DIR}/${FRAMEWORK}_${timestamp}"
mkdir -p "$results_path"

echo "=== Phase 7: Advanced Workload Testing ==="
echo "Framework: $FRAMEWORK"
echo "Host: localhost"
echo "Port: $PORT"
echo "Threads: $THREADS"
echo "Loops: $LOOPS"
echo "Results: $results_path"
echo ""

# Array of workloads to run
declare -a workloads=(
    "simple"
    "parameterized"
    "aggregation"
    "pagination"
    "fulltext"
    "deep-traversal"
    "mutations"
    "mixed"
)

# Check if JMeter is available
if ! command -v jmeter &> /dev/null; then
    echo "ERROR: JMeter not found. Install JMeter to run workloads."
    echo "See: https://jmeter.apache.org/download_jmeter.cgi"
    exit 1
fi

# Run each workload
for workload in "${workloads[@]}"; do
    workload_file="${WORKLOADS_DIR}/${workload}.jmx"

    if [ ! -f "$workload_file" ]; then
        echo "SKIP: $workload (file not found)"
        continue
    fi

    echo "Running: $workload workload..."

    # Run JMeter in non-GUI mode
    jmeter -n \
        -t "$workload_file" \
        -l "${results_path}/${workload}.jtl" \
        -e -o "${results_path}/${workload}_report" \
        -Jhost=localhost \
        -Jport=$PORT \
        -Jthreads=$THREADS \
        -Jloops=$LOOPS \
        -Jframework=$FRAMEWORK \
        -j "${results_path}/${workload}.log" 2>&1 | tail -5

    echo "✓ Completed: $workload"
    echo ""
done

# Generate summary report
echo "Generating summary report..."
python3 tests/perf/scripts/summarize-workloads.py "$results_path" "$FRAMEWORK"

echo ""
echo "=== Workload Testing Complete ==="
echo "Results saved to: $results_path"
echo "Next: Review results and analyze performance metrics"
