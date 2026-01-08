#!/bin/bash

# Generate all database size variations from XXLARGE master
# Run this after fraiseql_xxlarge.db generation completes

set -e

XXLARGE_DB="datasets/fraiseql_xxlarge.db"
DATASET_DIR="datasets"

echo "========================================================================"
echo "GENERATING ALL DATABASE VARIATIONS FROM XXLARGE MASTER"
echo "========================================================================"

# Check if XXLARGE exists
if [ ! -f "$XXLARGE_DB" ]; then
    echo "❌ Error: $XXLARGE_DB not found"
    echo "Please wait for XXLARGE generation to complete first"
    exit 1
fi

echo ""
echo "✓ XXLARGE master database found: $(du -h $XXLARGE_DB | cut -f1)"
echo ""

# Define variations: (name, percentage, description)
declare -a VARIATIONS=(
    "xs:0.5:Extra Small"
    "small:1.0:Small"
    "medium:5.0:Medium"
    "large:10.0:Large"
    "xlarge:50.0:X-Large"
)

# Generate each variation
for variation in "${VARIATIONS[@]}"; do
    IFS=':' read -r name percent desc <<< "$variation"

    output_db="$DATASET_DIR/fraiseql_${name}.db"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Generating: $name ($desc) - $percent% sample"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    python database/database-sampler.py "$XXLARGE_DB" "$output_db" "$percent"

    echo ""
done

# Also copy XXLARGE as-is (100%)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "XXLARGE (100%) already exists"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "========================================================================"
echo "✅ ALL VARIATIONS GENERATED"
echo "========================================================================"
echo ""
echo "Summary of generated databases:"
ls -lh $DATASET_DIR/fraiseql_*.db | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Next steps:"
echo "  1. Validate all databases: python database/validate-all.py"
echo "  2. Import to PostgreSQL: python database/import-all-to-pg.py"
echo "  3. Commit to git-lfs: git add datasets/*.db && git commit -m 'data: add benchmark dataset variations'"
