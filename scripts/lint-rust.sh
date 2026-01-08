#!/bin/bash
set -e

echo "Linting Rust frameworks..."

if [ -d "frameworks/actix-web-rest" ]; then
  echo ""
  echo "→ Checking frameworks/actix-web-rest..."
  (
    cd frameworks/actix-web-rest
    echo "  Running clippy..."
    cargo clippy --all-targets --all-features 2>&1 || true
    echo "  Checking formatting..."
    cargo fmt --check 2>&1 || true
  )
fi

echo ""
echo "✓ Rust linting check complete"
