#!/bin/bash
set -e

echo "Linting Python frameworks..."

FRAMEWORKS=(
  "frameworks/fastapi-rest"
  "frameworks/flask-rest"
  "frameworks/strawberry"
  "frameworks/graphene"
  "frameworks/fraiseql"
)

for dir in "${FRAMEWORKS[@]}"; do
  if [ -d "$dir" ]; then
    echo ""
    echo "→ Checking $dir..."
    (
      cd "$dir"
      python -m ruff check . 2>&1 || true
      ty check . 2>&1 || true
    )
  fi
done

echo ""
echo "✓ Python linting check complete"
