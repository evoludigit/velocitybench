#!/bin/bash
set -e

echo "Linting Go frameworks..."

FRAMEWORKS=(
  "frameworks/gin-rest"
  "frameworks/go-gqlgen"
)

for dir in "${FRAMEWORKS[@]}"; do
  if [ -d "$dir" ]; then
    echo ""
    echo "→ Checking $dir..."
    (
      cd "$dir"
      echo "  Checking formatting..."
      gofmt -l -d . 2>&1 || true

      # golangci-lint if available
      if command -v golangci-lint &> /dev/null; then
        echo "  Running golangci-lint..."
        golangci-lint run ./... 2>&1 || true
      else
        echo "  (golangci-lint not installed, skipping)"
      fi
    )
  fi
done

echo ""
echo "✓ Go linting check complete"
