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
DROP VIEW IF EXISTS fv_user CASCADE;

CREATE VIEW fv_user AS
SELECT
    id,
    jsonb_build_object(
        'id',         id::text,
        'identifier', identifier,
        'email',      email,
        'username',   username,
        'fullName',   full_name,
        'bio',        bio,
        'createdAt',  to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        'updatedAt',  to_char(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
    ) AS data,
    pk_user AS _pk
FROM benchmark.tb_user;

-- v_post: Post entity with nested author as JSONB
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
        'createdAt',  to_char(p.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        'updatedAt',  to_char(p.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'fullName',   u.full_name,
            'bio',        u.bio,
            'createdAt',  to_char(u.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(u.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        )
    ) AS data,
    p.pk_post      AS _pk,
    p.fk_author    AS _author_pk,
    p.published    AS _published
FROM benchmark.tb_post p
LEFT JOIN benchmark.tb_user u ON u.pk_user = p.fk_author;

-- v_comment: Comment entity with nested author and post as JSONB
-- Both relationships pre-computed to eliminate N+1 queries
DROP VIEW IF EXISTS fv_comment CASCADE;

CREATE VIEW fv_comment AS
SELECT
    c.id,
    jsonb_build_object(
        'id',         c.id::text,
        'identifier', c.identifier,
        'content',    c.content,
        'createdAt',  to_char(c.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        'updatedAt',  to_char(c.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'fullName',   u.full_name,
            'bio',        u.bio,
            'createdAt',  to_char(u.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(u.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        ),
        'post',       jsonb_build_object(
            'id',         p.id::text,
            'identifier', p.identifier,
            'title',      p.title,
            'content',    p.content,
            'published',  p.published,
            'createdAt',  to_char(p.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(p.updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'author',     jsonb_build_object(
                'id',         pu.id::text,
                'identifier', pu.identifier,
                'email',      pu.email,
                'username',   pu.username,
                'fullName',   pu.full_name,
                'bio',        pu.bio
            )
        )
    ) AS data,
    c.pk_comment   AS _pk,
    c.fk_author    AS _author_pk,
    c.fk_post      AS _post_pk
FROM benchmark.tb_comment c
LEFT JOIN benchmark.tb_user u  ON u.pk_user   = c.fk_author
LEFT JOIN benchmark.tb_post p  ON p.pk_post   = c.fk_post
LEFT JOIN benchmark.tb_user pu ON pu.pk_user  = p.fk_author;

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

-- ============================================================================
-- Permissions
-- ============================================================================

GRANT SELECT ON fv_user    TO PUBLIC;
GRANT SELECT ON fv_post    TO PUBLIC;
GRANT SELECT ON fv_comment TO PUBLIC;
