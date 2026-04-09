-- FraiseQL Full Mutation Functions (Audit Variant)
--
-- Production-grade mutations used by the fraiseql-tv-audit benchmark variant.
-- Compared to fraiseql_mutations.sql (lean), these add:
--   - before/after JSONB snapshots (read from v_* views)
--   - log_mutation_event() call (writes to tb_mutation_log with Debezium envelope)
--   - cascade data on create (signals which cached queries are invalidated)
--   - structured error details via error_detail_not_found()
--
-- Depends on: fraiseql_audit_helpers.sql

SET search_path TO benchmark, public;

-- ============================================================================
-- fn_update_user_full: update bio, snapshot before/after, log, return v_user
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.fn_update_user_full(
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
DECLARE
    v_pk             INT;
    v_user_id        UUID;
    v_payload_before JSONB;
    v_payload_after  JSONB;
BEGIN
    -- Resolve user → internal pk
    SELECT pk_user, id INTO v_pk, v_user_id
    FROM benchmark.tb_user
    WHERE id = (p_id #>> '{}')::UUID;

    IF v_pk IS NULL THEN
        PERFORM benchmark.log_mutation_event(
            'User', NULL, 'UPDATE', 'failed:not_found'
        );
        RETURN QUERY SELECT
            'failed:not_found'::TEXT,
            'User not found'::TEXT,
            NULL::JSONB,
            'User'::TEXT,
            NULL::JSONB,
            jsonb_build_array(
                benchmark.error_detail_not_found('User', p_id #>> '{}')
            );
        RETURN;
    END IF;

    -- Snapshot before
    SELECT vu.data INTO v_payload_before FROM benchmark.v_user vu WHERE vu._pk = v_pk;

    -- Apply update
    UPDATE benchmark.tb_user
    SET
        bio        = COALESCE(p_bio #>> '{}', bio),
        updated_at = NOW()
    WHERE pk_user = v_pk;

    -- Snapshot after (updated_at is now fresh)
    SELECT vu.data INTO v_payload_after FROM benchmark.v_user vu WHERE vu._pk = v_pk;

    -- Log with before/after
    PERFORM benchmark.log_mutation_event(
        'User', v_user_id, 'UPDATE', 'updated',
        v_payload_before, v_payload_after
    );

    RETURN QUERY SELECT
        'updated'::TEXT,
        NULL::TEXT,
        v_payload_after,
        'User'::TEXT,
        NULL::JSONB,
        NULL::JSONB;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_update_user_full(JSONB, JSONB) TO PUBLIC;

-- ============================================================================
-- fn_create_post_full: insert post, snapshot after, log, cascade-invalidate author
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.fn_create_post_full(
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
    v_post_pk     INT;
    v_post_id     UUID;
    v_slug        TEXT;
    v_payload_after JSONB;
    v_cascade_data  JSONB;
BEGIN
    v_title       := p_title #>> '{}';
    v_content     := p_content #>> '{}';
    v_author_uuid := (p_author_id #>> '{}')::UUID;
    v_published   := (p_published #>> '{}')::BOOLEAN;

    -- Resolve author UUID → internal pk
    SELECT pk_user INTO v_author_pk
    FROM benchmark.tb_user
    WHERE id = v_author_uuid;

    IF v_author_pk IS NULL THEN
        PERFORM benchmark.log_mutation_event(
            'Post', NULL, 'INSERT', 'failed:not_found'
        );
        RETURN QUERY SELECT
            'failed:not_found'::TEXT,
            'Author not found'::TEXT,
            NULL::JSONB,
            'Post'::TEXT,
            NULL::JSONB,
            jsonb_build_array(
                benchmark.error_detail_not_found('User', v_author_uuid::TEXT, 'Author not found')
            );
        RETURN;
    END IF;

    -- Generate unique slug from title
    v_post_id := gen_random_uuid();
    v_slug := lower(regexp_replace(v_title, '[^a-zA-Z0-9]+', '-', 'g'))
              || '-' || substring(v_post_id::TEXT, 1, 8);

    -- Insert
    INSERT INTO benchmark.tb_post (id, identifier, title, content, fk_author, published)
    VALUES (v_post_id, v_slug, v_title, v_content, v_author_pk, v_published)
    RETURNING pk_post INTO v_post_pk;

    -- Snapshot after (reads v_post which has author embedded)
    SELECT vp.data INTO v_payload_after FROM benchmark.v_post vp WHERE vp._pk = v_post_pk;

    -- Cascade: author's post list is now stale
    v_cascade_data := jsonb_build_object(
        'invalidate', jsonb_build_array(
            jsonb_build_object('type', 'User', 'id', v_author_uuid::TEXT)
        )
    );

    -- Log with after snapshot and cascade context
    PERFORM benchmark.log_mutation_event(
        'Post', v_post_id, 'INSERT', 'new',
        NULL, v_payload_after
    );

    RETURN QUERY SELECT
        'new'::TEXT,
        NULL::TEXT,
        v_payload_after,
        'Post'::TEXT,
        v_cascade_data,
        NULL::JSONB;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION benchmark.fn_create_post_full(JSONB, JSONB, JSONB, JSONB) TO PUBLIC;
