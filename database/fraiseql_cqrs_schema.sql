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
-- ============================================================================

-- Users view (query side) - denormalized with post count
CREATE TABLE benchmark.tv_user (
    id UUID PRIMARY KEY,  -- UUID for GraphQL API
    identifier TEXT UNIQUE NOT NULL,  -- Human-readable identifier
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Posts view (query side) - denormalized with author and comments
CREATE TABLE benchmark.tv_post (
    id UUID PRIMARY KEY,  -- UUID for GraphQL API
    identifier TEXT UNIQUE NOT NULL,  -- Human-readable slug
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comments view (query side) - denormalized with author info
CREATE TABLE benchmark.tv_comment (
    id UUID PRIMARY KEY,  -- UUID for GraphQL API
    identifier TEXT UNIQUE,  -- Optional for comments
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GIN indexes for fast JSONB queries
CREATE INDEX idx_tv_user_data ON benchmark.tv_user USING GIN(data);
CREATE INDEX idx_tv_user_identifier ON benchmark.tv_user(identifier);

CREATE INDEX idx_tv_post_data ON benchmark.tv_post USING GIN(data);
CREATE INDEX idx_tv_post_identifier ON benchmark.tv_post(identifier);

CREATE INDEX idx_tv_comment_data ON benchmark.tv_comment USING GIN(data);

-- ============================================================================
-- SYNC FUNCTIONS: Explicit sync from command (tb_*) to query (tv_*) side
-- ============================================================================

-- Sync function for user: tb_user → tv_user
CREATE OR REPLACE FUNCTION benchmark.fn_sync_tv_user(p_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO benchmark.tv_user (id, identifier, data, updated_at)
    SELECT
        u.id,
        u.identifier,
        jsonb_build_object(
            'id', u.id::text,
            'identifier', u.identifier,
            'email', u.email,
            'username', u.username,
            'fullName', u.full_name,  -- camelCase for GraphQL
            'bio', u.bio,
            'createdAt', u.created_at,  -- camelCase for GraphQL
            'updatedAt', u.updated_at,  -- camelCase for GraphQL
            'postCount', COALESCE(
                (SELECT COUNT(*) FROM benchmark.tb_post WHERE fk_author = u.pk_user),
                0
            )
        ),
        NOW()
    FROM benchmark.tb_user u
    WHERE u.id = p_id
    ON CONFLICT (id) DO UPDATE
    SET
        identifier = EXCLUDED.identifier,
        data = EXCLUDED.data,
        updated_at = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Sync function for post: tb_post → tv_post
CREATE OR REPLACE FUNCTION benchmark.fn_sync_tv_post(p_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO benchmark.tv_post (id, identifier, data, updated_at)
    SELECT
        p.id,
        p.identifier,
        jsonb_build_object(
            'id', p.id::text,
            'identifier', p.identifier,
            'title', p.title,
            'content', p.content,
            'published', p.published,
            'createdAt', p.created_at,
            'updatedAt', p.updated_at,
            'author', jsonb_build_object(
                'id', u.id::text,
                'username', u.username,
                'fullName', u.full_name
            ),
            'commentCount', COALESCE(
                (SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post = p.pk_post),
                0
            )
        ),
        NOW()
    FROM benchmark.tb_post p
    JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
    WHERE p.id = p_id
    ON CONFLICT (id) DO UPDATE
    SET
        identifier = EXCLUDED.identifier,
        data = EXCLUDED.data,
        updated_at = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Sync function for comment: tb_comment → tv_comment
CREATE OR REPLACE FUNCTION benchmark.fn_sync_tv_comment(p_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO benchmark.tv_comment (id, identifier, data, updated_at)
    SELECT
        c.id,
        c.identifier,
        jsonb_build_object(
            'id', c.id::text,
            'identifier', c.identifier,
            'content', c.content,
            'createdAt', c.created_at,
            'updatedAt', c.updated_at,
            'author', jsonb_build_object(
                'id', u.id::text,
                'username', u.username,
                'fullName', u.full_name
            ),
            'post', jsonb_build_object(
                'id', p.id::text,
                'title', p.title
            )
        ),
        NOW()
    FROM benchmark.tb_comment c
    JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
    JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
    WHERE c.id = p_id
    ON CONFLICT (id) DO UPDATE
    SET
        identifier = EXCLUDED.identifier,
        data = EXCLUDED.data,
        updated_at = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

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

-- Sync all data to query side (tv_* tables)
SELECT benchmark.fn_sync_tv_user(id) FROM benchmark.tb_user;
SELECT benchmark.fn_sync_tv_post(id) FROM benchmark.tb_post;
SELECT benchmark.fn_sync_tv_comment(id) FROM benchmark.tb_comment;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE benchmark.tb_user IS 'Command side: Normalized users with Trinity identifiers (pk_user, id, identifier)';
COMMENT ON TABLE benchmark.tb_post IS 'Command side: Normalized posts with INT foreign keys for fast joins';
COMMENT ON TABLE benchmark.tb_comment IS 'Command side: Normalized comments with INT foreign keys for fast joins';

COMMENT ON TABLE benchmark.tv_user IS 'Query side: Denormalized users with JSONB data and pre-computed aggregations';
COMMENT ON TABLE benchmark.tv_post IS 'Query side: Denormalized posts with embedded author and comment count';
COMMENT ON TABLE benchmark.tv_comment IS 'Query side: Denormalized comments with embedded author and post info';

COMMENT ON FUNCTION benchmark.fn_sync_tv_user IS 'Explicit sync: tb_user → tv_user (call after INSERT/UPDATE/DELETE on tb_user)';
COMMENT ON FUNCTION benchmark.fn_sync_tv_post IS 'Explicit sync: tb_post → tv_post (call after INSERT/UPDATE/DELETE on tb_post)';
COMMENT ON FUNCTION benchmark.fn_sync_tv_comment IS 'Explicit sync: tb_comment → tv_comment (call after INSERT/UPDATE/DELETE on tb_comment)';

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