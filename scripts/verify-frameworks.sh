#!/bin/bash

# Framework Status Verification Script
# Checks all frameworks are running and healthy

echo "════════════════════════════════════════════════════════════════"
echo "  Framework Status Verification"
echo "════════════════════════════════════════════════════════════════"
echo ""

declare -A PORTS=(
  ["fraiseql"]="4000"
  ["strawberry"]="8011"
  ["graphene"]="8002"
  ["fastapi-rest"]="8003"
  ["flask-rest"]="8004"
  ["apollo-server"]="4001"
  ["express-rest"]="8005"
  ["go-gqlgen"]="4003"
  ["gin-rest"]="8006"
)

declare -A ENDPOINTS=(
  ["fraiseql"]="/health"
  ["strawberry"]="/health"
  ["graphene"]="/health"
  ["fastapi-rest"]="/health"
  ["flask-rest"]="/health"
  ["apollo-server"]="/graphql"
  ["express-rest"]="/health"
  ["go-gqlgen"]="/health"
  ["gin-rest"]="/health"
)

declare -A DISPLAY_NAMES=(
  ["fraiseql"]="FraiseQL"
  ["strawberry"]="Strawberry"
  ["graphene"]="Graphene"
  ["fastapi-rest"]="FastAPI"
  ["flask-rest"]="Flask"
  ["apollo-server"]="Apollo"
  ["express-rest"]="Express"
  ["go-gqlgen"]="gqlgen"
  ["gin-rest"]="Gin"
)

ALL_HEALTHY=true

for framework in "${!PORTS[@]}"; do
  port="${PORTS[$framework]}"
  endpoint="${ENDPOINTS[$framework]}"
  display_name="${DISPLAY_NAMES[$framework]}"

  # Check container status
  container="fraiseql-performance-assessment-${framework}-1"
  if ! docker ps | grep -q "$container"; then
    echo "❌ $display_name - Container not running"
    ALL_HEALTHY=false
    continue
  fi

  # Check HTTP response
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${endpoint}" 2>/dev/null || echo "000")

  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✅ $display_name - Healthy (port $port)"
  elif [ "$HTTP_CODE" = "000" ]; then
    echo "⚠️  $display_name - No response (port $port)"
    ALL_HEALTHY=false
  else
    echo "⚠️  $display_name - HTTP $HTTP_CODE (port $port)"
    ALL_HEALTHY=false
  fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"

if [ "$ALL_HEALTHY" = true ]; then
  echo "  ✅ All frameworks are healthy"
  exit 0
else
  echo "  ⚠️  Some frameworks have issues"
  exit 1
fi