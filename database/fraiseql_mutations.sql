-- FraiseQL Mutation SQL Functions
--
-- FraiseQL passes each argument as JSONB (serde_json::Value via tokio-postgres).
-- Use `p_arg #>> '{}'` to extract a scalar JSONB value as TEXT, then cast.
-- JSON null → SQL NULL via #>> '{}', so COALESCE works correctly.
--
-- Return shape must be the FraiseQL mutation_response contract:
--   status      TEXT   -- "updated" | "new" | "deleted" | "failed:*" | "conflict:*" | "error"
--   message     TEXT   -- optional error description
--   entity      JSONB  -- the mutated entity
--   entity_type TEXT   -- GraphQL type name (e.g. "User")
--   cascade     JSONB  -- optional cascaded changes
--   metadata    JSONB  -- optional error metadata
--
-- Write path: fn_*() writes to tb_* (CQRS command tables).
-- pg_tviews triggers then cascade-sync to tv_* (pre-computed JSONB tables)
-- and the v_* views pick up changes automatically.

SET search_path TO benchmark, public;

-- ============================================================================
-- fn_update_user: Update a user's bio and return the updated user as JSONB
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.fn_update_user(
    p_id   JSONB,
    p_bio  JSONB DEFAULT NULL
) RETURNS TABLE(
    status      TEXT,
    message     TEXT,
    entity      JSONB,
    entity_type TEXT,
    cascade     JSONB,
    metadata    JSONB
) AS $$
    UPDATE benchmark.tb_user
    SET
        bio        = COALESCE(p_bio #>> '{}', bio),
        updated_at = NOW()
    WHERE benchmark.tb_user.id = (p_id #>> '{}')::UUID
    RETURNING
        'updated'::TEXT,
        NULL::TEXT,
        jsonb_build_object(
            'id',         benchmark.tb_user.id::text,
            'identifier', identifier,
            'email',      email,
            'username',   username,
            'fullName',   full_name,
            'bio',        bio,
            'createdAt',  to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        ),
        'User'::TEXT,
        NULL::JSONB,
        NULL::JSONB;
$$ LANGUAGE sql;

GRANT EXECUTE ON FUNCTION benchmark.fn_update_user(JSONB, JSONB) TO PUBLIC;

-- ============================================================================
-- fn_create_post: Insert a new post and return the created post as JSONB
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.fn_create_post(
    p_title     JSONB,
    p_content   JSONB,
    p_author_id JSONB,
    p_published JSONB DEFAULT 'false'::jsonb
) RETURNS TABLE(
    status      TEXT,
    message     TEXT,
    entity      JSONB,
    entity_type TEXT,
    cascade     JSONB,
    metadata    JSONB
) AS $$
DECLARE
    v_title       TEXT;
    v_content     TEXT;
    v_author_uuid UUID;
    v_published   BOOLEAN;
    v_author_pk   INT;
    v_post_id     UUID;
    v_slug        TEXT;
BEGIN
    v_title       := p_title #>> '{}';
    v_content     := p_content #>> '{}';
    v_author_uuid := (p_author_id #>> '{}')::UUID;
    v_published   := (p_published #>> '{}')::BOOLEAN;

    -- Resolve author UUID → internal pk (fast INT join)
    SELECT pk_user INTO v_author_pk
    FROM benchmark.tb_user
    WHERE benchmark.tb_user.id = v_author_uuid;

    IF v_author_pk IS NULL THEN
        RETURN QUERY SELECT
            'failed:not_found'::TEXT,
            'Author not found'::TEXT,
            NULL::JSONB,
            'Post'::TEXT,
            NULL::JSONB,
            NULL::JSONB;
        RETURN;
    END IF;

    -- Generate a unique slug from title
    v_post_id := gen_random_uuid();
    v_slug := lower(regexp_replace(v_title, '[^a-zA-Z0-9]+', '-', 'g'))
              || '-' || substring(v_post_id::text, 1, 8);

    RETURN QUERY
    INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published)
    VALUES (v_post_id, v_slug, v_title, v_content, v_author_pk, v_published)
    RETURNING
        'new'::TEXT,
        NULL::TEXT,
        jsonb_build_object(
            'id',         benchmark.tb_post.id::text,
            'identifier', identifier,
            'title',      title,
            'content',    content,
            'published',  published,
            'createdAt',  to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'updatedAt',  to_char(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'author',     jsonb_build_object(
                'id',       v_author_uuid::text,
                'username', (SELECT username FROM benchmark.tb_user WHERE benchmark.tb_user.id = v_author_uuid),
                'fullName', (SELECT full_name FROM benchmark.tb_user WHERE benchmark.tb_user.id = v_author_uuid)
            )
        ),
        'Post'::TEXT,
        NULL::JSONB,
        NULL::JSONB;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_post(JSONB, JSONB, JSONB, JSONB) TO PUBLIC;
