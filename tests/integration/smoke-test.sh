#!/bin/bash
#
# Quick Smoke Test - Tests if all frameworks are responding
# This is a fast health-check-only test
#
# Usage: ./smoke-test.sh
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
RUNNING=0
STOPPED=0

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Quick Smoke Test - Framework Health Check                       ║${NC}"
echo -e "${BLUE}║  Dynamically reading framework configuration from JSON           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Load framework configuration from JSON
CONFIG_FILE="$(dirname "$0")/framework-config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: $CONFIG_FILE not found${NC}"
    exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required to parse framework configuration${NC}"
    echo "Install with: sudo apt-get install jq"
    exit 1
fi

# Test each framework from JSON config
echo -e "${BLUE}Testing frameworks from configuration...${NC}"
echo ""

jq -r '.frameworks | to_entries[] | "\(.key):\(.value.port):\(.value.health)"' "$CONFIG_FILE" | while IFS=':' read -r name port health; do
    url="http://localhost:$port$health"

    # Quick HTTP check
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} ${name:0:25} $(printf '%15s' ' ') Port: $port"
        RUNNING=$((RUNNING + 1))
    else
        echo -e "${RED}✗${NC} ${name:0:25} $(printf '%15s' ' ') Port: $port (status: $response)"
        STOPPED=$((STOPPED + 1))
    fi
done

# Count total from config
TOTAL=$(jq '.frameworks | length' "$CONFIG_FILE")
echo ""

# Summary
echo ""
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${BLUE}Total Frameworks:${NC}  $TOTAL"
echo -e "  ${GREEN}Running:${NC}         $RUNNING"
echo -e "  ${RED}Stopped:${NC}          $STOPPED"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $STOPPED -eq 0 ]; then
    echo -e "${GREEN}✓ All $TOTAL frameworks are running!${NC}"
    exit 0
else
    echo -e "${YELLOW}○ $RUNNING/$TOTAL frameworks running. Start them with: docker-compose up -d${NC}"
    exit 1
fi
