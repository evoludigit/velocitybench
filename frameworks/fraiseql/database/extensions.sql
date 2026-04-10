-- FraiseQL v2.0.0-beta.3 Database Extensions
--
-- Two families of views, both built on the CQRS trinity-pattern tables:
--
--   v_*  (Variant A) — on-the-fly JSONB views (schema.py)
--       JSONB is constructed at query time via jsonb_build_object().
--       Consistent with fraiseql init canonical blog template.
--
--   tv_* (Variant B) — pre-computed JSONB tables (schema_tv.py)
--       JSONB is baked in at INSERT time; queries just SELECT the column.
--       snake_case keys align directly with database columns.
--
-- Trinity pattern fields exposed at the top level of every JSONB object:
--   pk         INT    — internal integer primary key (fast join)
--   id         UUID   — public GraphQL ID (secure, UUID v4)
--   identifier TEXT   — human-readable identifier (username / slug)

SET search_path TO benchmark, public;

-- ============================================================================
-- VARIANT A: On-the-fly JSONB Views (v_*)
-- ============================================================================

-- v_user: User entity as JSONB
DROP VIEW IF EXISTS v_user CASCADE;

CREATE VIEW v_user AS
SELECT
    id,
    jsonb_build_object(
        'id',         id::text,
        'identifier', identifier,
        'email',      email,
        'username',   username,
        'full_name',   full_name,
        'bio',        bio,
        'created_at',  created_at,
        'updated_at',  updated_at
    ) AS data,
    pk_user AS _pk
FROM benchmark.tb_user;

-- v_post: Post entity with nested author as JSONB
-- Author pre-computed to eliminate N+1 queries
DROP VIEW IF EXISTS v_post CASCADE;

CREATE VIEW v_post AS
SELECT
    p.id,
    jsonb_build_object(
        'id',         p.id::text,
        'identifier', p.identifier,
        'title',      p.title,
        'content',    p.content,
        'published',  p.published,
        'created_at',  p.created_at,
        'updated_at',  p.updated_at,
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'full_name',   u.full_name,
            'bio',        u.bio,
            'created_at',  u.created_at,
            'updated_at',  u.updated_at
        )
    ) AS data,
    p.pk_post      AS _pk,
    p.fk_author    AS _author_pk,
    p.published    AS _published
FROM benchmark.tb_post p
LEFT JOIN benchmark.tb_user u ON u.pk_user = p.fk_author;

-- v_comment: Comment entity with nested author and post as JSONB
-- Both relationships pre-computed to eliminate N+1 queries
DROP VIEW IF EXISTS v_comment CASCADE;

CREATE VIEW v_comment AS
SELECT
    c.id,
    jsonb_build_object(
        'id',         c.id::text,
        'identifier', c.identifier,
        'content',    c.content,
        'created_at',  c.created_at,
        'updated_at',  c.updated_at,
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'full_name',   u.full_name,
            'bio',        u.bio,
            'created_at',  u.created_at,
            'updated_at',  u.updated_at
        ),
        'post',       jsonb_build_object(
            'id',         p.id::text,
            'identifier', p.identifier,
            'title',      p.title,
            'content',    p.content,
            'published',  p.published,
            'created_at',  p.created_at,
            'updated_at',  p.updated_at,
            'author',     jsonb_build_object(
                'id',         pu.id::text,
                'identifier', pu.identifier,
                'email',      pu.email,
                'username',   pu.username,
                'full_name',   pu.full_name,
                'bio',        pu.bio
            )
        )
    ) AS data,
    c.pk_comment   AS _pk,
    c.fk_author    AS _author_pk,
    c.fk_post      AS _post_pk,
    p.id           AS post_id
FROM benchmark.tb_comment c
LEFT JOIN benchmark.tb_user u  ON u.pk_user   = c.fk_author
LEFT JOIN benchmark.tb_post p  ON p.pk_post   = c.fk_post
LEFT JOIN benchmark.tb_user pu ON pu.pk_user  = p.fk_author;

