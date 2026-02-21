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

    -- -----------------------------------------------------------------------
    -- Bulk sync to query side (tv_* tables)
    -- Set-based sync avoids the slow row-by-row fn_sync_tv_* functions.
    -- -----------------------------------------------------------------------

    -- tv_user: embed post count per user
    INSERT INTO benchmark.tv_user (id, identifier, data, updated_at)
    SELECT
        u.id,
        u.identifier,
        jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'fullName',   u.full_name,
            'bio',        u.bio,
            'createdAt',  u.created_at,
            'updatedAt',  u.updated_at,
            'postCount',  COALESCE(pc.post_count, 0)
        ),
        NOW()
    FROM benchmark.tb_user u
    LEFT JOIN (
        SELECT fk_author, COUNT(*) AS post_count
        FROM benchmark.tb_post
        GROUP BY fk_author
    ) pc ON pc.fk_author = u.pk_user
    ON CONFLICT (id) DO UPDATE
        SET identifier  = EXCLUDED.identifier,
            data        = EXCLUDED.data,
            updated_at  = EXCLUDED.updated_at;

    RAISE NOTICE '[05-medium-seed] tv_user synced.';

    -- tv_post: embed author info and comment count
    INSERT INTO benchmark.tv_post (id, identifier, data, updated_at)
    SELECT
        p.id,
        p.identifier,
        jsonb_build_object(
            'id',           p.id::text,
            'identifier',   p.identifier,
            'title',        p.title,
            'content',      p.content,
            'published',    p.published,
            'createdAt',    p.created_at,
            'updatedAt',    p.updated_at,
            'author', jsonb_build_object(
                'id',       u.id::text,
                'username', u.username,
                'fullName', u.full_name
            ),
            'commentCount', COALESCE(cc.comment_count, 0)
        ),
        NOW()
    FROM benchmark.tb_post p
    JOIN benchmark.tb_user u ON u.pk_user = p.fk_author
    LEFT JOIN (
        SELECT fk_post, COUNT(*) AS comment_count
        FROM benchmark.tb_comment
        GROUP BY fk_post
    ) cc ON cc.fk_post = p.pk_post
    ON CONFLICT (id) DO UPDATE
        SET identifier  = EXCLUDED.identifier,
            data        = EXCLUDED.data,
            updated_at  = EXCLUDED.updated_at;

    RAISE NOTICE '[05-medium-seed] tv_post synced.';

    -- tv_comment: embed author and post info
    INSERT INTO benchmark.tv_comment (id, identifier, data, updated_at)
    SELECT
        c.id,
        c.identifier,
        jsonb_build_object(
            'id',         c.id::text,
            'identifier', c.identifier,
            'content',    c.content,
            'createdAt',  c.created_at,
            'updatedAt',  c.updated_at,
            'author', jsonb_build_object(
                'id',       u.id::text,
                'username', u.username,
                'fullName', u.full_name
            ),
            'post', jsonb_build_object(
                'id',    p.id::text,
                'title', p.title
            )
        ),
        NOW()
    FROM benchmark.tb_comment c
    JOIN benchmark.tb_user u ON u.pk_user = c.fk_author
    JOIN benchmark.tb_post  p ON p.pk_post = c.fk_post
    ON CONFLICT (id) DO UPDATE
        SET identifier  = EXCLUDED.identifier,
            data        = EXCLUDED.data,
            updated_at  = EXCLUDED.updated_at;

    RAISE NOTICE '[05-medium-seed] tv_comment synced.';
    RAISE NOTICE '[05-medium-seed] Seeding complete for % dataset.', v_scale;
END $$;
