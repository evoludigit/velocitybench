#!/bin/bash
# Post-creation setup script for VelocityBench development container

set -e

echo "🚀 VelocityBench Development Container Setup"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Install system dependencies
echo -e "${BLUE}📦 Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq \
  build-essential \
  curl \
  git \
  git-lfs \
  jq \
  postgresql-client \
  mysql-client \
  make \
  unzip \
  > /dev/null 2>&1

# Install Rust tools
echo -e "${BLUE}🦀 Setting up Rust...${NC}"
rustup component add clippy rustfmt 2>/dev/null || true

# Install uv (Python package manager)
echo -e "${BLUE}🐍 Installing uv package manager...${NC}"
pip install -q uv

# Install pre-commit
echo -e "${BLUE}🔧 Installing pre-commit hooks...${NC}"
pip install -q pre-commit
pre-commit install || true

# Set up root Python venv
echo -e "${BLUE}🐍 Setting up root Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || true
deactivate

# Set up database venv
if [ -f database/pyproject.toml ]; then
  echo -e "${BLUE}💾 Setting up database environment...${NC}"
  cd database
  uv sync -q 2>/dev/null || true
  cd ..
fi

# Set up framework venvs (optional - comment out to speed up setup)
# echo -e "${BLUE}📚 Setting up framework environments...${NC}"
# for framework in fastapi-rest flask-rest strawberry graphene; do
#   if [ -d "frameworks/$framework" ] && [ -f "frameworks/$framework/pyproject.toml" ]; then
#     echo "  - Setting up $framework..."
#     cd "frameworks/$framework"
#     python3 -m venv .venv
#     .venv/bin/pip install -q -r requirements.txt 2>/dev/null || true
#     .venv/bin/pip install -q -r requirements-dev.txt 2>/dev/null || true
#     cd ../..
#   fi
# done

echo ""
echo -e "${GREEN}✅ VelocityBench development environment ready!${NC}"
echo ""
echo "Quick start commands:"
echo "  make help              - Show available commands"
echo "  make venv-check        - Verify virtual environments"
echo "  make db-up             - Start database containers"
echo "  ./tests/integration/smoke-test.sh  - Run framework health checks"
echo ""
echo "Docker Compose will start on demand for database services."
echo ""
