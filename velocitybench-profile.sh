# VelocityBench Shell Profile Setup
# Add this to your ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish
#
# For bash/zsh:
#   echo 'source /path/to/velocitybench/bin/velocitybench-profile.sh' >> ~/.bashrc
#   source ~/.bashrc
#
# For fish:
#   echo 'source /path/to/velocitybench/bin/velocitybench-profile.fish' >> ~/.config/fish/config.fish
#   source ~/.config/fish/config.fish

# Only load if we're in a velocitybench directory
if [ ! -f "README.md" ] || ! grep -q "VelocityBench" "README.md" 2>/dev/null; then
    return 0
fi

# Set environment variables
export VELOCITYBENCH_ROOT="$(pwd)"
export PYTHONPATH="${VELOCITYBENCH_ROOT}:${PYTHONPATH}"
export DATABASE_HOST=${DATABASE_HOST:-localhost}
export DATABASE_PORT=${DATABASE_PORT:-5433}
export DATABASE_NAME=${DATABASE_NAME:-velocitybench}
export DATABASE_USER=${DATABASE_USER:-postgres}
export DATABASE_PASSWORD=${DATABASE_PASSWORD:-postgres}

# Add bin directory to PATH
export PATH="${VELOCITYBENCH_ROOT}/bin:${PATH}"

# Shortcut: Quick smoke test
bench-quick() {
    echo "Running quick smoke test..."
    ./tests/integration/smoke-test.sh
}

# Shortcut: Full integration tests
bench-full() {
    echo "Running full integration tests..."
    ./tests/integration/test-all-frameworks.sh --verbose
}

# Shortcut: Test specific framework
bench-framework() {
    if [ -z "$1" ]; then
        echo "Usage: bench-framework [framework-name]"
        list-frameworks
        return 1
    fi
    echo "Testing framework: $1"
    ./tests/integration/test-all-frameworks.sh --framework="$1" --verbose
}

# Shortcut: Quick performance benchmark
perf-quick() {
    echo "Running quick performance benchmark (10 min)..."
    make perf PROFILE=quick
}

# Shortcut: Full performance benchmark
perf-full() {
    echo "Running full performance benchmark..."
    make perf PROFILE=extended
}

# Shortcut: Compare against baseline
perf-compare() {
    echo "Comparing against baseline..."
    if [ -f "tests/perf/results/baseline.json" ]; then
        latest_comparison=$(ls -t tests/perf/results/comparison-*.json 2>/dev/null | head -1)
        if [ -n "$latest_comparison" ]; then
            python scripts/compare-baseline.py \
                tests/perf/results/baseline.json \
                "$latest_comparison"
        else
            echo "No comparison results found. Run 'perf-full' first."
        fi
    else
        echo "❌ No baseline found. Run 'perf-full' first to establish baseline."
    fi
}

# Shortcut: Format code
fmt-code() {
    echo "Formatting code with Ruff..."
    if [ -f "venv/bin/ruff" ]; then
        venv/bin/ruff format .
    else
        echo "❌ Ruff not found. Run ./setup.sh first."
        return 1
    fi
    echo "✅ Done!"
}

# Shortcut: Lint code
lint-code() {
    echo "Linting code with Ruff..."
    if [ -f "venv/bin/ruff" ]; then
        venv/bin/ruff check . --show-fixes
    else
        echo "❌ Ruff not found. Run ./setup.sh first."
        return 1
    fi
}

# Shortcut: Type check
type-check() {
    echo "Type checking with ty..."
    if [ -f "venv/bin/ty" ]; then
        venv/bin/ty check .
    else
        echo "❌ ty not found. Run ./setup.sh first."
        return 1
    fi
}

# Shortcut: Docker logs
docker-logs() {
    if [ -z "$1" ]; then
        echo "Usage: docker-logs [service]"
        echo "Available services:"
        docker-compose ps | tail -n +2 | awk '{print "  - " $1}' 2>/dev/null || echo "  (run: docker-compose up -d)"
        return 1
    fi
    docker-compose logs -f "$1"
}

