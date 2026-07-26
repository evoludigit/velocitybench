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

-- fv_user: User entity as JSONB
DROP VIEW IF EXISTS fv_user CASCADE;

CREATE VIEW fv_user AS
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

-- fv_post: Post entity with nested author as JSONB
-- Author pre-computed to eliminate N+1 queries
DROP VIEW IF EXISTS fv_post CASCADE;

CREATE VIEW fv_post AS
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
        -- LEAN author summary — matches tv_post.author so the fv/tv document shapes agree.
        'author',     jsonb_build_object(
            'id',        u.id::text,
            'username',  u.username,
            'full_name', u.full_name,
            'bio',       u.bio
        )
    ) AS data,
    p.pk_post      AS _pk,
    p.fk_author    AS _author_pk,
    p.published    AS _published
FROM benchmark.tb_post p
LEFT JOIN benchmark.tb_user u ON u.pk_user = p.fk_author;

-- fv_comment: Comment entity with nested author and post as JSONB
-- Both relationships pre-computed to eliminate N+1 queries
DROP VIEW IF EXISTS fv_comment CASCADE;

CREATE VIEW fv_comment AS
SELECT
    c.id,
    jsonb_build_object(
        'id',         c.id::text,
        'identifier', c.identifier,
        'content',    c.content,
        'created_at',  c.created_at,
        'updated_at',  c.updated_at,
        -- LEAN author {id, username} + post summary {id, title} — matches tv_comment.
        'author',     jsonb_build_object(
            'id',       u.id::text,
            'username', u.username
        ),
        'post',       jsonb_build_object(
            'id',    p.id::text,
            'title', p.title
        )
    ) AS data,
    c.pk_comment   AS _pk,
    c.fk_author    AS _author_pk,
    c.fk_post      AS _post_pk,
    p.id           AS post_id
FROM benchmark.tb_comment c
LEFT JOIN benchmark.tb_user u  ON u.pk_user   = c.fk_author
LEFT JOIN benchmark.tb_post p  ON p.pk_post   = c.fk_post;

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
-- Under the lean model tv_comment.post is already just {id, title}; the 'post' key
-- is still dropped at aggregation time (data - 'post') because the full blog page
-- carries the post once at the top level, so repeating even a tiny post per comment
-- is redundant. Key removal stays O(1). The lean author inside tv_comment is preserved.
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
-- fk_author indexes on the precomputed tables — the pg_tviews cascade updates
-- tv_post / tv_comment by fk_author when a user changes, so without these it
-- falls back to a seq scan.
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tv_comment_fk_author ON benchmark.tv_comment(fk_author);
CREATE INDEX IF NOT EXISTS idx_tv_post_fk_author    ON benchmark.tv_post(fk_author);

-- ============================================================================
-- (v_comment_slim removed) — with the lean model tv_comment.post is already just
-- {id, title}, so Q3 reads tv_comment directly. The old slim view existed only to
-- strip the full embedded post JSONB at query time; that heavy embed no longer exists.
-- ============================================================================

-- ============================================================================
-- Permissions
-- ============================================================================

GRANT SELECT ON fv_user    TO PUBLIC;
GRANT SELECT ON fv_post    TO PUBLIC;
GRANT SELECT ON fv_comment TO PUBLIC;
