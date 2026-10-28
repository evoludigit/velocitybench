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

-- pg_jsonb_delta: efficient JSONB merge, patch, and array operations (Rust, pgrx 0.16.1)
-- Provides jsonb_merge_shallow(), jsonb_smart_patch_nested(), jsonb_array_update_where(), etc.
-- Created before pg_tviews, which patches documents with it when it is installed.
CREATE EXTENSION IF NOT EXISTS jsonb_delta;

-- pg_tviews: automatic JSONB TVIEW materialization with trigger-based cascade sync
-- Provides tviews.pg_tviews_create(), tviews.pg_tviews_refresh(), and DDL event triggers
CREATE EXTENSION IF NOT EXISTS pg_tviews;

-- ltree: Tree-like data structure support (required by pg_treekey)
CREATE EXTENSION IF NOT EXISTS ltree;

-- pg_treekey: Tree-key management and path operations (Rust, pgrx 0.17.0)
-- Provides tree path management functions and cascading updates
CREATE EXTENSION IF NOT EXISTS pg_treekey;

-- Note: jsonb_ivm and pg_tview would be installed separately
-- as they are external extensions that need to be compiled
-- For now, we'll simulate their functionality with standard PostgreSQL features

-- Create benchmark schema
CREATE SCHEMA IF NOT EXISTS benchmark;
GRANT USAGE ON SCHEMA benchmark TO benchmark;
GRANT ALL PRIVILEGES ON SCHEMA benchmark TO benchmark;

-- Set search path for benchmark operations
SET search_path TO benchmark, public;