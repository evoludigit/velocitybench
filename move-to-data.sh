#!/bin/bash
set -e

echo "=========================================="
echo "Moving VelocityBench to /data Storage"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_HOME="/home/lionel/code/velocitybench"
DATA_STORAGE="/data/velocitybench-storage"

# Step 1: Clean Docker
echo -e "${YELLOW}[1/5] Cleaning Docker...${NC}"
docker system prune -af --volumes 2>/dev/null || true
echo -e "${GREEN}✓ Docker cleanup complete${NC}"
echo ""

# Step 2: Create storage directory
echo -e "${YELLOW}[2/5] Creating /data storage structure...${NC}"
mkdir -p "$DATA_STORAGE/seed-data-output"
mkdir -p "$DATA_STORAGE/venvs"
echo -e "${GREEN}✓ Storage directories created${NC}"
echo ""

# Step 3: Move seed-data output
echo -e "${YELLOW}[3/5] Moving seed-data output to /data...${NC}"
if [ -d "$PROJECT_HOME/database/seed-data/output" ] && [ ! -L "$PROJECT_HOME/database/seed-data/output" ]; then
    mv "$PROJECT_HOME/database/seed-data/output"/* "$DATA_STORAGE/seed-data-output/" 2>/dev/null || true
    rmdir "$PROJECT_HOME/database/seed-data/output"
    ln -s "$DATA_STORAGE/seed-data-output" "$PROJECT_HOME/database/seed-data/output"
    echo -e "${GREEN}✓ Seed data moved and symlinked${NC}"
else
    echo -e "${YELLOW}⚠ Seed-data output already symlinked or doesn't exist${NC}"
fi
echo ""

# Step 4: Move venvs
echo -e "${YELLOW}[4/5] Moving Python virtual environments to /data...${NC}"

# Root venv
if [ -d "$PROJECT_HOME/venv" ] && [ ! -L "$PROJECT_HOME/venv" ]; then
    echo "  Moving root venv..."
    mv "$PROJECT_HOME/venv" "$DATA_STORAGE/venvs/root-venv"
    ln -s "$DATA_STORAGE/venvs/root-venv" "$PROJECT_HOME/venv"
fi

# Framework venvs
for framework in frameworks/*/; do
    if [ -d "$PROJECT_HOME/$framework/.venv" ] && [ ! -L "$PROJECT_HOME/$framework/.venv" ]; then
        framework_name=$(basename "$framework")
        echo "  Moving $framework_name/.venv..."
        mv "$PROJECT_HOME/$framework/.venv" "$DATA_STORAGE/venvs/${framework_name}-venv"
        ln -s "$DATA_STORAGE/venvs/${framework_name}-venv" "$PROJECT_HOME/$framework/.venv"
    elif [ -d "$PROJECT_HOME/$framework/venv" ] && [ ! -L "$PROJECT_HOME/$framework/venv" ]; then
        framework_name=$(basename "$framework")
        echo "  Moving $framework_name/venv..."
        mv "$PROJECT_HOME/$framework/venv" "$DATA_STORAGE/venvs/${framework_name}-venv"
        ln -s "$DATA_STORAGE/venvs/${framework_name}-venv" "$PROJECT_HOME/$framework/venv"
    fi
done

# Database venv
if [ -d "$PROJECT_HOME/database/.venv" ] && [ ! -L "$PROJECT_HOME/database/.venv" ]; then
    echo "  Moving database/.venv..."
    mv "$PROJECT_HOME/database/.venv" "$DATA_STORAGE/venvs/database-venv"
    ln -s "$DATA_STORAGE/venvs/database-venv" "$PROJECT_HOME/database/.venv"
fi

# QA venv
if [ -d "$PROJECT_HOME/tests/qa/.venv" ] && [ ! -L "$PROJECT_HOME/tests/qa/.venv" ]; then
    echo "  Moving tests/qa/.venv..."
    mv "$PROJECT_HOME/tests/qa/.venv" "$DATA_STORAGE/venvs/qa-venv"
    ln -s "$DATA_STORAGE/venvs/qa-venv" "$PROJECT_HOME/tests/qa/.venv"
fi

echo -e "${GREEN}✓ All venvs moved and symlinked${NC}"
echo ""

# Step 5: Update .gitignore
echo -e "${YELLOW}[5/5] Updating .gitignore...${NC}"
if ! grep -q "# Generated content stored in /data" "$PROJECT_HOME/.gitignore"; then
    cat >> "$PROJECT_HOME/.gitignore" << 'EOF'

# Generated content stored in /data
database/seed-data/output/
venv/
frameworks/*/.venv
frameworks/*/venv
database/.venv
tests/qa/.venv
EOF
    echo -e "${GREEN}✓ .gitignore updated${NC}"
else
    echo -e "${YELLOW}⚠ .gitignore already configured${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Migration Complete!${NC}"
echo "=========================================="
echo ""
echo "Storage moved to /data:"
echo "  • Seed data: $DATA_STORAGE/seed-data-output"
echo "  • Virtual envs: $DATA_STORAGE/venvs"
echo ""
echo "Symlinks created in project:"
echo "  • database/seed-data/output"
echo "  • venv and framework venvs"
echo ""
echo "Docker cleanup:"
echo "  • Removed unused images"
echo "  • Removed stopped containers"
echo "  • Removed build cache"
echo ""

# Show final status
echo "Current disk usage:"
df -h /home /data | tail -2
echo ""
docker system df