-- ============================================================================
-- COMPOSED VIEW: v_post_full
-- Post with embedded comments — enables single-query T1 (full blog page load).
--
-- tv_post supplies the post + author JSONB (pre-computed at write time).
-- tb_comment + tb_user supply the comments (raw tables, joined at query time).
--
-- Shape selection (benchmarked 2026-04-09, 40 workers):
--   A) jsonb_agg(c.data)              → 2,791 RPS, 23KB payload (post content ×N per comment)
--   B) jsonb_agg(c.data - 'post')     → 4,213 RPS,  8.7KB payload  ← WINNER
--   C) jsonb_build_object from raw tables → 2,561 RPS, 8.7KB (CPU cost > wire savings)
--   D) LATERAL + strip                → 3,120 RPS, 8.7KB
--
-- tv_comment embeds the full post JSONB at write time. Stripping the 'post' key
-- at aggregation time (data - 'post') cuts payload 2.7× with negligible CPU cost,
-- since key removal on a small key set is O(1) compared to jsonb_build_object
-- over join rows. The pre-computed author inside tv_comment is preserved.
-- ============================================================================

DROP VIEW IF EXISTS benchmark.v_post_full;

CREATE VIEW benchmark.v_post_full AS
SELECT
    p.pk_post,
    p.id,
    p.identifier,
    p.fk_author,
    p._published,
    p.author_id,
    jsonb_set(
        p.data,
        '{comments}',
        COALESCE(
            (
                SELECT jsonb_agg((c.data - 'post') ORDER BY (c.data->>'created_at') DESC)
                FROM benchmark.tv_comment c
                WHERE c.fk_post = p.pk_post
                LIMIT 10
            ),
            '[]'::jsonb
        )
    ) AS data
FROM benchmark.tv_post p;

GRANT SELECT ON benchmark.v_post_full TO PUBLIC;

-- ============================================================================
-- Indexes on underlying tables (views are not directly indexed)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tb_user_id         ON benchmark.tb_user(id);
CREATE INDEX IF NOT EXISTS idx_tb_user_identifier  ON benchmark.tb_user(identifier);

CREATE INDEX IF NOT EXISTS idx_tb_post_id          ON benchmark.tb_post(id);
CREATE INDEX IF NOT EXISTS idx_tb_post_identifier  ON benchmark.tb_post(identifier);
CREATE INDEX IF NOT EXISTS idx_tb_post_published   ON benchmark.tb_post(published);
CREATE INDEX IF NOT EXISTS idx_tb_post_fk_author   ON benchmark.tb_post(fk_author);

CREATE INDEX IF NOT EXISTS idx_tb_comment_id       ON benchmark.tb_comment(id);
CREATE INDEX IF NOT EXISTS idx_tb_comment_fk_post  ON benchmark.tb_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_tb_comment_fk_author ON benchmark.tb_comment(fk_author);

-- Indexes on tv_comment for v_post_full composed view
-- Without these, postFull triggers a full-table seq scan on tv_comment (500k rows) per request
CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_post     ON benchmark.tv_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_tv_comment_created_at  ON benchmark.tv_comment((data->>'created_at'));

-- ============================================================================
-- Indexes on tv_comment.fk_author for delta mutation path
-- (tv_comment only had idx_tv_comment_fk_post; fk_author was missing → seq scan)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_author ON benchmark.tv_comment(fk_author);
CREATE INDEX IF NOT EXISTS idx_tv_post_fk_author    ON benchmark.tv_post(fk_author);

-- ============================================================================
-- tvd_* tables — delta-managed TV tables (no pg_tviews triggers)
--
-- Structurally identical to tv_* but owned exclusively by fn_update_user_delta.
-- pg_tviews writes to tv_*; jsonb_delta patches write to tvd_*.
-- Seeded from tv_* at init time; diverges after mutations.
--
-- Purpose: isolated benchmark target for jsonb_delta surgical-patch vs
-- pg_tviews full-recompute cascade comparison (M1 vs M1d).
-- ============================================================================

CREATE TABLE IF NOT EXISTS benchmark.tvd_user (
    pk_user    BIGINT      NOT NULL,
    id         UUID        NOT NULL,
    identifier TEXT,
    data       JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (pk_user)
);

CREATE TABLE IF NOT EXISTS benchmark.tvd_post (
    pk_post    BIGINT      NOT NULL,
    id         UUID        NOT NULL,
    identifier TEXT,
    data       JSONB,
    fk_author  BIGINT,
    author_id  UUID,
    _published BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (pk_post)
);

