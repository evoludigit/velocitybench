#!/bin/bash
# Generate JMeter parameterized test datasets from populated database
# Run after seeding large dataset

set -e

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fraiseql_benchmark}"
DB_USER="${DB_USER:-benchmark}"
DB_PASSWORD="${DB_PASSWORD:-benchmark123}"

DB_CONN="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Generating JMeter datasets from database..."
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "Output directory: $SCRIPT_DIR"
echo ""

# Create output directory if it doesn't exist
mkdir -p "$SCRIPT_DIR"

# Function to run query and save to CSV
generate_dataset() {
    local query="$1"
    local output_file="$2"
    local label="$3"

    echo "Generating: $label"
    echo "  Query: $query"
    echo "  Output: $output_file"

    psql "$DB_CONN" \
        -t -A \
        -c "$query" \
        > "$output_file"

    local count=$(wc -l < "$output_file")
    echo "  Generated $count records"
    echo ""
}

# 1. User IDs for parameterized queries (1000 random users)
generate_dataset \
    "SELECT id::TEXT FROM benchmark.tb_user ORDER BY random() LIMIT 1000" \
    "$SCRIPT_DIR/user_ids.csv" \
    "User IDs (1000 random users)"

# 2. Post IDs for parameterized queries (1000 random published posts)
generate_dataset \
    "SELECT id::TEXT FROM benchmark.tb_post WHERE published = true ORDER BY random() LIMIT 1000" \
    "$SCRIPT_DIR/post_ids.csv" \
    "Post IDs (1000 random published posts)"

# 3. Comment IDs for parameterized queries (500 random comments)
generate_dataset \
    "SELECT id::TEXT FROM benchmark.tb_comment ORDER BY random() LIMIT 500" \
    "$SCRIPT_DIR/comment_ids.csv" \
    "Comment IDs (500 random comments)"

# 4. Active users - users with many posts (for relationship queries)
generate_dataset \
    "SELECT u.id::TEXT FROM benchmark.tb_user u WHERE (SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = u.pk_user) > 5 ORDER BY random() LIMIT 200" \
    "$SCRIPT_DIR/active_users.csv" \
    "Active users (200 users with 5+ posts)"

# 5. Popular posts - posts with many comments (for deep traversal)
generate_dataset \
    "SELECT p.id::TEXT FROM benchmark.tb_post p WHERE (SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = p.pk_post) > 10 ORDER BY random() LIMIT 200" \
    "$SCRIPT_DIR/popular_posts.csv" \
    "Popular posts (200 posts with 10+ comments)"

# 6. Commented posts - posts that have comments
generate_dataset \
    "SELECT DISTINCT p.id::TEXT FROM benchmark.tb_post p JOIN benchmark.tb_comment c ON p.pk_post = c.fk_post ORDER BY random() LIMIT 500" \
    "$SCRIPT_DIR/commented_posts.csv" \
    "Commented posts (500 posts with comments)"

# 7. Users with followers - for social graph queries
generate_dataset \
    "SELECT DISTINCT u.id::TEXT FROM benchmark.tb_user u WHERE EXISTS (SELECT 1 FROM benchmark.tb_user_follows WHERE fk_following = u.pk_user) ORDER BY random() LIMIT 200" \
    "$SCRIPT_DIR/followed_users.csv" \
    "Followed users (200 users with followers)"

# 8. Liked posts - posts that have likes
generate_dataset \
    "SELECT DISTINCT p.id::TEXT FROM benchmark.tb_post p WHERE EXISTS (SELECT 1 FROM benchmark.tb_post_like WHERE fk_post = p.pk_post) ORDER BY random() LIMIT 500" \
    "$SCRIPT_DIR/liked_posts.csv" \
    "Liked posts (500 posts with likes)"

# 9. Dataset distribution stats
echo "Generating dataset statistics..."
psql "$DB_CONN" \
    -t -A \
    -c "
    SELECT 'users' as entity, COUNT(*) as count FROM benchmark.tb_user
    UNION ALL
    SELECT 'posts', COUNT(*) FROM benchmark.tb_post
    UNION ALL
    SELECT 'comments', COUNT(*) FROM benchmark.tb_comment
    UNION ALL
    SELECT 'follows', COUNT(*) FROM benchmark.tb_user_follows
    UNION ALL
    SELECT 'likes', COUNT(*) FROM benchmark.tb_post_like
    " > "$SCRIPT_DIR/dataset_stats.csv"

echo "Dataset statistics:"
column -t -s '|' "$SCRIPT_DIR/dataset_stats.csv"
echo ""

echo "All datasets generated successfully!"
echo ""
echo "Files created:"
ls -lh "$SCRIPT_DIR"/*.csv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
