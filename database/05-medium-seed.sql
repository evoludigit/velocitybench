-- Medium-scale seed data for VelocityBench
-- Generates 10K users / 50K posts / 200K comments when benchmark.data_volume = 'medium'
-- Idempotent: skips if more than 5 users already exist (fixture-only state)
-- Fixtures (alice-eve, pk_user 1-5) are preserved from fraiseql_cqrs_schema.sql

DO $$
DECLARE
    v_scale        TEXT := COALESCE(current_setting('benchmark.data_volume', true), 'xs');
    v_user_count   INT;
    v_post_count   INT;
    v_comment_count INT;
    v_existing     INT;
BEGIN
    -- Idempotency: skip if bulk data already loaded
    SELECT COUNT(*) INTO v_existing FROM benchmark.tb_user;
    IF v_existing > 5 THEN
        RAISE NOTICE '[05-medium-seed] Already seeded (% users). Skipping.', v_existing;
        RETURN;
    END IF;

    IF v_scale = 'medium' THEN
        v_user_count    := 10000;
        v_post_count    := 50000;
        v_comment_count := 200000;
    ELSIF v_scale = 'large' THEN
        v_user_count    := 100000;
        v_post_count    := 500000;
        v_comment_count := 2000000;
    ELSE
        -- 'xs' or anything else: fixtures (1-5) are already present, add small bulk
        v_user_count    := 100;
        v_post_count    := 500;
        v_comment_count := 2000;
    END IF;

    RAISE NOTICE '[05-medium-seed] Seeding % dataset: % users, % posts, % comments',
        v_scale, v_user_count, v_post_count, v_comment_count;

    -- Disable pg_tviews triggers during bulk insert to avoid per-row overhead.
    -- pg_tviews_refresh() is called after all inserts complete for a single-pass sync.
    ALTER TABLE benchmark.tb_user    DISABLE TRIGGER ALL;
    ALTER TABLE benchmark.tb_post    DISABLE TRIGGER ALL;
    ALTER TABLE benchmark.tb_comment DISABLE TRIGGER ALL;

    -- -----------------------------------------------------------------------
    -- Users (6 → v_user_count, fixtures 1-5 already inserted)
    -- -----------------------------------------------------------------------
    INSERT INTO benchmark.tb_user (identifier, email, username, full_name, bio)
    SELECT
        'user-' || i,
        'user' || i || '@bench.test',
        'user_' || i,
        'Benchmark User ' || i,
        CASE WHEN (i % 3) = 0 THEN NULL
             ELSE 'Auto-generated user for benchmarking. Index: ' || i
        END
    FROM generate_series(6, v_user_count) AS i;

    RAISE NOTICE '[05-medium-seed] Users inserted.';

    -- -----------------------------------------------------------------------
    -- Posts (fixtures 1-5 already inserted)
    -- The post titles cycle through 10 realistic tech topics.
    -- Author distribution: power-law — first 10% of users own ~50% of posts.
    -- -----------------------------------------------------------------------
    INSERT INTO benchmark.tb_post (identifier, title, content, fk_author, published, created_at)
    SELECT
        'post-' || i,
        (ARRAY[
            'GraphQL Performance Deep Dive',
            'REST vs GraphQL: A Practical Comparison',
            'Async Patterns in Modern Web APIs',
            'Database Optimization with PostgreSQL',
            'Connection Pooling Strategies',
            'DataLoader and the N+1 Problem',
            'CQRS in Practice: Command vs Query',
            'Benchmarking Web API Frameworks',
            'Rust for High-Performance Backends',
            'Understanding JSONB Indexes'
        ])[(i % 10) + 1] || ' — Part ' || ((i / 10) + 1),
        'This is the content of post ' || i || '. A realistic-length body for benchmarking '
            || 'JSON serialization overhead. GraphQL frameworks must serialize nested objects '
            || 'including author data and comment counts. Post index: ' || i || '. '
            || 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
        -- Power-law: 50% of posts go to top 10% of users
        CASE
            WHEN random() < 0.5
                THEN GREATEST(1, (random() * (v_user_count * 0.1))::INT)
            ELSE GREATEST(1, (random() * v_user_count)::INT)
        END,
        (random() < 0.8),  -- 80% published
        NOW() - (random() * INTERVAL '730 days')
    FROM generate_series(6, v_post_count) AS i;

    RAISE NOTICE '[05-medium-seed] Posts inserted.';

    -- -----------------------------------------------------------------------
    -- Comments (fixtures 1-5 already inserted)
    -- Distribute across all posts and users uniformly.
    -- -----------------------------------------------------------------------
    INSERT INTO benchmark.tb_comment (fk_post, fk_author, content, created_at)
    SELECT
        GREATEST(1, (random() * v_post_count)::INT),
        GREATEST(1, (random() * v_user_count)::INT),
        'Comment ' || i || ': This benchmark comment has realistic length. '
            || 'Great post! The performance characteristics described here are '
            || 'consistent with our production observations.',
        NOW() - (random() * INTERVAL '365 days')
    FROM generate_series(6, v_comment_count) AS i;

    RAISE NOTICE '[05-medium-seed] Comments inserted.';

    -- Re-enable triggers now that bulk data is loaded
    ALTER TABLE benchmark.tb_user    ENABLE TRIGGER ALL;
    ALTER TABLE benchmark.tb_post    ENABLE TRIGGER ALL;
    ALTER TABLE benchmark.tb_comment ENABLE TRIGGER ALL;

    -- -----------------------------------------------------------------------
    -- Refresh TVIEWs via pg_tviews_refresh() (beta.3+ API).
    -- Takes the entity name (e.g. 'user'), not the tview name ('tv_user').
    -- Internally does TRUNCATE + column-explicit INSERT from the backing view,
    -- so created_at/updated_at column mismatch is handled correctly.
    -- -----------------------------------------------------------------------
    PERFORM pg_tviews_refresh('user');
    RAISE NOTICE '[05-medium-seed] tv_user refreshed.';

    PERFORM pg_tviews_refresh('post');
    RAISE NOTICE '[05-medium-seed] tv_post refreshed.';

    PERFORM pg_tviews_refresh('comment');
    RAISE NOTICE '[05-medium-seed] tv_comment refreshed.';

    RAISE NOTICE '[05-medium-seed] Seeding complete for % dataset.', v_scale;
END $$;
