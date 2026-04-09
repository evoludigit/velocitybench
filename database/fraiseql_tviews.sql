-- FraiseQL TV Tables — pg_tviews_create() setup
--
-- Must run AFTER:
--   - fraiseql_cqrs_schema.sql  (tb_* tables + small seed data)
--   - 04-cqrs-extensions.sql    (tb_user_follows, tb_post_like)
--   - extensions.sql            (v_* views must exist first so pg_tviews resolves correctly)
--
-- Must run BEFORE:
--   - 05-large-dataset.sql      (bulk inserts; triggers installed here cascade to tv_*)
--
-- pg_tviews_create() requires direct table queries (not views) so it can trace
-- source tables and install the correct triggers. The JSONB shape uses the same
-- snake_case keys as the v_* views — single convention, two materialisation paths.

SET search_path TO benchmark, public;

-- tv_user
SELECT pg_tviews_create('tv_user', $TVIEW_SQL$
    SELECT
        u.pk_user     AS pk_user,
        u.id          AS id,
        u.identifier  AS identifier,
        jsonb_build_object(
            'id',         u.id::text,
            'identifier', u.identifier,
            'email',      u.email,
            'username',   u.username,
            'full_name',  u.full_name,
            'bio',        u.bio,
            'created_at', u.created_at,
            'updated_at', u.updated_at
        )             AS data
    FROM benchmark.tb_user u
$TVIEW_SQL$);

-- tv_post — author embedded via JOIN
SELECT pg_tviews_create('tv_post', $TVIEW_SQL$
    SELECT
        p.pk_post     AS pk_post,
        p.id          AS id,
        p.identifier  AS identifier,
        p.fk_author   AS fk_author,
        p.published   AS _published,
        u.id          AS author_id,
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
        )             AS data
    FROM benchmark.tb_post p
    JOIN benchmark.tb_user u ON u.pk_user = p.fk_author
$TVIEW_SQL$);

-- pg_tviews infers TEXT for generic expressions; cast _published to BOOLEAN so
-- FraiseQL can filter directly with boolean params instead of JSONB extraction.
ALTER TABLE benchmark.tv_post ALTER COLUMN _published TYPE boolean USING _published::boolean;

-- tv_comment — author + post (with its author) embedded via JOINs
SELECT pg_tviews_create('tv_comment', $TVIEW_SQL$
    SELECT
        c.pk_comment  AS pk_comment,
        c.id          AS id,
        c.identifier  AS identifier,
        c.fk_author   AS fk_author,
        c.fk_post     AS fk_post,
        u.id          AS author_id,
        p.id          AS post_id,
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
        )             AS data
    FROM benchmark.tb_comment c
    JOIN benchmark.tb_user u  ON u.pk_user  = c.fk_author
    JOIN benchmark.tb_post  p ON p.pk_post  = c.fk_post
    JOIN benchmark.tb_user pu ON pu.pk_user = p.fk_author
$TVIEW_SQL$);

COMMENT ON TABLE benchmark.tv_user    IS 'Query side: TVIEW managed by pg_tviews — pre-computed user JSONB';
COMMENT ON TABLE benchmark.tv_post    IS 'Query side: TVIEW managed by pg_tviews — pre-computed post JSONB with embedded author';
COMMENT ON TABLE benchmark.tv_comment IS 'Query side: TVIEW managed by pg_tviews — pre-computed comment JSONB with embedded author and post';
