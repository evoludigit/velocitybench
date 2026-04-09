-- FraiseQL TV Tables — Bulk Sync after Large Dataset Load
--
-- pg_tviews installs row-level triggers on tb_* for incremental updates,
-- but bulk INSERT via generate_series bypasses trigger cascading in pg_tviews.
-- This file does a one-time full sync from tb_* into tv_*.
--
-- Must run AFTER: 05-large-dataset.sql and 05-fraiseql-views.sql
-- (v_* views must exist for the JSONB shape to be consistent)

SET search_path TO benchmark, public;

-- Sync tv_user from tb_user
INSERT INTO benchmark.tv_user (pk_user, id, identifier, data)
SELECT
    u.pk_user,
    u.id,
    u.identifier,
    jsonb_build_object(
        'id',         u.id::text,
        'identifier', u.identifier,
        'email',      u.email,
        'username',   u.username,
        'full_name',  u.full_name,
        'bio',        u.bio,
        'created_at', u.created_at,
        'updated_at', u.updated_at
    )
FROM benchmark.tb_user u
ON CONFLICT (pk_user) DO UPDATE
    SET data       = EXCLUDED.data,
        updated_at = NOW();

ANALYZE benchmark.tv_user;

-- Sync tv_post from tb_post (with embedded author)
INSERT INTO benchmark.tv_post (pk_post, id, identifier, fk_author, _published, author_id, data)
SELECT
    p.pk_post,
    p.id,
    p.identifier,
    p.fk_author,
    p.published,
    u.id,
    jsonb_build_object(
        'id',         p.id::text,
        'identifier', p.identifier,
        'title',      p.title,
        'content',    p.content,
        'published',  p.published,
        'created_at', p.created_at,
        'updated_at', p.updated_at,
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'full_name',  u.full_name,
            'bio',        u.bio,
            'created_at', u.created_at,
            'updated_at', u.updated_at
        )
    )
FROM benchmark.tb_post p
JOIN benchmark.tb_user u ON u.pk_user = p.fk_author
ON CONFLICT (pk_post) DO UPDATE
    SET data       = EXCLUDED.data,
        fk_author  = EXCLUDED.fk_author,
        _published = EXCLUDED._published,
        author_id  = EXCLUDED.author_id,
        updated_at = NOW();

ANALYZE benchmark.tv_post;

-- Sync tv_comment from tb_comment (with embedded author + post + post.author)
INSERT INTO benchmark.tv_comment (pk_comment, id, identifier, fk_author, fk_post, author_id, post_id, data)
SELECT
    c.pk_comment,
    c.id,
    c.identifier,
    c.fk_author,
    c.fk_post,
    u.id,
    p.id,
    jsonb_build_object(
        'id',         c.id::text,
        'identifier', c.identifier,
        'content',    c.content,
        'created_at', c.created_at,
        'updated_at', c.updated_at,
        'author',     jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'full_name',  u.full_name,
            'bio',        u.bio,
            'created_at', u.created_at,
            'updated_at', u.updated_at
        ),
        'post',       jsonb_build_object(
            'id',         p.id::text,
            'identifier', p.identifier,
            'title',      p.title,
            'content',    p.content,
            'published',  p.published,
            'created_at', p.created_at,
            'updated_at', p.updated_at,
            'author',     jsonb_build_object(
                'id',         pu.id::text,
                'identifier', pu.identifier,
                'email',      pu.email,
                'username',   pu.username,
                'full_name',  pu.full_name,
                'bio',        pu.bio,
                'created_at', pu.created_at,
                'updated_at', pu.updated_at
            )
        )
    )
FROM benchmark.tb_comment c
JOIN benchmark.tb_user u  ON u.pk_user  = c.fk_author
JOIN benchmark.tb_post  p ON p.pk_post  = c.fk_post
JOIN benchmark.tb_user pu ON pu.pk_user = p.fk_author
ON CONFLICT (pk_comment) DO UPDATE
    SET data       = EXCLUDED.data,
        fk_author  = EXCLUDED.fk_author,
        fk_post    = EXCLUDED.fk_post,
        author_id  = EXCLUDED.author_id,
        post_id    = EXCLUDED.post_id,
        updated_at = NOW();

ANALYZE benchmark.tv_comment;

DO $$ BEGIN
    RAISE NOTICE 'tv_* bulk sync complete.';
END $$;
