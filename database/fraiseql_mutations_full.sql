-- FraiseQL Full Mutation Functions (Audit Variant, v2.2.0 — uses fraiseql helpers)
--
-- Depends on: fraiseql_audit_helpers.sql, fraiseql setup (mutation_ok/mutation_err)

SET search_path TO benchmark, public;

-- ============================================================================
-- fn_update_user_full: update bio, snapshot before/after, log, return fv_user
-- ============================================================================

DROP FUNCTION IF EXISTS benchmark.fn_update_user_full(JSONB, JSONB);
DROP FUNCTION IF EXISTS benchmark.fn_update_user_full(TEXT, TEXT);

CREATE FUNCTION benchmark.fn_update_user_full(
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
    v_pk             INT;
    v_user_id        UUID;
    v_payload_before JSONB;
    v_payload_after  JSONB;
    v_changed        BOOLEAN;
BEGIN
    SELECT pk_user, id INTO v_pk, v_user_id
    FROM benchmark.tb_user
    WHERE id = p_id::UUID;

    IF v_pk IS NULL THEN
        PERFORM benchmark.log_mutation_event('User', NULL, 'UPDATE', 'failed:not_found');
        RETURN QUERY SELECT * FROM fraiseql.mutation_err(
            'not_found', 'User not found',
            jsonb_build_array(benchmark.error_detail_not_found('User', p_id))
        );
        RETURN;
    END IF;

    SELECT vu.data INTO v_payload_before FROM benchmark.fv_user vu WHERE vu._pk = v_pk;

    v_changed := (SELECT bio FROM benchmark.tb_user WHERE pk_user = v_pk)
                 IS DISTINCT FROM p_bio;

    IF v_changed THEN
        UPDATE benchmark.tb_user
        SET bio = p_bio, updated_at = NOW()
        WHERE pk_user = v_pk;
    END IF;

    SELECT vu.data INTO v_payload_after FROM benchmark.fv_user vu WHERE vu._pk = v_pk;

    PERFORM benchmark.log_mutation_event(
        'User', v_user_id, 'UPDATE',
        CASE WHEN v_changed THEN 'updated' ELSE 'noop' END,
        v_payload_before, v_payload_after
    );

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(
        v_payload_after, v_user_id, 'User', v_changed,
        CASE WHEN v_changed THEN ARRAY['bio']::TEXT[] ELSE ARRAY[]::TEXT[] END
    );
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_update_user_full(TEXT, TEXT) TO PUBLIC;

-- ============================================================================
-- fn_create_post_full: insert post, snapshot after, log, cascade-invalidate author
-- ============================================================================

DROP FUNCTION IF EXISTS benchmark.fn_create_post_full(JSONB, JSONB, JSONB, JSONB);
DROP FUNCTION IF EXISTS benchmark.fn_create_post_full(TEXT, TEXT, TEXT, TEXT);

CREATE FUNCTION benchmark.fn_create_post_full(
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
    v_author_uuid   UUID;
    v_author_pk     INT;
    v_post_pk       INT;
    v_post_id       UUID;
    v_slug          TEXT;
    v_payload_after JSONB;
    v_cascade_data  JSONB;
BEGIN
    v_author_uuid := p_author_id::UUID;

    SELECT pk_user INTO v_author_pk
    FROM benchmark.tb_user
    WHERE id = v_author_uuid;

    IF v_author_pk IS NULL THEN
        PERFORM benchmark.log_mutation_event('Post', NULL, 'INSERT', 'failed:not_found');
        RETURN QUERY SELECT * FROM fraiseql.mutation_err(
            'not_found', 'Author not found',
            jsonb_build_array(benchmark.error_detail_not_found('User', p_author_id, 'Author not found'))
        );
        RETURN;
    END IF;

    v_post_id := gen_random_uuid();
    v_slug := lower(regexp_replace(p_title, '[^a-zA-Z0-9]+', '-', 'g'))
              || '-' || substring(v_post_id::TEXT, 1, 8);

    INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published)
    VALUES (v_post_id, v_slug, p_title, p_content, v_author_pk, p_published::BOOLEAN)
    RETURNING pk_post INTO v_post_pk;

    SELECT vp.data INTO v_payload_after FROM benchmark.fv_post vp WHERE vp._pk = v_post_pk;

    v_cascade_data := jsonb_build_object(
        'invalidate', jsonb_build_array(
            jsonb_build_object('type', 'User', 'id', v_author_uuid::TEXT)
        )
    );

    PERFORM benchmark.log_mutation_event(
        'Post', v_post_id, 'INSERT', 'new', NULL, v_payload_after
    );

    RETURN QUERY SELECT * FROM fraiseql.mutation_ok(
        v_payload_after, v_post_id, 'Post', TRUE, NULL, v_cascade_data
    );
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_post_full(TEXT, TEXT, TEXT, TEXT) TO PUBLIC;
