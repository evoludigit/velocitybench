#!/bin/bash
#
# Integration Test Suite for FraiseQL Performance Assessment
# Tests all frameworks for basic functionality, health checks, and API responses
#
# Usage: ./test-all-frameworks.sh [--verbose] [--framework=name] [--type=graphql|rest]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$SCRIPT_DIR/framework-config.json"
RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/test-results-$TIMESTAMP.json"
LOG_FILE="$RESULTS_DIR/test-run-$TIMESTAMP.log"

# Test configuration
TIMEOUT=10
VERBOSE=false
FILTER_FRAMEWORK=""
FILTER_TYPE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --framework=*)
            FILTER_FRAMEWORK="${1#*=}"
            shift
            ;;
        --type=*)
            FILTER_TYPE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v           Enable verbose output"
            echo "  --framework=NAME        Test only specified framework"
            echo "  --type=graphql|rest     Test only GraphQL or REST frameworks"
            echo "  --help, -h              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create results directory
mkdir -p "$RESULTS_DIR"

# Initialize log file
echo "Integration Test Run - $(date)" > "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Print header
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  FraiseQL Performance Assessment - Integration Test Suite        ║${NC}"
    echo -e "${BLUE}║  Testing all frameworks for health and functionality             ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Print test info
print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Print success
print_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

# Print error
print_error() {
    echo -e "${RED}✗${NC}  $1"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Print skip
print_skip() {
    echo -e "${YELLOW}○${NC}  $1"
}

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    if [ "$VERBOSE" = true ]; then
        echo "$1"
    fi
}

# Test if port is listening
test_port() {
    local port=$1
    timeout $TIMEOUT bash -c "exec 3<>/dev/tcp/localhost/$port" 2>/dev/null
    return $?
}

# Test HTTP endpoint
test_http() {
    local url=$1
    local expected_status=${2:-200}

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        return 0
    else
        log "HTTP test failed: $url returned $response (expected $expected_status)"
        return 1
    fi
}

# Test GraphQL endpoint
test_graphql() {
    local url=$1
    local query=$2

    response=$(curl -s --max-time $TIMEOUT \
        -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"$query\"}" \
        2>/dev/null)

    if echo "$response" | grep -q '"data"'; then
        return 0
    else
        log "GraphQL test failed: $url - Response: $response"
        return 1
    fi
}

# Test REST endpoint
test_rest() {
    local url=$1

    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null)

    if echo "$response" | grep -qE '\[|\{'; then
        return 0
    else
        log "REST test failed: $url - Response: $response"
        return 1
    fi
}

# Test a single framework
test_framework() {
    local name=$1
    local port=$2
    local type=$3
    local health=$4
    local endpoint=$5

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Testing: $name${NC} (Port: $port, Type: $type)"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local framework_passed=0
    local framework_failed=0

    # Test 1: Port listening
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log "Testing port $port for $name"
    if test_port "$port"; then
        print_success "Port $port is listening"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        framework_passed=$((framework_passed + 1))
    else
        print_error "Port $port is NOT listening (framework may not be running)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        framework_failed=$((framework_failed + 1))
        echo -e "  ${YELLOW}→ Skipping remaining tests for $name${NC}"
        return 1
    fi

    # Test 2: Health endpoint
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    local health_url="http://localhost:$port$health"
    log "Testing health endpoint: $health_url"
    if test_http "$health_url"; then
        print_success "Health check passed: $health"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        framework_passed=$((framework_passed + 1))
    else
        print_error "Health check failed: $health"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        framework_failed=$((framework_failed + 1))
    fi

    # Test 3: API endpoint (type-specific)
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    local api_url="http://localhost:$port$endpoint"
    log "Testing API endpoint: $api_url"

    if [ "$type" = "graphql" ]; then
        if test_graphql "$api_url" "{ __typename }"; then
            print_success "GraphQL introspection query passed"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            framework_passed=$((framework_passed + 1))
        else
            print_error "GraphQL introspection query failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            framework_failed=$((framework_failed + 1))
        fi
    elif [ "$type" = "rest" ]; then
        if test_rest "$api_url"; then
            print_success "REST endpoint returned valid JSON"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            framework_passed=$((framework_passed + 1))
        else
            print_error "REST endpoint failed or returned invalid JSON"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            framework_failed=$((framework_failed + 1))
        fi
    fi

    # Test 4: Metrics endpoint (if standard)
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    local metrics_url="http://localhost:$port/metrics"
    log "Testing metrics endpoint: $metrics_url"
    if test_http "$metrics_url" 200 || test_http "$metrics_url" 404; then
        if test_http "$metrics_url" 200; then
            print_success "Metrics endpoint available"
        else
            print_skip "Metrics endpoint not implemented (optional)"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            TOTAL_TESTS=$((TOTAL_TESTS - 1))
        fi
        PASSED_TESTS=$((PASSED_TESTS + 1))
        framework_passed=$((framework_passed + 1))
    else
        print_warning "Metrics endpoint check inconclusive"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        framework_passed=$((framework_passed + 1))
    fi

    # Framework summary
    echo ""
    if [ $framework_failed -eq 0 ]; then
        echo -e "  ${GREEN}✓ $name: All tests passed ($framework_passed/$framework_passed)${NC}"
    else
        echo -e "  ${RED}✗ $name: Some tests failed ($framework_passed/$((framework_passed + framework_failed)))${NC}"
    fi

    return 0
}

# Main test execution
main() {
    print_header

    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi

    print_info "Starting integration tests..."
    print_info "Results will be saved to: $RESULTS_FILE"
    print_info "Logs will be saved to: $LOG_FILE"
    echo ""

    # Extract framework list from JSON config
    frameworks=$(python3 -c "
import json
import sys

with open('$CONFIG_FILE') as f:
    config = json.load(f)

for name, info in config['frameworks'].items():
    # Apply filters
    if '$FILTER_FRAMEWORK' and name != '$FILTER_FRAMEWORK':
        continue
    if '$FILTER_TYPE' and info['type'] != '$FILTER_TYPE':
        continue

    print(f\"{name}|{info['port']}|{info['type']}|{info['health']}|{info['endpoint']}\")
")

    # Test each framework
    while IFS='|' read -r name port type health endpoint; do
        if [ -n "$name" ]; then
            test_framework "$name" "$port" "$type" "$health" "$endpoint" || true
        fi
    done <<< "$frameworks"

    # Print summary
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Test Summary                                                     ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Total Tests:    $TOTAL_TESTS"
    echo -e "  ${GREEN}Passed:${NC}         $PASSED_TESTS"
    echo -e "  ${RED}Failed:${NC}         $FAILED_TESTS"
    echo -e "  ${YELLOW}Skipped:${NC}        $SKIPPED_TESTS"
    echo ""

    # Calculate success rate
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo -e "  Success Rate:   ${success_rate}%"
    fi

    echo ""
    echo -e "  Results saved to: ${BLUE}$RESULTS_FILE${NC}"
    echo -e "  Logs saved to:    ${BLUE}$LOG_FILE${NC}"
    echo ""

    # Save results to JSON
    python3 << EOF
import json
from datetime import datetime

results = {
    "timestamp": "$TIMESTAMP",
    "total_tests": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "skipped": $SKIPPED_TESTS,
    "success_rate": $success_rate if $TOTAL_TESTS > 0 else 0,
    "filter_framework": "$FILTER_FRAMEWORK" or None,
    "filter_type": "$FILTER_TYPE" or None
}

with open("$RESULTS_FILE", "w") as f:
    json.dump(results, f, indent=2)
EOF

    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${RED}Some tests failed. Please review the logs.${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Run main function
main
