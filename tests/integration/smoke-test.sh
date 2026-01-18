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
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Framework definitions (name:port:health_path)
# Note: Hasura and PostGraphile use profiles, so they may not always be running
FRAMEWORKS=(
    "fraiseql:4000:/health"
    "strawberry:8011:/health"
    "graphene:8002:/health"
    "apollo-server:4002:/health"
    "apollo-orm:4005:/health"
    "async-graphql:8016:/health"
    "go-gqlgen:4010:/health"
    "ruby-rails:8012:/api/health"
    "express-rest:8005:/health"
    "express-orm:8007:/health"
    "fastapi-rest:8003:/health"
    "flask-rest:8004:/health"
    "actix-web-rest:8015:/health"
    "gin-rest:8006:/health"
    "java-spring-boot:8010:/actuator/health"
)

# Profile-based frameworks (run with: docker-compose --profile <name> up -d)
PROFILE_FRAMEWORKS=(
    "hasura:4000:/healthz"
    "postgraphile:4000:/health"
    "ariadne:4000:/health"
    "asgi-graphql:4000:/health"
    "graphql-yoga:4000:/health"
    "mercurius:4000:/health"
    "express-graphql:4000:/health"
    "graphql-go:4000:/health"
)

# Test each framework
for framework_def in "${FRAMEWORKS[@]}"; do
    IFS=':' read -r name port health <<< "$framework_def"

    url="http://localhost:$port$health"

    # Quick HTTP check
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} ${name:0:20} $(printf '%20s' ' ') http://localhost:$port"
        RUNNING=$((RUNNING + 1))
    else
        echo -e "${RED}✗${NC} ${name:0:20} $(printf '%20s' ' ') http://localhost:$port (status: $response)"
        STOPPED=$((STOPPED + 1))
    fi
done

# Test profile-based frameworks (optional)
echo ""
echo -e "${BLUE}Profile-based frameworks (use: docker-compose --profile <name> up -d)${NC}"
for framework_def in "${PROFILE_FRAMEWORKS[@]}"; do
    IFS=':' read -r name port health <<< "$framework_def"

    url="http://localhost:$port$health"

    # Quick HTTP check
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} ${name:0:20} $(printf '%20s' ' ') http://localhost:$port (profile)"
        RUNNING=$((RUNNING + 1))
    else
        echo -e "${YELLOW}○${NC} ${name:0:20} $(printf '%20s' ' ') http://localhost:$port (not running - use --profile $name)"
    fi
done

# Summary
echo ""
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Running:${NC}  $RUNNING"
echo -e "  ${RED}Stopped:${NC}  $STOPPED"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $STOPPED -eq 0 ]; then
    echo -e "${GREEN}All frameworks are running!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some frameworks are not running. Start them with: docker-compose up -d${NC}"
    exit 1
fi
