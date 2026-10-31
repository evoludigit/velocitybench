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
    -- One statement for a write. pg_tviews refreshes nothing for an UPDATE that leaves
    -- a TVIEW's source values unchanged, so the no-op guard lives in the WHERE clause,
    -- not in a separate read.
    UPDATE benchmark.tb_user
    SET bio = p_bio, updated_at = NOW()
    WHERE id = p_id::UUID AND bio IS DISTINCT FROM p_bio
    RETURNING pk_user, id INTO v_pk, v_uuid;

    v_changed := FOUND;

    -- No row came back: the user is missing, or its bio already is p_bio.
    IF NOT v_changed THEN
        SELECT pk_user, id INTO v_pk, v_uuid
        FROM benchmark.tb_user
        WHERE id = p_id::UUID;

        IF v_pk IS NULL THEN
            RETURN QUERY SELECT * FROM fraiseql.mutation_err('not_found', 'User not found');
            RETURN;
        END IF;
    END IF;

    SELECT vu.data INTO v_data FROM benchmark.fv_user vu WHERE vu._pk = v_pk;

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

    SELECT vp.data INTO v_data FROM benchmark.fv_post vp WHERE vp._pk = v_post_pk;

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(v_data, v_post_id, 'Post');
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_post(TEXT, TEXT, TEXT, TEXT) TO PUBLIC;

-- ============================================================================
-- fn_create_comment / fn_create_comment_cascade: MC1's write
--
-- Adds a comment to a post: the post's latest-10 comment list changes, which
-- no lookup of the comment by id can show a client. The client generates the
-- comment id, so the benchmark deletes exactly the rows it inserted.
--
-- fn_create_comment returns the comment. fn_create_comment_cascade also
-- returns the cascade: the comment (CREATED) and the post with its latest 10
-- comments (PostFull, UPDATED), read from the command-side views, since
-- pg_tviews refreshes tv_* only when the transaction commits.
-- ============================================================================

DROP FUNCTION IF EXISTS benchmark.fn_insert_comment(TEXT, TEXT, TEXT, TEXT);

CREATE FUNCTION benchmark.fn_insert_comment(
    p_id        TEXT,
    p_post_id   TEXT,
    p_author_id TEXT,
    p_content   TEXT
) RETURNS UUID AS $$
DECLARE
    v_post_pk   INT;
    v_author_pk INT;
BEGIN
    SELECT pk_post INTO v_post_pk FROM benchmark.tb_post WHERE id = p_post_id::UUID;
    SELECT pk_user INTO v_author_pk FROM benchmark.tb_user WHERE id = p_author_id::UUID;
    IF v_post_pk IS NULL OR v_author_pk IS NULL THEN
        RETURN NULL;
    END IF;

    INSERT INTO benchmark.tb_comment (id, fk_post, fk_author, content)
    VALUES (p_id::UUID, v_post_pk, v_author_pk, p_content);
    RETURN p_id::UUID;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS benchmark.fn_create_comment(TEXT, TEXT, TEXT, TEXT);

CREATE FUNCTION benchmark.fn_create_comment(
    p_id        TEXT,
    p_post_id   TEXT,
    p_author_id TEXT,
    p_content   TEXT
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
    v_id UUID;
BEGIN
    v_id := benchmark.fn_insert_comment(p_id, p_post_id, p_author_id, p_content);
    IF v_id IS NULL THEN
        RETURN QUERY SELECT * FROM fraiseql.mutation_err('not_found', 'Post or author not found');
        RETURN;
    END IF;

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(
        (SELECT c.data FROM benchmark.fv_comment c WHERE c.id = v_id), v_id, 'Comment'
    );
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS benchmark.fn_create_comment_cascade(TEXT, TEXT, TEXT, TEXT);

CREATE FUNCTION benchmark.fn_create_comment_cascade(
    p_id        TEXT,
    p_post_id   TEXT,
    p_author_id TEXT,
    p_content   TEXT
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
    v_id UUID;
BEGIN
    v_id := benchmark.fn_insert_comment(p_id, p_post_id, p_author_id, p_content);
    IF v_id IS NULL THEN
        RETURN QUERY SELECT * FROM fraiseql.mutation_err('not_found', 'Post or author not found');
        RETURN;
    END IF;

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(
        p_entity      := (SELECT c.data FROM benchmark.fv_comment c WHERE c.id = v_id),
        p_entity_id   := v_id,
        p_entity_type := 'Comment',
        p_cascade     := fraiseql.build_cascade(
            p_updated := jsonb_build_array(
                fraiseql.cascade_entity('Comment', v_id, 'CREATED', 'fv_comment'),
                fraiseql.cascade_entity('PostFull', p_post_id::UUID, 'UPDATED', 'fv_post_full')
            )
        )
    );
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_comment(TEXT, TEXT, TEXT, TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION benchmark.fn_create_comment_cascade(TEXT, TEXT, TEXT, TEXT) TO PUBLIC;