# Shortcut: Docker shell
docker-shell() {
    if [ -z "$1" ]; then
        echo "Usage: docker-shell [service]"
        echo "Available services:"
        docker-compose ps | tail -n +2 | awk '{print "  - " $1}' 2>/dev/null || echo "  (run: docker-compose up -d)"
        return 1
    fi
    docker-compose exec "$1" /bin/bash || docker-compose exec "$1" /bin/sh
}

# Shortcut: List frameworks
list-frameworks() {
    echo "📦 Available frameworks:"
    if [ -d "frameworks" ]; then
        ls -1 frameworks/ | grep -v "^[._]" | nl
    else
        echo "  (no frameworks directory)"
    fi
}

# Shortcut: Add framework
add-framework() {
    if [ -z "$1" ]; then
        echo "Interactive framework addition"
        printf "Framework name: "
        read -r framework_name
    else
        framework_name="$1"
    fi
    echo "📚 See docs/ADD_FRAMEWORK_GUIDE.md for detailed instructions"
    echo "Creating: frameworks/$framework_name"
    mkdir -p "frameworks/$framework_name"
    cat > "frameworks/$framework_name/README.md" << 'EOF'
# [Framework Name] Implementation

[Add description here]

## Setup

[Add setup instructions]

## Testing

[Add test instructions]
EOF
    echo "✅ Framework directory created!"
    echo "Next: Review docs/ADD_FRAMEWORK_GUIDE.md"
}

# Shortcut: Test specific framework
test-framework() {
    if [ -z "$1" ]; then
        echo "Usage: test-framework [framework-name]"
        list-frameworks
        return 1
    fi

    framework_path="frameworks/$1"
    if [ ! -d "$framework_path" ]; then
        echo "❌ Framework not found: $1"
        list-frameworks
        return 1
    fi

    echo "Testing $1..."
    (
        cd "$framework_path" || return 1

        if [ -f "requirements.txt" ]; then
            if [ -d ".venv" ]; then
                # shellcheck source=/dev/null
                source .venv/bin/activate
                python -m pytest tests/ -v
                deactivate
            else
                echo "❌ Virtual environment not found. Run: ./setup.sh --frameworks"
                return 1
            fi
        elif [ -f "package.json" ]; then
            npm test
        else
            echo "❌ No test configuration found for $1"
            return 1
        fi
    )
}

# Shortcut: Show help
vb-help() {
    cat << 'EOF'
═══════════════════════════════════════════════════════════════════
  VelocityBench Quick Reference
═══════════════════════════════════════════════════════════════════

📋 Common Commands:
  make help                 - Show all Make targets
  make venv-check          - Verify environments
  make db-up               - Start database
  make db-down             - Stop database

🧪 Testing:
  bench-quick              - Quick smoke test
  bench-full               - Full test suite
  bench-framework [name]   - Test specific framework

📊 Performance:
  perf-quick               - 10-minute benchmark
  perf-full                - Full benchmark suite
  perf-compare             - Compare against baseline

📚 Documentation:
  docs-open                - Open documentation
  docs-search [term]       - Search documentation

🛠️  Development:
  fmt-code                 - Format code (Ruff)
  lint-code                - Lint code (Ruff)
  type-check               - Type check Python

🐳 Docker:
  docker-logs [service]    - View service logs
  docker-shell [service]   - Enter service shell

📚 Frameworks:
  list-frameworks          - Show all frameworks
  add-framework [name]     - Add new framework (interactive)
  test-framework [name]    - Test specific framework

ℹ️  For more details: make help
═══════════════════════════════════════════════════════════════════
EOF
}

# Print welcome message
echo ""
echo "🚀 VelocityBench environment loaded"
echo "Type 'vb-help' for quick reference"
echo ""
