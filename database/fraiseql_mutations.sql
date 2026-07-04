-- FraiseQL Mutation SQL Functions (v2.2.0 — uses fraiseql.mutation_ok / mutation_err helpers)
--
-- FraiseQL v2.2.0 passes scalar arguments as TEXT via FlexParam::Text.
-- Null arguments arrive as SQL NULL (FlexParam::Null).
--
-- Requires: fraiseql setup (installs fraiseql.mutation_ok / fraiseql.mutation_err)
--
-- Write path: fn_*() writes to tb_* (CQRS command tables).
-- pg_tviews triggers then cascade-sync to tv_* (pre-computed JSONB tables)
-- and the v_* views pick up changes automatically.

SET search_path TO benchmark, public;

-- ============================================================================
-- fn_update_user: Update a user's bio and return the updated user as JSONB
-- ============================================================================

DROP FUNCTION IF EXISTS benchmark.fn_update_user(JSONB, JSONB);
DROP FUNCTION IF EXISTS benchmark.fn_update_user(TEXT, TEXT);

CREATE FUNCTION benchmark.fn_update_user(
    p_id  TEXT,
    p_bio TEXT DEFAULT NULL
) RETURNS TABLE(
    succeeded      BOOLEAN,
    state_changed  BOOLEAN,
    error_class    TEXT,
    status_detail  TEXT,
    http_status    SMALLINT,
    message        TEXT,
    entity_id      UUID,
    entity_type    TEXT,
    entity         JSONB,
    updated_fields TEXT[],
    cascade        JSONB,
    error_detail   JSONB,
    metadata       JSONB
) AS $$
DECLARE
    v_pk      INT;
    v_uuid    UUID;
    v_data    JSONB;
    v_changed BOOLEAN;
BEGIN
    SELECT pk_user, id INTO v_pk, v_uuid
    FROM benchmark.tb_user
    WHERE id = p_id::UUID;

    IF v_pk IS NULL THEN
        RETURN QUERY SELECT * FROM fraiseql.mutation_err('not_found', 'User not found');
        RETURN;
    END IF;

    v_changed := (SELECT bio FROM benchmark.tb_user WHERE pk_user = v_pk)
                 IS DISTINCT FROM p_bio;

    IF v_changed THEN
        UPDATE benchmark.tb_user
        SET bio = p_bio, updated_at = NOW()
        WHERE pk_user = v_pk;
    END IF;

    SELECT vu.data INTO v_data FROM benchmark.v_user vu WHERE vu._pk = v_pk;

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(
        v_data, v_uuid, 'User', v_changed,
        CASE WHEN v_changed THEN ARRAY['bio']::TEXT[] ELSE ARRAY[]::TEXT[] END
    );
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_update_user(TEXT, TEXT) TO PUBLIC;

-- ============================================================================
-- fn_create_post: Insert a new post and return the created post as JSONB
-- ============================================================================

DROP FUNCTION IF EXISTS benchmark.fn_create_post(JSONB, JSONB, JSONB, JSONB);
DROP FUNCTION IF EXISTS benchmark.fn_create_post(TEXT, TEXT, TEXT, TEXT);

CREATE FUNCTION benchmark.fn_create_post(
    p_title     TEXT,
    p_content   TEXT,
    p_author_id TEXT,
    p_published TEXT DEFAULT 'false'
) RETURNS TABLE(
    succeeded      BOOLEAN,
    state_changed  BOOLEAN,
    error_class    TEXT,
    status_detail  TEXT,
    http_status    SMALLINT,
    message        TEXT,
    entity_id      UUID,
    entity_type    TEXT,
    entity         JSONB,
    updated_fields TEXT[],
    cascade        JSONB,
    error_detail   JSONB,
    metadata       JSONB
) AS $$
DECLARE
    v_author_pk INT;
    v_post_pk   INT;
    v_post_id   UUID;
    v_slug      TEXT;
    v_data      JSONB;
BEGIN
    SELECT pk_user INTO v_author_pk
    FROM benchmark.tb_user
    WHERE id = p_author_id::UUID;

    IF v_author_pk IS NULL THEN
        RETURN QUERY SELECT * FROM fraiseql.mutation_err('not_found', 'Author not found');
        RETURN;
    END IF;

    v_post_id := gen_random_uuid();
    v_slug := lower(regexp_replace(p_title, '[^a-zA-Z0-9]+', '-', 'g'))
              || '-' || substring(v_post_id::TEXT, 1, 8);

    INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published)
    VALUES (v_post_id, v_slug, p_title, p_content, v_author_pk, p_published::BOOLEAN)
    RETURNING pk_post INTO v_post_pk;

    SELECT vp.data INTO v_data FROM benchmark.v_post vp WHERE vp._pk = v_post_pk;

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(v_data, v_post_id, 'Post');
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_post(TEXT, TEXT, TEXT, TEXT) TO PUBLIC;
