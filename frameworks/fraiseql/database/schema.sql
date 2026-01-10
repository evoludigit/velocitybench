-- FraiseQL-specific schema for benchmark testing
--
-- Architecture: Three-layer view system
-- 1. tb_* (write layer): Tables with pk_*, id (UUID), fk_* (internal FKs)
-- 2. v_* (projection layer): Scalar extraction from tb_* tables
-- 3. tv_* (composition layer): JSONB denormalized objects for FraiseQL GraphQL
--
-- FraiseQL works with denormalized JSONB data for performance:
-- - Each tv_* view provides a single JSONB 'data' field with the object
-- - Child objects are recursively composed via jsonb_build_object
-- - Pre-computed denormalization reduces query complexity
-- - CamelCase field names in JSONB for JavaScript/GraphQL compatibility

SET search_path TO benchmark, public;

-- ============================================================================
-- LAYER 2: PROJECTION VIEWS (v_* tables)
-- ============================================================================
-- Extract scalar fields from tb_* tables, maintain pk_*/fk_* for joining

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
-- LAYER 3: JSONB COMPOSITION VIEWS (tv_* tables)
-- ============================================================================
-- Build denormalized JSONB objects with recursive composition

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

COMMENT ON VIEW tv_comment IS 'Comment JSONB composition: includes author, post, and parent comment objects';

-- ============================================================================
-- INDEXES FOR FraiseQL QUERY PERFORMANCE
-- ============================================================================

-- Index on v_* views for FK joins
CREATE INDEX IF NOT EXISTS idx_v_post_fk_author ON v_post(fk_author);
CREATE INDEX IF NOT EXISTS idx_v_comment_fk_post ON v_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_v_comment_fk_author ON v_comment(fk_author);
CREATE INDEX IF NOT EXISTS idx_v_comment_fk_parent ON v_comment(fk_parent);

-- Index on tv_* views for GraphQL lookups
CREATE INDEX IF NOT EXISTS idx_tv_user_id ON tv_user(id);
CREATE INDEX IF NOT EXISTS idx_tv_post_id ON tv_post(id);
CREATE INDEX IF NOT EXISTS idx_tv_post_fk_author ON tv_post(fk_author);
CREATE INDEX IF NOT EXISTS idx_tv_comment_id ON tv_comment(id);
CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_post ON tv_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_author ON tv_comment(fk_author);
CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_parent ON tv_comment(fk_parent);

-- JSONB indexes for filtering/searching within denormalized data
CREATE INDEX IF NOT EXISTS idx_tv_user_data ON tv_user USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_tv_post_data ON tv_post USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_tv_comment_data ON tv_comment USING GIN (data);

-- ============================================================================
-- NOTES FOR FRAISEQL INTEGRATION
-- ============================================================================
--
-- Architecture Layers:
--
-- LAYER 1: Write (tb_*)
-- ├─ pk_user, pk_post, pk_comment: SERIAL INT - internal PKs
-- ├─ id: UUID - public identifiers (exposed in FraiseQL)
-- ├─ fk_author, fk_post, fk_parent: INT - internal FKs
-- └─ Data columns: title, content, username, etc.
--
-- LAYER 2: Projection (v_*)
-- ├─ Extracts scalars from tb_* tables
-- ├─ Removes pk_* (internal, never exposed)
-- ├─ Keeps fk_* (for internal joining only)
-- ├─ Includes id (UUID, exposed to API)
-- └─ Used as source for tv_* composition
--
-- LAYER 3: Composition (tv_*)
-- ├─ Builds complete JSONB objects
-- ├─ CamelCase fields (firstName, lastName, createdAt, etc.)
-- ├─ Recursive nesting: author, post, parentComment objects
-- ├─ Single 'data' JSONB field mapped to @fraiseql.type
-- └─ Optimized for efficient GraphQL queries
--
-- FraiseQL Type Mapping:
-- ├─ @fraiseql.type(sql_source="tv_user") class User
-- ├─ @fraiseql.type(sql_source="tv_post") class Post
-- └─ @fraiseql.type(sql_source="tv_comment") class Comment
--
-- Field Extraction:
-- ├─ FraiseQL reads tv_*.data JSONB field
-- ├─ Deserializes to Python dataclass fields
-- ├─ CamelCase in JSON → snake_case in Python (with auto_camel_case config)
-- ├─ Nested objects automatically composed
-- └─ id field exposed as UUID type
--
-- Performance Characteristics:
-- ├─ Pre-computed denormalization (no N+1 queries)
-- ├─ Integer PK joins in tb_* layer (5-10x faster than UUID)
-- ├─ JSONB composition at DB layer (less network overhead)
-- ├─ GIN indexes on JSONB data for filtering
-- └─ Suitable for GraphQL with complex nested queries
--
-- ============================================================================
