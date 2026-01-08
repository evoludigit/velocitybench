-- Large dataset generation for FraiseQL performance benchmarking
-- This script uses pure SQL for fast bulk data generation
-- Run after schema initialization

SET search_path TO benchmark, public;

-- ============================================================================
-- HELPER FUNCTIONS FOR DATA GENERATION
-- ============================================================================

-- Random text generator for realistic content
CREATE OR REPLACE FUNCTION benchmark.fn_random_text(min_len INT, max_len INT)
RETURNS TEXT AS $$
DECLARE
    words TEXT[] := ARRAY[
        'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur',
        'adipiscing', 'elit', 'sed', 'do', 'eiusmod', 'tempor',
        'incididunt', 'ut', 'labore', 'et', 'dolore', 'magna',
        'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis',
        'nostrud', 'exercitation', 'ullamco', 'laboris', 'nisi',
        'aliquip', 'ex', 'ea', 'commodo', 'consequat', 'duis',
        'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
        'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur',
        'excepteur', 'sint', 'occaecat', 'cupidatat', 'non',
        'proident', 'sunt', 'culpa', 'qui', 'officia', 'deserunt',
        'mollit', 'anim', 'id', 'est', 'laborum'
    ];
    result TEXT := '';
    target_len INT;
    word_count INT := 0;
    max_words INT := max_len / 5; -- Assume average 5 chars per word
BEGIN
    target_len := min_len + floor(random() * (max_len - min_len + 1))::INT;
    WHILE length(result) < target_len AND word_count < max_words LOOP
        result := result || ' ' || words[1 + floor(random() * array_length(words, 1))::INT];
        word_count := word_count + 1;
    END LOOP;
    RETURN trim(result);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DATA GENERATION - LARGE SCALE (10K users, 100K posts, 500K comments)
-- ============================================================================

-- Generate users with varied profile data
INSERT INTO benchmark.tb_user (id, identifier, email, username, full_name, bio)
SELECT
    CASE
        WHEN n <= 100 THEN (lpad(n::TEXT, 8, '0') || '-1111-1111-1111-111111111111')::UUID
        ELSE gen_random_uuid()
    END,
    CASE
        WHEN n <= 100 THEN 'user_' || lpad(n::TEXT, 5, '0')
        ELSE 'user_' || lpad(n::TEXT, 5, '0')
    END,
    'user' || n || '@benchmark.local',
    'user_' || n,
    'User ' || n || ' Full Name',
    CASE WHEN random() > 0.3 THEN benchmark.fn_random_text(50, 500) ELSE NULL END
FROM generate_series(1, 10000) AS n;

ANALYZE benchmark.tb_user;

-- Generate posts with realistic content (10 per user average)
INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published, created_at)
SELECT
    CASE
        WHEN n <= 100 THEN (lpad(n::TEXT, 8, '0') || '-2222-2222-2222-222222222222')::UUID
        ELSE gen_random_uuid()
    END,
    'post_' || lpad(n::TEXT, 6, '0'),
    benchmark.fn_random_text(20, 100),
    benchmark.fn_random_text(200, 5000),
    ((n - 1) % 10000) + 1,  -- Distribute posts across users
    random() > 0.2,  -- 80% published, 20% draft
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 100000) AS n;

ANALYZE benchmark.tb_post;

-- Generate comments (5 per post average)
INSERT INTO benchmark.tb_comment (id, identifier, content, fk_post, fk_author, created_at)
SELECT
    CASE
        WHEN n <= 100 THEN (lpad(n::TEXT, 8, '0') || '-3333-3333-3333-333333333333')::UUID
        ELSE gen_random_uuid()
    END,
    NULL,
    benchmark.fn_random_text(50, 1000),
    ((n - 1) % 100000) + 1,  -- Distribute comments across posts
    ((n - 1) % 10000) + 1,   -- Comments from various users
    NOW() - (random() * INTERVAL '180 days')
FROM generate_series(1, 500000) AS n;

ANALYZE benchmark.tb_comment;

-- Generate user follows (5 per user average)
INSERT INTO benchmark.tb_user_follows (fk_follower, fk_following, created_at)
SELECT
    ((n - 1) % 10000) + 1 as fk_follower,
    ((n - 1 + (n / 10000)::INT + 1) % 10000) + 1 as fk_following,
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 50000) AS n
WHERE ((n - 1) % 10000) + 1 != ((n - 1 + (n / 10000)::INT + 1) % 10000) + 1
LIMIT 50000;

ANALYZE benchmark.tb_user_follows;

-- Generate post likes (2 per post average)
INSERT INTO benchmark.tb_post_like (fk_user, fk_post, reaction_type, created_at)
SELECT
    ((n - 1) % 10000) + 1 as fk_user,
    ((n - 1) % 100000) + 1 as fk_post,
    (ARRAY['like', 'like', 'like', 'love', 'laugh', 'angry'])[1 + floor(random() * 6)::INT],
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 200000) AS n
ON CONFLICT DO NOTHING;

ANALYZE benchmark.tb_post_like;

-- ============================================================================
-- SYNC TO QUERY SIDE (tv_* TABLES)
-- ============================================================================

-- Sync all users to tv_user
DO $$
DECLARE
    batch_size INT := 1000;
    total_count INT;
    processed INT := 0;
BEGIN
    SELECT COUNT(*) INTO total_count FROM benchmark.tb_user;
    RAISE NOTICE 'Syncing % users to tv_user...', total_count;

    FOR user_rec IN SELECT id FROM benchmark.tb_user LOOP
        PERFORM benchmark.fn_sync_tv_user(user_rec.id);
        processed := processed + 1;
        IF processed % batch_size = 0 THEN
            RAISE NOTICE '  Synced %/%', processed, total_count;
            COMMIT;
        END IF;
    END LOOP;
    RAISE NOTICE '  All % users synced', total_count;
END $$;

-- Sync all posts to tv_post
DO $$
DECLARE
    batch_size INT := 1000;
    total_count INT;
    processed INT := 0;
BEGIN
    SELECT COUNT(*) INTO total_count FROM benchmark.tb_post;
    RAISE NOTICE 'Syncing % posts to tv_post...', total_count;

    FOR post_rec IN SELECT id FROM benchmark.tb_post LOOP
        PERFORM benchmark.fn_sync_tv_post(post_rec.id);
        processed := processed + 1;
        IF processed % batch_size = 0 THEN
            RAISE NOTICE '  Synced %/%', processed, total_count;
            COMMIT;
        END IF;
    END LOOP;
    RAISE NOTICE '  All % posts synced', total_count;
END $$;

-- Sync all comments to tv_comment
DO $$
DECLARE
    batch_size INT := 1000;
    total_count INT;
    processed INT := 0;
BEGIN
    SELECT COUNT(*) INTO total_count FROM benchmark.tb_comment;
    RAISE NOTICE 'Syncing % comments to tv_comment...', total_count;

    FOR comment_rec IN SELECT id FROM benchmark.tb_comment LOOP
        PERFORM benchmark.fn_sync_tv_comment(comment_rec.id);
        processed := processed + 1;
        IF processed % batch_size = 0 THEN
            RAISE NOTICE '  Synced %/%', processed, total_count;
            COMMIT;
        END IF;
    END LOOP;
    RAISE NOTICE '  All % comments synced', total_count;
END $$;

-- Final analysis for query planner
ANALYZE;

RAISE NOTICE 'Large dataset generation complete!';
