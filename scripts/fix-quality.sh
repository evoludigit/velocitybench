#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"

echo "════════════════════════════════════════════════════════════════"
echo "Fixing code quality issues..."
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$ROOT_DIR"

echo "=== TypeScript/Node.js ==="
for dir in frameworks/express-rest frameworks/apollo-server; do
  if [ -d "$dir" ]; then
    echo "→ Fixing $dir..."
    (
      cd "$dir"
      npm run lint:fix 2>&1 || true
      npm run format 2>&1 || true
    )
  fi
done
echo ""

echo "=== Python ==="
for dir in frameworks/fastapi-rest frameworks/flask-rest frameworks/strawberry frameworks/graphene frameworks/fraiseql; do
  if [ -d "$dir" ]; then
    echo "→ Fixing $dir..."
    (
      cd "$dir"
      python -m ruff check . --fix 2>&1 || true
    )
  fi
done
echo ""

echo "=== Rust ==="
if [ -d "frameworks/actix-web-rest" ]; then
  echo "→ Fixing frameworks/actix-web-rest..."
  (
    cd frameworks/actix-web-rest
    cargo fmt 2>&1 || true
  )
fi
echo ""

echo "=== Go ==="
for dir in frameworks/gin-rest frameworks/go-gqlgen; do
  if [ -d "$dir" ]; then
    echo "→ Fixing $dir..."
    (
      cd "$dir"
      gofmt -w . 2>&1 || true
    )
  fi
done
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✓ Code quality fixes complete!"
echo "════════════════════════════════════════════════════════════════"
