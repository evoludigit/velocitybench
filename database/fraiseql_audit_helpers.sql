-- FraiseQL Audit Helpers
--
-- Provides the production-grade mutation pattern for the fraiseql-tv-audit variant:
--   - tb_mutation_log: append-only audit table with Debezium-style before/after
--   - log_mutation_event(): side-effect logger, reads fraiseql.started_at for duration_ms
--   - build_error_detail(): standardized error object builder
--   - error_detail_not_found(): template for 404-style errors
--
-- Ported and adapted from printoptim_backend 03_functions/030_common/0302_mutation.
-- Differences from printoptim: no tenant_id, no contact_id, no OTel tracing params
-- (not relevant for a single-user benchmark). Duration_ms and Debezium envelope kept
-- as they represent realistic production overhead.

SET search_path TO benchmark, public;

-- ============================================================================
-- Audit log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS benchmark.tb_mutation_log (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    object_type      TEXT        NOT NULL,
    object_id        UUID,
    modification_type TEXT       NOT NULL,  -- INSERT | UPDATE | DELETE | NOOP
    change_status    TEXT        NOT NULL,  -- updated | new | deleted | failed:* | noop
    object_data      JSONB,                 -- Debezium-style {before, after, op, source}
    duration_ms      INTEGER,               -- wall-clock ms from fraiseql.started_at
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_tb_mutation_log_object
    ON benchmark.tb_mutation_log (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_tb_mutation_log_occurred
    ON benchmark.tb_mutation_log (occurred_at DESC);

GRANT INSERT, SELECT ON benchmark.tb_mutation_log TO PUBLIC;
GRANT USAGE, SELECT ON SEQUENCE benchmark.tb_mutation_log_id_seq TO PUBLIC;

-- ============================================================================
-- log_mutation_event: append one audit row, return its id
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.log_mutation_event(
    p_object_type      TEXT,
    p_object_id        UUID,
    p_modification_type TEXT,
    p_change_status    TEXT,
    p_payload_before   JSONB DEFAULT NULL,
    p_payload_after    JSONB DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_fraiseql_started_at TEXT := current_setting('fraiseql.started_at', true);
    v_duration_ms         INTEGER;
    v_debezium_op         TEXT := CASE p_modification_type
                                      WHEN 'INSERT' THEN 'c'
                                      WHEN 'UPDATE' THEN 'u'
                                      WHEN 'DELETE' THEN 'd'
                                      ELSE 'r'
                                  END;
    v_object_data         JSONB;
    v_inserted_id         BIGINT;
BEGIN
    IF v_fraiseql_started_at IS NOT NULL AND v_fraiseql_started_at <> '' THEN
        v_duration_ms := (EXTRACT(EPOCH FROM (
            clock_timestamp() - v_fraiseql_started_at::TIMESTAMPTZ
        )) * 1000)::INTEGER;
    END IF;

    v_object_data := jsonb_build_object(
        'before', p_payload_before,
        'after',  p_payload_after,
        'op',     v_debezium_op,
        'source', jsonb_build_object(
            'table',  p_object_type,
            'schema', 'benchmark',
            'db',     current_database(),
            'ts_ms',  (EXTRACT(EPOCH FROM clock_timestamp()) * 1000)::BIGINT
        )
    );

    INSERT INTO benchmark.tb_mutation_log
        (object_type, object_id, modification_type, change_status, object_data, duration_ms)
    VALUES
        (p_object_type, p_object_id, p_modification_type, p_change_status, v_object_data, v_duration_ms)
    RETURNING id INTO v_inserted_id;

    RETURN v_inserted_id;
END;
$$;

GRANT EXECUTE ON FUNCTION benchmark.log_mutation_event(TEXT, UUID, TEXT, TEXT, JSONB, JSONB) TO PUBLIC;

-- ============================================================================
-- build_error_detail: standardized error object {code, identifier, message, details}
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.build_error_detail(
    p_code       INTEGER,
    p_identifier TEXT,
    p_message    TEXT,
    p_details    JSONB DEFAULT '{}'::JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN jsonb_build_object(
        'code',       p_code,
        'identifier', p_identifier,
        'message',    p_message,
        'details',    COALESCE(p_details, '{}'::JSONB)
    );
END;
$$;

GRANT EXECUTE ON FUNCTION benchmark.build_error_detail(INTEGER, TEXT, TEXT, JSONB) TO PUBLIC;

-- ============================================================================
-- error_detail_not_found: template for 404-style errors
-- ============================================================================

CREATE OR REPLACE FUNCTION benchmark.error_detail_not_found(
    p_resource_type TEXT,
    p_resource_id   TEXT,
    p_message       TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN benchmark.build_error_detail(
        404,
        format('%s_not_found', lower(p_resource_type)),
        COALESCE(p_message, format('%s not found', p_resource_type)),
        jsonb_build_object(
            'resource_type', p_resource_type,
            'resource_id',   p_resource_id,
            'reason',        'not_found_or_access_denied'
        )
    );
END;
$$;

GRANT EXECUTE ON FUNCTION benchmark.error_detail_not_found(TEXT, TEXT, TEXT) TO PUBLIC;
