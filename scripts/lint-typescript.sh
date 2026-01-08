#!/bin/bash
set -e

echo "Linting TypeScript frameworks..."

FRAMEWORKS=(
  "frameworks/express-rest"
  "frameworks/apollo-server"
)

for dir in "${FRAMEWORKS[@]}"; do
  if [ -d "$dir" ]; then
    echo ""
    echo "→ Checking $dir..."
    (
      cd "$dir"
      npm run lint 2>&1 || true
      npm run type-check 2>&1 || true
    )
  fi
done

echo ""
echo "✓ TypeScript linting check complete"
