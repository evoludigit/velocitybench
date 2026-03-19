-- JSONB views (v_*) for fraiseql-v variant (on-the-fly JSONB computation)
-- Apply to an existing database: psql -h localhost -U benchmark -d velocitybench_benchmark -f database/v_views.sql
--
-- Run this when the DB was initialized with the old fv_ view names
-- (renames fv_* → v_* and recreates with FraiseQL-compatible column aliases).

SET search_path TO benchmark, public;

-- Drop old fv_ views if they exist (pre-rename migration)
DROP VIEW IF EXISTS benchmark.fv_comment CASCADE;
DROP VIEW IF EXISTS benchmark.fv_post CASCADE;
DROP VIEW IF EXISTS benchmark.fv_user CASCADE;

-- Drop current v_ views so we can recreate with correct schema
DROP VIEW IF EXISTS v_comment CASCADE;
DROP VIEW IF EXISTS v_post CASCADE;
DROP VIEW IF EXISTS v_user CASCADE;

-- v_user: User entity as JSONB
CREATE VIEW v_user AS
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
CREATE VIEW v_post AS
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
CREATE VIEW v_comment AS
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
LEFT JOIN benchmark.tb_user u  ON u.pk_user  = c.fk_author
LEFT JOIN benchmark.tb_post p  ON p.pk_post  = c.fk_post
LEFT JOIN benchmark.tb_user pu ON pu.pk_user = p.fk_author;

GRANT SELECT ON v_user    TO PUBLIC;
GRANT SELECT ON v_post    TO PUBLIC;
GRANT SELECT ON v_comment TO PUBLIC;
