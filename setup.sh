#!/bin/bash
#
# VelocityBench One-Command Setup Script
#
# Usage: ./setup.sh [OPTIONS]
# Options:
#   --frameworks       Install all framework dependencies
#   --minimal          Skip optional dependencies
#   --dev              Install development tools
#   --help             Show this help message

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Defaults
INSTALL_FRAMEWORKS=false
INSTALL_DEV=false
MINIMAL=false
VERBOSE=false

# Helper functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --frameworks)
            INSTALL_FRAMEWORKS=true
            shift
            ;;
        --dev)
            INSTALL_DEV=true
            shift
            ;;
        --minimal)
            MINIMAL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "^#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Welcome
print_header "VelocityBench Setup"
echo ""
echo "This script will set up your VelocityBench development environment."
echo ""
echo "What will be installed:"
echo "  ✅ System dependencies (if needed)"
echo "  ✅ Python virtual environments"
echo "  ✅ Project dependencies"
echo "  ✅ Pre-commit hooks"
echo "  ✅ Docker containers (PostgreSQL)"

if [ "$INSTALL_FRAMEWORKS" = true ]; then
    echo "  ✅ Framework dependencies"
fi

if [ "$INSTALL_DEV" = true ]; then
    echo "  ✅ Development tools (linters, type checkers)"
fi

echo ""

# OS Detection
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "linux")
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
}

# Check Python version
check_python() {
    print_header "Checking Python"

    if ! check_command python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    python_version=$(python3 --version | awk '{print $2}')
    print_success "Python $python_version"

    # Check Python version is 3.11+
    version_major=$(echo "$python_version" | cut -d. -f1)
    version_minor=$(echo "$python_version" | cut -d. -f2)

    if [ "$version_major" -lt 3 ] || ([ "$version_major" -eq 3 ] && [ "$version_minor" -lt 11 ]); then
        print_error "Python 3.11+ is required (found $python_version)"
        exit 1
    fi
}

# Check required tools
check_requirements() {
    print_header "Checking Requirements"

    local missing=0

    # Python
    if check_command python3; then
        print_success "Python 3"
    else
        print_error "Python 3 not found"
        missing=$((missing + 1))
    fi

    # Git
    if check_command git; then
        print_success "Git"
    else
        print_error "Git not found"
        missing=$((missing + 1))
    fi

    # Docker (optional but recommended)
    if check_command docker; then
        print_success "Docker"
    else
        print_warning "Docker not found (required for database services)"
    fi

    if [ "$INSTALL_FRAMEWORKS" = true ]; then
        # Node.js for JavaScript frameworks
        if check_command node; then
            print_success "Node.js $(node --version)"
        else
            print_warning "Node.js not found (required for JavaScript frameworks)"
        fi

        # Go for Go frameworks
        if check_command go; then
            print_success "Go $(go version | awk '{print $3}')"
        else
            print_warning "Go not found (required for Go frameworks)"
        fi

        # Rust for Rust frameworks
        if check_command rustc; then
            print_success "Rust $(rustc --version | awk '{print $2}')"
        else
            print_warning "Rust not found (required for Rust frameworks)"
        fi
    fi

    if [ $missing -gt 0 ]; then
        print_error "$missing required tool(s) not found"
        echo ""
        echo "Install missing tools with:"
        echo "  Ubuntu/Debian: sudo apt-get install git python3"
        echo "  macOS: brew install git python@3.12"
        echo "  Windows: Use WSL or install from python.org"
        exit 1
    fi
}

# Create root virtual environment
setup_root_venv() {
    print_header "Setting up Root Virtual Environment"

    if [ -d "$PROJECT_ROOT/venv" ]; then
        print_warning "Virtual environment already exists, skipping"
        return
    fi

    python3 -m venv "$PROJECT_ROOT/venv"
    source "$PROJECT_ROOT/venv/bin/activate"

    pip install --upgrade pip setuptools wheel -q

    # Install root requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt" -q
        print_success "Root dependencies installed"
    fi

    deactivate
}

# Set up pre-commit hooks
setup_precommit() {
    print_header "Setting up Pre-Commit Hooks"

    source "$PROJECT_ROOT/venv/bin/activate"

    if pip show pre-commit > /dev/null 2>&1; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        pip install pre-commit -q
        pre-commit install
        print_success "Pre-commit hooks installed"
    fi

    deactivate
}

