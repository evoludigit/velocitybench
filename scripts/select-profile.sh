#!/bin/bash
# Helper script to select PostgreSQL profile and verify configuration
#
# Usage:
#   ./scripts/select-profile.sh powerful   # Select powerful profile
#   ./scripts/select-profile.sh laptop     # Select laptop profile
#   ./scripts/select-profile.sh standard   # Select standard profile
#   ./scripts/select-profile.sh ci         # Select CI profile
#   ./scripts/select-profile.sh            # Show available profiles

set -e

PROFILE="${1:-}"
PROFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    cat << 'EOF'
Select PostgreSQL performance profile for benchmarks

Usage:
  ./scripts/select-profile.sh PROFILE

Available profiles:
  ci          - CI/CD pipeline (minimal resources)
  laptop      - Developer laptop (2-4GB Docker allocation)
  standard    - Cloud server (8-12GB Docker allocation)
  powerful    - Powerful workstation (20-30GB Docker allocation)

Examples:
  ./scripts/select-profile.sh powerful
  ./scripts/select-profile.sh laptop
  ./scripts/select-profile.sh ci

After selecting, start with:
  docker-compose up

Verify configuration:
  docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -c 'SHOW shared_buffers;'
EOF
}

if [[ -z "$PROFILE" ]]; then
    show_help
    exit 0
fi

# Validate profile exists
ENV_FILE="${PROFILES_DIR}/.env.${PROFILE}"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}Error: Profile '$PROFILE' not found${NC}"
    echo -e "${YELLOW}Available profiles:${NC}"
    ls -1 "${PROFILES_DIR}"/.env.* 2>/dev/null | xargs -I {} basename {} .env. | sed 's/^/  /' || true
    exit 1
fi

# Select profile
TARGET_ENV="${PROFILES_DIR}/.env"
cp "$ENV_FILE" "$TARGET_ENV"

echo -e "${GREEN}✓ Selected profile: ${BLUE}${PROFILE}${NC}"
echo ""
echo "Profile settings:"
echo "  $(grep '^DB_' "$TARGET_ENV" | sed 's/^/  /')"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start environment:"
echo "     ${BLUE}docker-compose up${NC}"
echo ""
echo "  2. Verify configuration (in another terminal):"
echo "     ${BLUE}docker-compose exec postgres psql -U benchmark -d fraiseql_benchmark -c 'SHOW shared_buffers;'${NC}"
echo ""
echo "  3. Run benchmarks:"
echo "     ${BLUE}pytest tests/performance/test_performance.py -v -s${NC}"
