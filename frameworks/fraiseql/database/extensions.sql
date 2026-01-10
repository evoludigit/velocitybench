-- FraiseQL Framework Extensions
-- FraiseQL-specific views and functions for denormalized JSONB composition
-- Applied ONLY to the fraiseql_test database
-- The Trinity Pattern tables are already created by schema-template.sql
--
-- Architecture: Three-layer view system
-- 1. tb_* (write layer): Tables with Trinity Pattern
-- 2. v_* (projection layer): Read-only scalar extraction from tb_*
-- 3. tv_* (composition layer): JSONB denormalized objects for FraiseQL

SET search_path TO benchmark, public;

-- ============================================================================
-- LAYER 2: PROJECTION VIEWS (v_*)
-- ============================================================================
-- Read-only views that extract scalar fields from write tables
-- These views maintain pk_* and fk_* for efficient joining

-- v_user: Scalar projection of tb_user
CREATE OR REPLACE VIEW v_user AS
SELECT
    u.pk_user,
    u.id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.bio,
    u.avatar_url,
    u.is_active,
    u.created_at,
    u.updated_at
FROM benchmark.tb_user u;

COMMENT ON VIEW v_user IS 'Projection view: scalar extraction from tb_user for FraiseQL composition';

-- v_post: Scalar projection of tb_post (includes fk_author for joining)
CREATE OR REPLACE VIEW v_post AS
SELECT
    p.pk_post,
    p.id,
    p.fk_author,
    p.title,
    p.content,
    p.excerpt,
    p.status,
    p.published_at,
    p.created_at,
    p.updated_at
FROM benchmark.tb_post p;

COMMENT ON VIEW v_post IS 'Projection view: scalar extraction from tb_post, includes fk_author for joining';

-- v_comment: Scalar projection of tb_comment (includes FKs for joining)
CREATE OR REPLACE VIEW v_comment AS
SELECT
    c.pk_comment,
    c.id,
    c.fk_post,
    c.fk_author,
    c.fk_parent,
    c.content,
    c.is_approved,
    c.created_at,
    c.updated_at
FROM benchmark.tb_comment c;

COMMENT ON VIEW v_comment IS 'Projection view: scalar extraction from tb_comment, includes FKs for joining';

-- ============================================================================
-- LAYER 3: JSONB COMPOSITION VIEWS (tv_*)
-- ============================================================================
-- These views build denormalized JSONB objects with recursive composition
-- FraiseQL uses these for efficient GraphQL queries with zero N+1 problems

-- tv_user: JSONB composition of user with CamelCase fields
CREATE OR REPLACE VIEW tv_user AS
SELECT
    u.id,
    jsonb_build_object(
        'id', u.id,
        'username', u.username,
        'email', u.email,
        'firstName', u.first_name,
        'lastName', u.last_name,
        'bio', u.bio,
        'avatarUrl', u.avatar_url,
        'isActive', u.is_active,
        'createdAt', u.created_at,
        'updatedAt', u.updated_at
    ) as data
FROM v_user u;

COMMENT ON VIEW tv_user IS 'User JSONB composition: denormalized object for FraiseQL GraphQL queries';

-- tv_post: JSONB composition of post with nested author object
CREATE OR REPLACE VIEW tv_post AS
SELECT
    p.id,
    p.fk_author,
    jsonb_build_object(
        'id', p.id,
        'title', p.title,
        'content', p.content,
        'excerpt', p.excerpt,
        'status', p.status,
        'publishedAt', p.published_at,
        'createdAt', p.created_at,
        'updatedAt', p.updated_at,
        'author', COALESCE(
            (SELECT u.data FROM tv_user u WHERE u.id = (
                SELECT id FROM v_user WHERE pk_user = p.fk_author
            )),
            jsonb_null()
        )
    ) as data
FROM v_post p;

COMMENT ON VIEW tv_post IS 'Post JSONB composition: includes denormalized author object via nested tv_user';

-- tv_comment: JSONB composition of comment with nested author, post, and parent
CREATE OR REPLACE VIEW tv_comment AS
SELECT
    c.id,
    c.fk_post,
    c.fk_author,
    c.fk_parent,
    jsonb_build_object(
        'id', c.id,
        'content', c.content,
        'isApproved', c.is_approved,
        'createdAt', c.created_at,
        'updatedAt', c.updated_at,
        'author', COALESCE(
            (SELECT u.data FROM tv_user u WHERE u.id = (
                SELECT id FROM v_user WHERE pk_user = c.fk_author
            )),
            jsonb_null()
        ),
        'post', COALESCE(
            (SELECT p.data FROM tv_post p WHERE p.id = (
                SELECT id FROM v_post WHERE pk_post = c.fk_post
            )),
            jsonb_null()
        ),
        'parentComment', CASE
            WHEN c.fk_parent IS NOT NULL THEN COALESCE(
                (SELECT tc.data FROM tv_comment tc WHERE tc.id = (
                    SELECT id FROM v_comment WHERE pk_comment = c.fk_parent
                )),
                jsonb_null()
            )
            ELSE null::jsonb
        END
    ) as data
