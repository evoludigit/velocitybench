-- FraiseQL Framework Database Extensions
--
-- Applies FraiseQL-specific JSONB views for compiled query execution
-- These views implement the FraiseQL pattern: id + data (JSONB) + denormalized filters

SET search_path TO benchmark, public;

-- ============================================================================
-- View: v_user
-- Maps tb_user table to FraiseQL JSONB structure
-- ============================================================================

CREATE OR REPLACE VIEW v_user AS
SELECT
    u.id,
    jsonb_build_object(
        'id', u.id::text,
        'email', u.email,
        'username', u.username,
        'firstName', u.first_name,
        'lastName', u.last_name,
        'bio', u.bio,
        'avatarUrl', u.avatar_url,
        'isActive', u.is_active,
        'createdAt', u.created_at,
        'updatedAt', u.updated_at
    ) AS data,
    u.pk_user AS user_pk
FROM tb_user u;

-- Index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_v_user_data_gin ON v_user USING GIN(data);

-- ============================================================================
-- View: v_post
-- Maps tb_post with nested author data
-- FraiseQL pattern: pre-compute nested relationships in JSONB at read time
-- ============================================================================

CREATE OR REPLACE VIEW v_post AS
SELECT
    p.id,
    jsonb_build_object(
        'id', p.id::text,
        'title', p.title,
        'content', p.content,
        'excerpt', p.excerpt,
        'status', p.status,
        'publishedAt', p.published_at,
        'createdAt', p.created_at,
        'updatedAt', p.updated_at,
        'author', (
            SELECT jsonb_build_object(
                'id', u.id::text,
                'username', u.username,
                'firstName', u.first_name,
                'lastName', u.last_name,
                'avatarUrl', u.avatar_url,
                'isActive', u.is_active
            )
            FROM tb_user u
            WHERE u.pk_user = p.fk_author
        )
    ) AS data,
    p.pk_post AS post_pk,
    p.fk_author AS author_pk
FROM tb_post p;

-- Denormalized filter columns for efficient WHERE clauses
CREATE INDEX IF NOT EXISTS idx_v_post_data_gin ON v_post USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_v_post_author_pk ON v_post(author_pk);

-- ============================================================================
-- View: v_comment
-- Maps tb_comment with nested author and post data
-- FraiseQL pattern: nested relationships pre-computed in JSONB
-- ============================================================================

CREATE OR REPLACE VIEW v_comment AS
SELECT
    c.id,
    jsonb_build_object(
        'id', c.id::text,
        'content', c.content,
        'isApproved', c.is_approved,
        'createdAt', c.created_at,
        'updatedAt', c.updated_at,
        'author', (
            SELECT jsonb_build_object(
                'id', u.id::text,
                'username', u.username,
                'firstName', u.first_name,
                'lastName', u.last_name,
                'avatarUrl', u.avatar_url
            )
            FROM tb_user u
            WHERE u.pk_user = c.fk_author
        ),
        'post', (
            SELECT jsonb_build_object(
                'id', p.id::text,
                'title', p.title,
                'status', p.status
            )
            FROM tb_post p
            WHERE p.pk_post = c.fk_post
        )
    ) AS data,
    c.pk_comment AS comment_pk,
    c.fk_post AS post_pk,
    c.fk_author AS author_pk
FROM tb_comment c;

-- Denormalized filter columns for efficient WHERE clauses
CREATE INDEX IF NOT EXISTS idx_v_comment_data_gin ON v_comment USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_v_comment_post_pk ON v_comment(post_pk);
CREATE INDEX IF NOT EXISTS idx_v_comment_author_pk ON v_comment(author_pk);

-- ============================================================================
-- Optional: Fact Tables for Analytics (tf_* pattern)
-- ============================================================================

-- Fact table for API query metrics
-- Measures: latency, response size, etc.
-- Dimensions: endpoint, status code, etc. (in JSONB for flexibility)
CREATE TABLE IF NOT EXISTS tf_api_calls (
    id BIGSERIAL PRIMARY KEY,

    -- Measures (numeric columns for aggregation)
    latency_ms INT NOT NULL,
    request_size INT DEFAULT 0,
    response_size INT DEFAULT 0,

    -- Dimensions (JSONB for flexible grouping)
    data JSONB NOT NULL,

    -- Denormalized filters (indexed for fast WHERE)
    user_id UUID,
    endpoint VARCHAR(500) NOT NULL,
    status_code INT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for denormalized filters
CREATE INDEX IF NOT EXISTS idx_api_calls_user ON tf_api_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_endpoint ON tf_api_calls(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_calls_status ON tf_api_calls(status_code);
CREATE INDEX IF NOT EXISTS idx_api_calls_occurred ON tf_api_calls(occurred_at);
CREATE INDEX IF NOT EXISTS idx_api_calls_data_gin ON tf_api_calls USING GIN(data);
