-- Install required PostgreSQL extensions for benchmarking
-- jsonb_ivm: Incremental View Maintenance for JSONB
-- pg_tview: Table Views extension
-- pg_stat_statements: Query performance monitoring
-- pg_buffercache: Buffer cache monitoring

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_buffercache";

-- Note: jsonb_ivm and pg_tview would be installed separately
-- as they are external extensions that need to be compiled
-- For now, we'll simulate their functionality with standard PostgreSQL features

-- Create benchmark schema
CREATE SCHEMA IF NOT EXISTS benchmark;
GRANT USAGE ON SCHEMA benchmark TO benchmark;
GRANT ALL PRIVILEGES ON SCHEMA benchmark TO benchmark;

-- Set search path for benchmark operations
SET search_path TO benchmark, public;