FROM v_comment c;

COMMENT ON VIEW tv_comment IS 'Comment JSONB composition: includes denormalized author, post, and parentComment objects';

-- ============================================================================
-- SYNC FUNCTIONS
-- ============================================================================
-- FraiseQL uses sync functions to maintain denormalized CQRS read models
-- These are optional but improve performance for write-heavy scenarios

-- fn_sync_tv_user: Sync user to denormalized read model (if using separate CQRS table)
-- This is a placeholder - actual implementation depends on FraiseQL configuration
CREATE OR REPLACE FUNCTION fn_sync_tv_user(p_user_id UUID)
RETURNS void AS $$
BEGIN
    -- In a full CQRS setup, this would INSERT/UPDATE a denormalized read table
    -- For now, views handle the composition dynamically
    -- Performance note: Views are sufficient if queries are well-indexed
END;
$$ LANGUAGE plpgsql;

-- fn_sync_tv_post: Sync post to denormalized read model
CREATE OR REPLACE FUNCTION fn_sync_tv_post(p_post_id UUID)
RETURNS void AS $$
BEGIN
    -- In a full CQRS setup, this would INSERT/UPDATE a denormalized read table
    -- For now, views handle the composition dynamically
END;
$$ LANGUAGE plpgsql;

-- fn_sync_tv_comment: Sync comment to denormalized read model
CREATE OR REPLACE FUNCTION fn_sync_tv_comment(p_comment_id UUID)
RETURNS void AS $$
BEGIN
    -- In a full CQRS setup, this would INSERT/UPDATE a denormalized read table
    -- For now, views handle the composition dynamically
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- OPTIMIZATION NOTES
-- ============================================================================
--
-- 1. INDEX STRATEGY FOR tv_* VIEWS
--    Since tv_* views use subqueries, ensure these indexes exist:
--    - CREATE INDEX IF NOT EXISTS idx_tv_user_id ON v_user(id);
--    - CREATE INDEX IF NOT EXISTS idx_tv_post_id ON v_post(id);
--    - CREATE INDEX IF NOT EXISTS idx_tv_comment_id ON v_comment(id);
--    These are already created in schema-template.sql
--
-- 2. RECURSIVE COMPOSITION
--    tv_post includes nested tv_user object
--    tv_comment includes nested tv_user, tv_post, and tv_comment (parent)
--    This denormalization reduces FraiseQL query complexity
--
-- 3. CamelCase FIELD NAMES
--    JSONB keys use camelCase (JavaScript/GraphQL convention)
--    Database columns use snake_case (PostgreSQL convention)
--    Conversion happens in the view definition via jsonb_build_object
--
-- 4. PERFORMANCE CHARACTERISTICS
--    - Views are computed on every query (no materialization)
--    - Suitable for read-heavy workloads with low update frequency
--    - Alternative: Materialized views with periodic refresh for very heavy reads
--    - Alternative: CQRS with separate read model tables and sync triggers
--
-- 5. NULL HANDLING
--    Uses COALESCE(..., jsonb_null()) for consistent NULL representation in JSONB
--
-- ============================================================================

-- ============================================================================
-- FUTURE: MATERIALIZED VIEWS (if performance testing shows need)
-- ============================================================================
--
-- For extremely heavy read workloads, consider materializing denormalized views:
--
-- CREATE MATERIALIZED VIEW mv_user AS SELECT * FROM tv_user;
-- CREATE UNIQUE INDEX idx_mv_user_id ON mv_user(id);
--
-- CREATE MATERIALIZED VIEW mv_post AS SELECT * FROM tv_post;
-- CREATE UNIQUE INDEX idx_mv_post_id ON mv_post(id);
--
-- CREATE MATERIALIZED VIEW mv_comment AS SELECT * FROM tv_comment;
-- CREATE UNIQUE INDEX idx_mv_comment_id ON mv_comment(id);
--
-- Then refresh periodically:
-- CREATE OR REPLACE FUNCTION refresh_materialized_views() RETURNS void AS $$
-- BEGIN
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user;
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_post;
--     REFRESH MATERIALIZED VIEW CONCURRENTLY mv_comment;
-- EXCEPTION
--     WHEN OTHERS THEN
--         REFRESH MATERIALIZED VIEW mv_user;
--         REFRESH MATERIALIZED VIEW mv_post;
--         REFRESH MATERIALIZED VIEW mv_comment;
-- END;
-- $$ LANGUAGE plpgsql;
--
-- ============================================================================
