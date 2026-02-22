-- FraiseQL CQRS Schema with TV Tables
-- This implements the core CQRS pattern that gives FraiseQL its performance advantage
-- Command side (tb_*): Normalized writes with Trinity identifiers
-- Query side (tv_*): Denormalized JSONB reads with pre-computed aggregations

-- ============================================================================
-- COMMAND SIDE: Normalized tables for writes (tb_* prefix) with Trinity Pattern
-- ============================================================================

-- Users table (command side) - Trinity Pattern
CREATE TABLE benchmark.tb_user (
    -- Trinity Identifiers
    pk_user INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Internal (fast INT joins)
    id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,     -- Public API (secure UUID)
    identifier TEXT UNIQUE NOT NULL,                       -- Human-readable (username)

    -- User data
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    bio TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tb_user_id ON benchmark.tb_user(id);
CREATE INDEX idx_tb_user_email ON benchmark.tb_user(email);
CREATE INDEX idx_tb_user_username ON benchmark.tb_user(username);
CREATE INDEX idx_tb_user_identifier ON benchmark.tb_user(identifier);

-- Posts table (command side) - Trinity Pattern with INT foreign keys
CREATE TABLE benchmark.tb_post (
    -- Trinity Identifiers
    pk_post INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Internal (fast INT joins)
    id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,     -- Public API (secure UUID)
    identifier TEXT UNIQUE NOT NULL,                       -- Human-readable (slug)

    -- Post data
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    fk_author INT NOT NULL REFERENCES benchmark.tb_user(pk_user) ON DELETE CASCADE,  -- Fast INT FK!
    published BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tb_post_id ON benchmark.tb_post(id);
CREATE INDEX idx_tb_post_identifier ON benchmark.tb_post(identifier);
CREATE INDEX idx_tb_post_fk_author ON benchmark.tb_post(fk_author);  -- Fast INT FK index
CREATE INDEX idx_tb_post_published ON benchmark.tb_post(published);
CREATE INDEX idx_tb_post_created ON benchmark.tb_post(created_at DESC);

-- Comments table (command side) - Trinity Pattern with INT foreign keys
CREATE TABLE benchmark.tb_comment (
    -- Trinity Identifiers
    pk_comment INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Internal (fast INT joins)
    id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,        -- Public API (secure UUID)
    identifier TEXT UNIQUE,                                   -- Optional for comments

    -- Comment data
    fk_post INT NOT NULL REFERENCES benchmark.tb_post(pk_post) ON DELETE CASCADE,    -- Fast INT FK!
    fk_author INT NOT NULL REFERENCES benchmark.tb_user(pk_user) ON DELETE CASCADE,  -- Fast INT FK!
    content TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tb_comment_id ON benchmark.tb_comment(id);
CREATE INDEX idx_tb_comment_fk_post ON benchmark.tb_comment(fk_post);    -- Fast INT FK index
CREATE INDEX idx_tb_comment_fk_author ON benchmark.tb_comment(fk_author);  -- Fast INT FK index
CREATE INDEX idx_tb_comment_created ON benchmark.tb_comment(created_at DESC);

-- ============================================================================
-- QUERY SIDE: Denormalized JSONB tables for reads (tv_* prefix)
-- Managed by pg_tviews — created via pg_tviews_create() after seed data is loaded.
-- pg_tviews installs triggers on tb_* tables so subsequent writes auto-cascade.
-- ============================================================================
-- (tv_* tables are created below, after INSERT of fixture data)

-- (sync functions removed — pg_tviews handles cascade sync via triggers)

-- ============================================================================
-- SEED DATA: Populate with test data and sync to query side
-- ============================================================================

-- Insert test users
INSERT INTO benchmark.tb_user (id, identifier, email, username, full_name, bio) VALUES
('11111111-1111-1111-1111-111111111111', 'alice', 'alice@example.com', 'alice', 'Alice Johnson', 'Software engineer passionate about GraphQL'),
('22222222-2222-2222-2222-222222222222', 'bob', 'bob@example.com', 'bob', 'Bob Smith', 'Database administrator with 10+ years experience'),
('33333333-3333-3333-3333-333333333333', 'carol', 'carol@example.com', 'carol', 'Carol Williams', 'Full-stack developer and tech blogger'),
('44444444-4444-4444-4444-444444444444', 'dave', 'dave@example.com', 'dave', 'Dave Brown', 'DevOps engineer specializing in PostgreSQL'),
('55555555-5555-5555-5555-555555555555', 'eve', 'eve@example.com', 'eve', 'Eve Davis', 'Product manager focused on developer experience');

-- Insert test posts
INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'getting-started-graphql', 'Getting Started with GraphQL', 'GraphQL is a query language for APIs that allows clients to request exactly the data they need...', 1, true),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'database-design-best-practices', 'Database Design Best Practices', 'When designing databases, consider normalization, indexing strategies, and query patterns...', 2, true),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'api-performance-optimization', 'API Performance Optimization', 'Optimizing API performance requires understanding bottlenecks, caching strategies, and efficient data access patterns...', 3, true),
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'modern-web-development', 'Modern Web Development', 'Modern web development has evolved significantly with new frameworks, tools, and best practices...', 4, true),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'data-modeling-techniques', 'Data Modeling Techniques', 'Effective data modeling is crucial for building scalable and maintainable applications...', 5, true);

