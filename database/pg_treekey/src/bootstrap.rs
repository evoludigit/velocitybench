/// SQL to initialize the `pg_treekey` extension schema and catalog tables.
///
/// This SQL is executed when the extension is created. It creates:
/// - `pg_treekey` schema for all extension objects
/// - `managed_identifiers` catalog table tracking registered identifier templates
/// - `managed_identifier_sources` catalog table tracking source table references
///
/// # Schema Creation
///
/// ```sql
/// CREATE SCHEMA IF NOT EXISTS pg_treekey;
///
/// CREATE TABLE IF NOT EXISTS treekey.managed_identifiers (
///     pk_managed_identifier bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
///     id              uuid         NOT NULL DEFAULT gen_random_uuid(),
///     table_oid       oid          NOT NULL,
///     slug_col        text         NOT NULL,
///     mode            text         NOT NULL DEFAULT 'flat'
///                     CHECK (mode IN ('flat', 'hierarchical')),
///     template        text,
///     parent_fk_col   text,
///     scope_template  text,
///     level_template  text,
///     level_sep       text         NOT NULL DEFAULT '.',
///     scope_ref       text,
///     dedup           boolean      NOT NULL DEFAULT false,
///     dedup_scope_col text,
///     registered_at   timestamptz  NOT NULL DEFAULT now(),
///     UNIQUE (table_oid, slug_col)
/// );
///
/// CREATE TABLE IF NOT EXISTS treekey.managed_identifier_sources (
///     pk_managed_identifier_source bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
///     id                   uuid   NOT NULL DEFAULT gen_random_uuid(),
///     fk_managed_identifier bigint NOT NULL
///         REFERENCES treekey.managed_identifiers(pk_managed_identifier),
///     alias                text   NOT NULL,
///     source_oid           oid    NOT NULL,
///     local_fk_col         text   NOT NULL,   -- FK column name (without alias prefix)
///     remote_pk_col        text   NOT NULL,
///     intermediate_alias   text,              -- NULL for direct FK; alias name for
///                                             -- chained FK (e.g. 'info' when the
///                                             -- source decl is 'info.fk_col=pk')
///     watch_cols           text[],
///     UNIQUE (fk_managed_identifier, alias)
/// );
/// ```
#[allow(dead_code)]
pub const BOOTSTRAP_SCHEMA: &str = r"
CREATE SCHEMA IF NOT EXISTS pg_treekey;

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
";

/// Describes the structure of the `managed_identifiers` catalog table.
#[allow(dead_code)]
pub struct ManagedIdentifierRecord {
    /// Primary key for this registration
    pub pk_managed_identifier: i64,
    /// Unique ID for this registration
    pub id: String, // uuid
    /// OID of the table being managed
    pub table_oid: u32,
    /// Name of the identifier/slug column
    pub slug_col: String,
    /// Registration mode: 'flat' or 'hierarchical'
    pub mode: String,
    /// Parsed template for identifier generation
    pub template: Option<String>,
    /// Parent FK column (for hierarchical mode)
    pub parent_fk_col: Option<String>,
    /// Template for scope (hierarchical mode)
    pub scope_template: Option<String>,
    /// Template for level (hierarchical mode)
    pub level_template: Option<String>,
    /// Separator for level components (default '.')
    pub level_sep: String,
    /// Reference to scope value for Strip modifier (e.g. 'org.identifier')
    pub scope_ref: Option<String>,
    /// Enable deduplication with numeric suffixes
    pub dedup: bool,
    /// Column to scope deduplication (NULL = table-wide dedup)
    pub dedup_scope_col: Option<String>,
    /// When this registration was created
    pub registered_at: String, // timestamptz
}

/// Describes the structure of the `managed_identifier_sources` catalog table.
#[allow(dead_code)]
pub struct ManagedIdentifierSourceRecord {
    /// Primary key for this source reference
    pub pk_managed_identifier_source: i64,
    /// Unique ID for this source reference
    pub id: String, // uuid
    /// Foreign key to `managed_identifiers`
    pub fk_managed_identifier: i64,
    /// Alias used in template expressions (e.g. 'org', 'model')
    pub alias: String,
    /// OID of the source table
    pub source_oid: u32,
    /// Local FK column name (without alias)
    pub local_fk_col: String,
    /// Remote PK column name on source table
    pub remote_pk_col: String,
    /// Alias for intermediate FK (for chained FKs)
    pub intermediate_alias: Option<String>,
    /// Columns to watch for updates (triggers cascade)
    pub watch_cols: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bootstrap_schema_contains_managed_identifiers() {
        assert!(BOOTSTRAP_SCHEMA.contains("managed_identifiers"));
        assert!(BOOTSTRAP_SCHEMA.contains("slug_col"));
        assert!(BOOTSTRAP_SCHEMA.contains("template"));
    }

    #[test]
    fn test_bootstrap_schema_contains_managed_identifier_sources() {
        assert!(BOOTSTRAP_SCHEMA.contains("managed_identifier_sources"));
        assert!(BOOTSTRAP_SCHEMA.contains("watch_cols"));
        assert!(BOOTSTRAP_SCHEMA.contains("local_fk_col"));
    }

    #[test]
    fn test_bootstrap_schema_has_unique_constraints() {
        assert!(BOOTSTRAP_SCHEMA.contains("UNIQUE (table_oid, slug_col)"));
        assert!(BOOTSTRAP_SCHEMA.contains("UNIQUE (fk_managed_identifier, alias)"));
    }

    #[test]
    fn test_bootstrap_schema_has_foreign_key_constraint() {
        assert!(BOOTSTRAP_SCHEMA.contains("REFERENCES treekey.managed_identifiers"));
    }

    #[test]
    fn test_bootstrap_schema_has_check_constraint() {
        assert!(BOOTSTRAP_SCHEMA.contains("CHECK (mode IN ('flat', 'hierarchical'))"));
    }

    #[test]
    fn test_bootstrap_schema_uses_if_not_exists() {
        assert!(BOOTSTRAP_SCHEMA.contains("IF NOT EXISTS"));
    }

    #[test]
    fn test_bootstrap_schema_has_uuid_defaults() {
        assert!(BOOTSTRAP_SCHEMA.contains("gen_random_uuid()"));
    }

    #[test]
    fn test_bootstrap_schema_has_timestamptz_defaults() {
        assert!(BOOTSTRAP_SCHEMA.contains("DEFAULT now()"));
    }
}