CREATE TABLE IF NOT EXISTS benchmark.tvd_comment (
    pk_comment BIGINT      NOT NULL,
    id         UUID        NOT NULL,
    identifier TEXT,
    data       JSONB,
    fk_author  BIGINT,
    fk_post    BIGINT,
    author_id  UUID,
    post_id    UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (pk_comment)
);

-- Indexes — include fk_author which tv_* was missing (caused seq scans in delta path)
CREATE INDEX IF NOT EXISTS idx_tvd_user_id          ON benchmark.tvd_user(id);
CREATE INDEX IF NOT EXISTS idx_tvd_post_id          ON benchmark.tvd_post(id);
CREATE INDEX IF NOT EXISTS idx_tvd_post_fk_author   ON benchmark.tvd_post(fk_author);
CREATE INDEX IF NOT EXISTS idx_tvd_comment_id       ON benchmark.tvd_comment(id);
CREATE INDEX IF NOT EXISTS idx_tvd_comment_fk_post  ON benchmark.tvd_comment(fk_post);
CREATE INDEX IF NOT EXISTS idx_tvd_comment_fk_author ON benchmark.tvd_comment(fk_author);

-- Seed from tv_* (run once at init; INSERT … ON CONFLICT DO NOTHING is idempotent)
INSERT INTO benchmark.tvd_user
    SELECT pk_user, id, identifier, data, created_at, updated_at FROM benchmark.tv_user
    ON CONFLICT (pk_user) DO NOTHING;

INSERT INTO benchmark.tvd_post
    SELECT pk_post, id, identifier, data, fk_author, author_id, _published, created_at, updated_at
    FROM benchmark.tv_post
    ON CONFLICT (pk_post) DO NOTHING;

INSERT INTO benchmark.tvd_comment
    SELECT pk_comment, id, identifier, data, fk_author, fk_post, author_id, post_id, created_at, updated_at
    FROM benchmark.tv_comment
    ON CONFLICT (pk_comment) DO NOTHING;

GRANT SELECT, INSERT, UPDATE ON benchmark.tvd_user    TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON benchmark.tvd_post    TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON benchmark.tvd_comment TO PUBLIC;

-- ============================================================================
-- v_post_full_delta — composed view over tvd_* for T1d read benchmark
-- Same shape as v_post_full but reads from delta-managed tables.
-- ============================================================================

DROP VIEW IF EXISTS benchmark.v_post_full_delta;

CREATE VIEW benchmark.v_post_full_delta AS
SELECT
    p.pk_post,
    p.id,
    p.identifier,
    p.fk_author,
    p._published,
    p.author_id,
    jsonb_set(
        p.data,
        '{comments}',
        COALESCE(
            (
                SELECT jsonb_agg((c.data - 'post') ORDER BY (c.data->>'created_at') DESC)
                FROM benchmark.tvd_comment c
                WHERE c.fk_post = p.pk_post
                LIMIT 10
            ),
            '[]'::jsonb
        )
    ) AS data
FROM benchmark.tvd_post p;

GRANT SELECT ON benchmark.v_post_full_delta TO PUBLIC;

