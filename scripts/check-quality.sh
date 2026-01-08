#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"

echo "════════════════════════════════════════════════════════════════"
echo "Running all code quality checks..."
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$ROOT_DIR"

echo "=== TypeScript/Node.js ==="
bash scripts/lint-typescript.sh
echo ""

echo "=== Python ==="
bash scripts/lint-python.sh
echo ""

echo "=== Rust ==="
bash scripts/lint-rust.sh
echo ""

echo "=== Go ==="
bash scripts/lint-go.sh
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✓ All quality checks complete!"
echo "════════════════════════════════════════════════════════════════"