# Set up database virtual environment
setup_database_venv() {
    print_header "Setting up Database Virtual Environment"

    db_venv="$PROJECT_ROOT/database/.venv"

    if [ -d "$db_venv" ]; then
        print_warning "Database venv already exists, skipping"
        return
    fi

    cd "$PROJECT_ROOT/database"

    # Try uv first (faster)
    if command -v uv &> /dev/null; then
        print_info "Using uv for database environment"
        uv sync -q
    else
        # Fall back to pip
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r pyproject.toml -q
        deactivate
    fi

    print_success "Database environment created"
    cd "$PROJECT_ROOT"
}

# Set up framework environments
setup_framework_venvs() {
    print_header "Setting up Framework Virtual Environments"

    frameworks=(
        "fastapi-rest"
        "flask-rest"
        "strawberry"
        "graphene"
    )

    for framework in "${frameworks[@]}"; do
        framework_path="$PROJECT_ROOT/frameworks/$framework"

        if [ ! -d "$framework_path" ]; then
            continue
        fi

        if [ -d "$framework_path/.venv" ]; then
            print_warning "$framework: venv already exists"
            continue
        fi

        print_info "Setting up $framework..."

        cd "$framework_path"

        python3 -m venv .venv
        source .venv/bin/activate

        pip install --upgrade pip -q

        # Install requirements
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt -q
        fi

        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt -q
        fi

        deactivate

        print_success "$framework ready"
    done

    cd "$PROJECT_ROOT"
}

# Set up QA test environment
setup_qa_venv() {
    print_header "Setting up QA Test Environment"

    qa_path="$PROJECT_ROOT/tests/qa"

    if [ -d "$qa_path/.venv" ]; then
        print_warning "QA venv already exists, skipping"
        return
    fi

    cd "$qa_path"

    python3 -m venv .venv
    source .venv/bin/activate

    pip install --upgrade pip -q

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
    fi

    deactivate

    print_success "QA environment ready"

    cd "$PROJECT_ROOT"
}

# Initialize Docker containers
init_docker() {
    print_header "Initializing Docker Containers"

    if ! check_command docker; then
        print_warning "Docker not found, skipping container initialization"
        return
    fi

    if ! check_command docker-compose; then
        print_warning "Docker Compose not found, skipping container initialization"
        return
    fi

    # Check if containers already running
    if docker ps | grep -q "postgres"; then
        print_info "Database containers already running"
        return
    fi

    print_info "Starting PostgreSQL container..."
    docker-compose up -d postgres 2>/dev/null || print_warning "Could not start containers"

    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    sleep 5

    if docker ps | grep -q "postgres"; then
        print_success "Database container started"
    else
        print_warning "Database container may not have started properly"
    fi
}

# Verify setup
verify_setup() {
    print_header "Verifying Setup"

    local issues=0

    # Check virtual environments
    if [ -d "$PROJECT_ROOT/venv" ]; then
        print_success "Root virtual environment"
    else
        print_error "Root virtual environment not found"
        issues=$((issues + 1))
    fi

    if [ -d "$PROJECT_ROOT/database/.venv" ]; then
        print_success "Database virtual environment"
    else
        print_warning "Database virtual environment not found"
    fi

    # Check pre-commit
    if [ -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
        print_success "Pre-commit hooks installed"
    else
        print_warning "Pre-commit hooks not installed"
    fi

    # Check Docker
    if check_command docker; then
        if docker ps | grep -q "postgres"; then
            print_success "Database container running"
        else
            print_warning "Database container not running (start with: docker-compose up -d)"
        fi
    fi

    if [ $issues -gt 0 ]; then
        print_warning "Setup completed with $issues warnings"
    else
        print_success "Setup completed successfully!"
    fi
}

# Main execution
main() {
    detect_os
    check_python
    check_requirements

    # Create directories if needed
    mkdir -p "$PROJECT_ROOT/logs"

    # Setup
    setup_root_venv
    setup_precommit
    setup_database_venv
    setup_qa_venv

    if [ "$INSTALL_FRAMEWORKS" = true ]; then
        setup_framework_venvs
    fi

    init_docker

    verify_setup

    echo ""
    print_header "Next Steps"
    echo ""
    echo "Quick start:"
    echo "  1. Activate root environment:  source venv/bin/activate"
    echo "  2. Start database:             docker-compose up -d"
    echo "  3. Check status:               make venv-check"
    echo "  4. View commands:              make help"
    echo ""
    echo "Run tests:"
    echo "  ./tests/integration/smoke-test.sh"
    echo ""
    echo "View documentation:"
    echo "  - Quick start: cat QUICK_START.md"
    echo "  - Development: cat DEVELOPMENT.md"
    echo "  - Contributing: cat CONTRIBUTING.md"
    echo ""
    print_success "Setup complete! Happy coding 🚀"
}

# Run main function
main "$@"
