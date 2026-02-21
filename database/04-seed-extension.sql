-- Seed Data Extension: Data Volume Scaling
-- This script extends the small CQRS seed data to test large datasets
-- Can be loaded manually: psql -U benchmark -d fraiseql_benchmark -f database/04-seed-extension.sql

SET search_path TO benchmark, public;

-- ============================================================================
-- GENERATE ADDITIONAL USERS (beyond initial 5)
-- ============================================================================

INSERT INTO benchmark.tb_user (id, identifier, email, username, full_name, bio)
SELECT
    gen_random_uuid(),
    'user_' || lpad(i::TEXT, 5, '0'),
    'user' || i || '@benchmark.local',
    'user_' || i,
    'User ' || i || ' Full Name',
    CASE WHEN random() > 0.3 THEN 'Bio for user ' || i ELSE NULL END
FROM generate_series(6, 100) AS i;

-- ============================================================================
-- GENERATE ADDITIONAL POSTS
-- ============================================================================

INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published, created_at)
SELECT
    gen_random_uuid(),
    'post_' || lpad(i::TEXT, 6, '0'),
    'Post Title ' || i,
    'This is the content of post ' || i || '. Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' ||
    'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
    (i % 100) + 1,  -- Distribute across users 1-100
    CASE WHEN random() > 0.2 THEN true ELSE false END,  -- 80% published
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(6, 100) AS i;

-- ============================================================================
-- GENERATE ADDITIONAL COMMENTS
-- ============================================================================

INSERT INTO benchmark.tb_comment (id, identifier, content, fk_post, fk_author, created_at)
SELECT
    gen_random_uuid(),
    NULL,
    'Comment ' || i || ': ' || 'This is a comment with substantive content discussing the post. Great article! Very informative.',
    (i % (SELECT COUNT(*) FROM benchmark.tb_post)) + 1,  -- Distribute across all posts
    (i % 100) + 1,  -- Distribute across users
    NOW() - (random() * INTERVAL '180 days')
FROM generate_series(6, 50) AS i;

-- ============================================================================
-- SYNC TO QUERY SIDE
-- ============================================================================

-- Sync new users to tv_user
DO $$
DECLARE
    user_rec RECORD;
BEGIN
    FOR user_rec IN SELECT id FROM benchmark.tb_user WHERE NOT EXISTS (SELECT 1 FROM benchmark.tv_user WHERE tv_user.id = tb_user.id)
    LOOP
        PERFORM benchmark.fn_sync_tv_user(user_rec.id);
    END LOOP;
END $$;

-- Sync new posts to tv_post
DO $$
DECLARE
    post_rec RECORD;
BEGIN
    FOR post_rec IN SELECT id FROM benchmark.tb_post WHERE NOT EXISTS (SELECT 1 FROM benchmark.tv_post WHERE tv_post.id = tb_post.id)
    LOOP
        PERFORM benchmark.fn_sync_tv_post(post_rec.id);
    END LOOP;
END $$;

-- Sync new comments to tv_comment
DO $$
DECLARE
    comment_rec RECORD;
BEGIN
    FOR comment_rec IN SELECT id FROM benchmark.tb_comment WHERE NOT EXISTS (SELECT 1 FROM benchmark.tv_comment WHERE tv_comment.id = tb_comment.id)
    LOOP
        PERFORM benchmark.fn_sync_tv_comment(comment_rec.id);
    END LOOP;
END $$;

-- Analyze tables
ANALYZE benchmark.tb_user;
ANALYZE benchmark.tb_post;
ANALYZE benchmark.tb_comment;
ANALYZE benchmark.tv_user;
ANALYZE benchmark.tv_post;
ANALYZE benchmark.tv_comment;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Data generation complete. Summary:' as status;
SELECT
    'tb_user' as table_name,
    COUNT(*) as record_count,
    pg_size_pretty(pg_total_relation_size('benchmark.tb_user')) as size
FROM benchmark.tb_user
UNION ALL
SELECT
    'tb_post',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('benchmark.tb_post'))
FROM benchmark.tb_post
UNION ALL
SELECT
    'tb_comment',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('benchmark.tb_comment'))
FROM benchmark.tb_comment
UNION ALL
SELECT
    'tv_user',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('benchmark.tv_user'))
FROM benchmark.tv_user
UNION ALL
SELECT
    'tv_post',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('benchmark.tv_post'))
FROM benchmark.tv_post
UNION ALL
SELECT
    'tv_comment',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('benchmark.tv_comment'))
FROM benchmark.tv_comment
ORDER BY table_name;