-- Insert test comments
INSERT INTO benchmark.tb_comment (id, content, fk_post, fk_author) VALUES
('11111111-1111-1111-1111-111111111111', 'Great article! Very helpful for beginners.', 1, 2),
('22222222-2222-2222-2222-222222222222', 'I learned a lot from this. Thanks for sharing!', 1, 3),
('33333333-3333-3333-3333-333333333333', 'Excellent explanation of the concepts.', 2, 1),
('44444444-4444-4444-4444-444444444444', 'This clarified many concepts for me.', 2, 4),
('55555555-5555-5555-5555-555555555555', 'Well written and informative.', 3, 5);

-- ============================================================================
-- QUERY SIDE SETUP: Create TVIEWs via pg_tviews_create()
-- pg_tviews creates backing views (public.v_*) and materialized tables
-- (benchmark.tv_*), populates them from current data, and installs triggers
-- on tb_* tables so future writes auto-cascade.
-- ============================================================================

-- Set search_path: pg_tviews creates materialized tables in the first schema
-- in the path (benchmark), while backing views go to public.v_*
SET search_path TO benchmark, public;

-- tv_user: backed by public.v_user, materialized in benchmark.tv_user
-- Triggers installed on tb_user. CASCADE: user update → tv_user + tv_post + tv_comment
SELECT pg_tviews_create('tv_user', $TVIEW_SQL$
    SELECT
        u.pk_user                              AS pk_user,
        u.id                                   AS id,
        u.identifier                           AS identifier,
        jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'fullName',   u.full_name,
            'bio',        u.bio,
            'createdAt',  to_char(u.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(u.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'postCount',  COALESCE(pc.cnt, 0)
        )                                      AS data
    FROM benchmark.tb_user u
    LEFT JOIN (
        SELECT fk_author, COUNT(*) AS cnt
        FROM benchmark.tb_post
        GROUP BY fk_author
    ) pc ON pc.fk_author = u.pk_user
$TVIEW_SQL$);

-- tv_post: backed by public.v_post, materialized in benchmark.tv_post
-- Triggers on tb_post AND tb_user (cascade: author change → tv_post update)
SELECT pg_tviews_create('tv_post', $TVIEW_SQL$
    SELECT
        p.pk_post                              AS pk_post,
        p.id                                   AS id,
        p.identifier                           AS identifier,
        p.fk_author                            AS fk_author,
        jsonb_build_object(
            'id',           p.id::text,
            'identifier',   p.identifier,
            'title',        p.title,
            'content',      p.content,
            'published',    p.published,
            'createdAt',    to_char(p.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',    to_char(p.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'author',       jsonb_build_object(
                'id',         u.id::text,
                'username',   u.username,
                'fullName',   u.full_name
            ),
            'commentCount', COALESCE(cc.cnt, 0)
        )                                      AS data
    FROM benchmark.tb_post p
    JOIN benchmark.tb_user u ON u.pk_user = p.fk_author
    LEFT JOIN (
        SELECT fk_post, COUNT(*) AS cnt
        FROM benchmark.tb_comment
        GROUP BY fk_post
    ) cc ON cc.fk_post = p.pk_post
$TVIEW_SQL$);

-- tv_comment: backed by public.v_comment, materialized in benchmark.tv_comment
-- Triggers on tb_comment, tb_post, tb_user
SELECT pg_tviews_create('tv_comment', $TVIEW_SQL$
    SELECT
        c.pk_comment                           AS pk_comment,
        c.id                                   AS id,
        c.identifier                           AS identifier,
        c.fk_author                            AS fk_author,
        c.fk_post                              AS fk_post,
        jsonb_build_object(
            'id',         c.id::text,
            'identifier', c.identifier,
            'content',    c.content,
            'createdAt',  to_char(c.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(c.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'author',     jsonb_build_object(
                'id',         u.id::text,
                'username',   u.username,
                'fullName',   u.full_name
            ),
            'post',       jsonb_build_object(
                'id',    p.id::text,
                'title', p.title
            )
        )                                      AS data
    FROM benchmark.tb_comment c
    JOIN benchmark.tb_user u ON u.pk_user = c.fk_author
    JOIN benchmark.tb_post  p ON p.pk_post  = c.fk_post
$TVIEW_SQL$);

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE benchmark.tb_user IS 'Command side: Normalized users with Trinity identifiers (pk_user, id, identifier)';
COMMENT ON TABLE benchmark.tb_post IS 'Command side: Normalized posts with INT foreign keys for fast joins';
COMMENT ON TABLE benchmark.tb_comment IS 'Command side: Normalized comments with INT foreign keys for fast joins';

COMMENT ON TABLE benchmark.tv_user IS 'Query side: TVIEW managed by pg_tviews — denormalized users with JSONB and pre-computed post count';
COMMENT ON TABLE benchmark.tv_post IS 'Query side: TVIEW managed by pg_tviews — denormalized posts with embedded author and comment count';
COMMENT ON TABLE benchmark.tv_comment IS 'Query side: TVIEW managed by pg_tviews — denormalized comments with embedded author and post info';

-- ============================================================================
-- PERFORMANCE ANALYSIS QUERIES
-- ============================================================================

-- Query to compare table sizes
-- SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
-- FROM pg_tables WHERE schemaname = 'benchmark' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Query to analyze JSONB data size
-- SELECT 'tv_user' as table_name, count(*) as rows, pg_size_pretty(sum(pg_column_size(data))) as jsonb_size FROM benchmark.tv_user
-- UNION ALL
-- SELECT 'tv_post' as table_name, count(*) as rows, pg_size_pretty(sum(pg_column_size(data))) as jsonb_size FROM benchmark.tv_post
-- UNION ALL
-- SELECT 'tv_comment' as table_name, count(*) as rows, pg_size_pretty(sum(pg_column_size(data))) as jsonb_size FROM benchmark.tv_comment;