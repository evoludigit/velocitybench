-- Install required PostgreSQL extensions for benchmarking
-- jsonb_ivm: Incremental View Maintenance for JSONB
-- pg_tview: Table Views extension
-- pg_stat_statements: Query performance monitoring
-- pg_buffercache: Buffer cache monitoring

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_buffercache";
CREATE EXTENSION IF NOT EXISTS "pg_prewarm";

-- pg_tviews: automatic JSONB TVIEW materialization with trigger-based cascade sync
-- Provides pg_tviews_create(), pg_tviews_refresh(), and DDL event triggers for tv_* tables
CREATE EXTENSION IF NOT EXISTS pg_tviews;

-- pg_jsonb_delta: efficient JSONB merge, patch, and array operations (Rust, pgrx 0.16.1)
-- Provides jsonb_merge_shallow(), jsonb_smart_patch_nested(), jsonb_array_update_where(), etc.
CREATE EXTENSION IF NOT EXISTS jsonb_delta;

-- Note: jsonb_ivm and pg_tview would be installed separately
-- as they are external extensions that need to be compiled
-- For now, we'll simulate their functionality with standard PostgreSQL features

-- Create benchmark schema
CREATE SCHEMA IF NOT EXISTS benchmark;
GRANT USAGE ON SCHEMA benchmark TO benchmark;
GRANT ALL PRIVILEGES ON SCHEMA benchmark TO benchmark;

-- Set search path for benchmark operations
SET search_path TO benchmark, public;