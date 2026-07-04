-- pg_treekey bootstrap schema
-- This file creates the core extension schema and catalog tables.
-- It is managed by the pg_treekey extension and should not be modified manually.

CREATE SCHEMA IF NOT EXISTS treekey;

CREATE TABLE IF NOT EXISTS treekey.managed_identifiers (
    pk_managed_identifier bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id              uuid         NOT NULL DEFAULT gen_random_uuid(),
    table_oid       oid          NOT NULL,
    slug_col        text         NOT NULL,
    mode            text         NOT NULL DEFAULT 'flat'
                    CHECK (mode IN ('flat', 'hierarchical')),
    template        text,
    parent_fk_col   text,
    scope_template  text,
    level_template  text,
    level_sep       text         NOT NULL DEFAULT '.',
    scope_ref       text,
    dedup           boolean      NOT NULL DEFAULT false,
    dedup_scope_col text,
    registered_at   timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (table_oid, slug_col)
);

CREATE TABLE IF NOT EXISTS treekey.managed_identifier_sources (
    pk_managed_identifier_source bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id                   uuid   NOT NULL DEFAULT gen_random_uuid(),
    fk_managed_identifier bigint NOT NULL
        REFERENCES treekey.managed_identifiers(pk_managed_identifier),
    alias                text   NOT NULL,
    source_oid           oid    NOT NULL,
    local_fk_col         text   NOT NULL,
    remote_pk_col        text   NOT NULL,
    intermediate_alias   text,
    watch_cols           text[],
    UNIQUE (fk_managed_identifier, alias)
);

CREATE TABLE IF NOT EXISTS treekey.managed_paths (
    pk_managed_path    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id                 uuid   NOT NULL DEFAULT gen_random_uuid(),
    table_oid          oid    NOT NULL UNIQUE,
    pk_col             text   NOT NULL,
    parent_fk_col      text   NOT NULL,
    path_col           text   NOT NULL DEFAULT 'path',
    registered_at      timestamptz NOT NULL DEFAULT now()
);

-- Set restrictive permissions on catalog tables
-- Only the extension functions (which run as superuser) can write to these tables
-- Tables are not readable by regular users
REVOKE ALL ON treekey.managed_identifiers FROM PUBLIC;
REVOKE ALL ON treekey.managed_identifier_sources FROM PUBLIC;
REVOKE ALL ON treekey.managed_paths FROM PUBLIC;