-- ============================================================================
-- fn_update_user_delta — surgical jsonb_delta mutation targeting tvd_* tables
--
-- Contrast with fn_update_user which writes to tb_user and lets pg_tviews
-- cascade-recompute tv_* via full JOINs.
--
-- This function:
--   1. Acquires tb_user row lock (same serialization as pg_tviews cascade)
--   2. Checks for no-change (skips if bio already matches — mirrors pg_tviews delta check)
--   3. Patches tvd_user / tvd_post / tvd_comment surgically via jsonb_delta
--      — no JOIN recompute, no full-row JSONB rebuild
--   4. Index on tvd_comment.fk_author (idx_tvd_comment_fk_author) ensures index scan,
--      not seq scan (the missing index that made the naive delta ~200× slower than pg_tviews)
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.fn_update_user_delta(
    p_id  JSONB,
    p_bio JSONB DEFAULT NULL
) RETURNS TABLE(
    status      TEXT,
    message     TEXT,
    entity      JSONB,
    entity_type TEXT,
    cascade     JSONB,
    metadata    JSONB,
    entity_id   TEXT
) AS $$
DECLARE
    v_pk          BIGINT;
    v_bio         TEXT := COALESCE(p_bio #>> '{}', '');
    v_data        JSONB;
    v_patch       JSONB;
    v_post_pks    BIGINT[];
    v_current_bio TEXT;
BEGIN
    -- Serialize concurrent updates per user via the same row lock pg_tviews uses
    SELECT pk_user INTO v_pk
    FROM benchmark.tb_user
    WHERE id = (p_id #>> '{}')::UUID
    FOR UPDATE;

    IF v_pk IS NULL THEN
        RETURN QUERY SELECT
            'failed:not_found'::TEXT, 'User not found'::TEXT,
            NULL::JSONB, 'User'::TEXT, NULL::JSONB, NULL::JSONB, NULL::TEXT;
        RETURN;
    END IF;

    -- No-change detection — mirrors pg_tviews_check_jsonb_delta skip behaviour
    SELECT data->>'bio' INTO v_current_bio FROM benchmark.tvd_user WHERE pk_user = v_pk;
    IF v_current_bio IS NOT DISTINCT FROM v_bio THEN
        SELECT data INTO v_data FROM benchmark.tvd_user WHERE pk_user = v_pk;
        RETURN QUERY SELECT
            'updated'::TEXT, NULL::TEXT, v_data, 'User'::TEXT,
            NULL::JSONB, NULL::JSONB, (p_id #>> '{}')::TEXT;
        RETURN;
    END IF;

    v_patch := jsonb_build_object('bio', v_bio);

    -- Surgical patches — idx_tvd_*_fk_author ensures index scan, not seq scan
    UPDATE benchmark.tvd_user
    SET data = jsonb_smart_patch_scalar(data, v_patch)
    WHERE pk_user = v_pk;

    UPDATE benchmark.tvd_post
    SET data = jsonb_smart_patch_nested(data, v_patch, '{author}')
    WHERE fk_author = v_pk;

    UPDATE benchmark.tvd_comment
    SET data = jsonb_smart_patch_nested(data, v_patch, '{author}')
    WHERE fk_author = v_pk;

    -- Also patch embedded post.author in comments on this user's posts
    SELECT ARRAY(SELECT pk_post FROM benchmark.tb_post WHERE fk_author = v_pk)
    INTO v_post_pks;

    IF array_length(v_post_pks, 1) > 0 THEN
        UPDATE benchmark.tvd_comment
        SET data = jsonb_smart_patch_nested(data, v_patch, '{post,author}')
        WHERE fk_post = ANY(v_post_pks);
    END IF;

    SELECT data INTO v_data FROM benchmark.tvd_user WHERE pk_user = v_pk;

    RETURN QUERY SELECT
        'updated'::TEXT, NULL::TEXT, v_data, 'User'::TEXT,
        NULL::JSONB, NULL::JSONB, (p_id #>> '{}')::TEXT;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_update_user_delta(JSONB, JSONB) TO PUBLIC;

-- ============================================================================
-- v_comment_slim — Q3 optimized view: strips heavy post fields from tv_comment
--
-- tv_comment embeds the full post JSONB (5KB content + author), yielding 1,936
-- bytes/row in Q3 responses. The Q3 query only needs post identity fields.
-- Stripping to {id, identifier, title, published, created_at} cuts rows to
-- ~761 bytes (-37%), reducing Q3 wire payload without a schema change.
-- ============================================================================

DROP VIEW IF EXISTS benchmark.v_comment_slim;

CREATE VIEW benchmark.v_comment_slim AS
SELECT
    pk_comment, id, identifier, fk_author, fk_post, author_id, post_id,
    created_at, updated_at,
    data || jsonb_build_object('post',
        jsonb_build_object(
            'id',         data->'post'->>'id',
            'identifier', data->'post'->>'identifier',
            'title',      data->'post'->>'title',
            'published',  data->'post'->'published',
            'created_at', data->'post'->>'created_at'
        )
    ) AS data
FROM benchmark.tv_comment;

GRANT SELECT ON benchmark.v_comment_slim TO PUBLIC;

-- ============================================================================
-- Permissions
-- ============================================================================

GRANT SELECT ON v_user    TO PUBLIC;
GRANT SELECT ON v_post    TO PUBLIC;
GRANT SELECT ON v_comment TO PUBLIC;
