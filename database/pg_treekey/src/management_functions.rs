//! Management functions for registering identifier and path management on tables.
//!
//! This module provides SQL-callable functions that:
//! 1. Register which columns the extension manages
//! 2. Write configuration to the catalog tables
//! 3. Install trigger functions on target tables

use crate::config_cache;
use crate::path_management::validate_column_name;
use pgrx::prelude::*;

/// Register identifier management on a table column.
///
/// Creates or updates a catalog entry for automatic identifier generation
/// and installs the corresponding trigger on the target table.
///
/// # Parameters
/// * `table_oid` - The table to manage (as regclass, validated by `PostgreSQL`)
/// * `slug_col` - The column name to store the generated identifier
/// * `template` - The identifier template (e.g., `'{name}'`, `'{org.abbr}.{name}'`)
/// * `mode` - Generation mode: `'flat'` or `'hierarchical'`
///
/// # SQL Signature
/// ```sql
/// pg_treekey.register_identifier(
///   table regclass,
///   slug_col text,
///   template text,
///   mode text
/// ) -> void
/// ```
///
/// # Errors
/// Returns a `String` error if:
/// - Column names contain invalid characters
/// - The SPI catalog write fails
#[pg_extern(schema = "treekey")]
pub fn register_identifier(
    table_oid: pgrx::pg_sys::Oid,
    slug_col: &str,
    template: &str,
    mode: &str,
) -> Result<(), String> {
    // Validate inputs
    validate_column_name(slug_col)?;

    let escaped_template = template.replace('\\', "\\\\").replace('\'', "''");
    let insert_sql = format!(
        "INSERT INTO treekey.managed_identifiers (table_oid, slug_col, template, mode) \
         VALUES ({table_oid}::oid, '{slug_col}', '{escaped_template}', '{mode}') \
         ON CONFLICT (table_oid, slug_col) DO NOTHING"
    );

    Spi::run(&insert_sql).map_err(|e| format!("Failed to register identifier: {e}"))?;

    // Get schema and table names from OID
    let schema_table_query = format!(
        "SELECT n.nspname || '.' || c.relname FROM pg_class c \
                 JOIN pg_namespace n ON n.oid = c.relnamespace \
                 WHERE c.oid = {table_oid}"
    );

    let schema_table: Option<String> =
        Spi::get_one(&schema_table_query).map_err(|e| format!("Failed to get table name: {e}"))?;

    let schema_table = schema_table.ok_or("Table OID not found in catalog")?;

    // Create trigger name from slug_col
    // SAFETY: slug_col is validated against ^[a-z_][a-z0-9_]*$ pattern,
    // so it's safe to use in trigger name
    let trigger_name = format!("pg_treekey__{slug_col}__identifier");

    // Install trigger - trigger functions are all in the treekey schema
    let function_name = match mode {
        "flat" => "treekey.tg_identifier_flatmode",
        "hierarchical" => "treekey.tg_identifier_hierarchical",
        _ => "treekey.tg_noop", // Fallback for unexpected modes
    };

    let trigger_sql = format!(
        "CREATE OR REPLACE TRIGGER \"{trigger_name}\" \
         BEFORE INSERT OR UPDATE ON {schema_table} \
         FOR EACH ROW EXECUTE FUNCTION {function_name}()"
    );

    Spi::run(&trigger_sql).map_err(|e| format!("Failed to create trigger: {e}"))?;

    // For hierarchical mode, also install the AFTER trigger that cascades
    // identifier prefix replacements to all descendants when a row's identifier changes.
    if mode == "hierarchical" {
        let cascade_trigger_name = format!("pg_treekey__{slug_col}__identifier_cascade");
        let cascade_trigger_sql = format!(
            "CREATE OR REPLACE TRIGGER \"{cascade_trigger_name}\" \
             AFTER UPDATE ON {schema_table} \
             FOR EACH ROW EXECUTE FUNCTION treekey.tg_cascade_identifier()"
        );
        Spi::run(&cascade_trigger_sql)
            .map_err(|e| format!("Failed to create cascade identifier trigger: {e}"))?;
    }

    Ok(())
}

/// Manage ltree path on a hierarchical table.
///
/// Creates or updates a catalog entry for automatic path computation
/// and installs the corresponding triggers on the target table.
///
/// # Parameters
/// * `table_oid` - The table to manage (as regclass, validated by `PostgreSQL`)
/// * `pk_col` - The primary key column name
/// * `parent_fk_col` - The parent foreign key column name
/// * `path_col` - The path column name (default: 'path')
///
/// # SQL Signature
/// ```sql
/// pg_treekey.manage_path(
///   table regclass,
///   pk_col text,
///   parent_fk_col text,
///   path_col text
/// ) -> void
/// ```
///
/// # Errors
/// Returns a `String` error if:
/// - Column names contain invalid characters
/// - The SPI catalog write fails
#[pg_extern(schema = "treekey")]
pub fn manage_path(
    table_oid: pgrx::pg_sys::Oid,
    pk_col: &str,
    parent_fk_col: &str,
    path_col: &str,
) -> Result<(), String> {
    // Validate inputs
    validate_column_name(pk_col)?;
    validate_column_name(parent_fk_col)?;
    validate_column_name(path_col)?;

    // Write to managed_paths catalog
    let insert_sql = format!(
        "INSERT INTO treekey.managed_paths (table_oid, pk_col, parent_fk_col, path_col) \
         VALUES ({table_oid}::oid, '{pk_col}', '{parent_fk_col}', '{path_col}') \
         ON CONFLICT (table_oid) DO NOTHING"
    );

    Spi::run(&insert_sql).map_err(|e| format!("Failed to manage path: {e}"))?;

    // Get schema and table names from OID
    let schema_table_query = format!(
        "SELECT n.nspname || '.' || c.relname FROM pg_class c \
                 JOIN pg_namespace n ON n.oid = c.relnamespace \
                 WHERE c.oid = {table_oid}"
    );

    let schema_table: Option<String> =
        Spi::get_one(&schema_table_query).map_err(|e| format!("Failed to get table name: {e}"))?;

    let schema_table = schema_table.ok_or("Table OID not found in catalog")?;

    // Create trigger names from path_col
    // SAFETY: path_col is validated against ^[a-z_][a-z0-9_]*$ pattern,
    // so it's safe to use in trigger names
    let compute_trigger_name = format!("pg_treekey__{path_col}__path");
    let cascade_trigger_name = format!("pg_treekey__{path_col}__cascade");

    // Install AFTER INSERT trigger for initial path computation.
    // tg_compute_path uses SPI UPDATE with ::ltree cast (cannot use tuple.set_by_name
    // for ltree columns from a BEFORE trigger — pgrx stores text Datum, ltree expects
    // its own binary varlena format).
    let compute_trigger_sql = format!(
        "CREATE OR REPLACE TRIGGER \"{compute_trigger_name}\" \
         AFTER INSERT ON {schema_table} \
         FOR EACH ROW EXECUTE FUNCTION treekey.tg_compute_path()"
    );

    Spi::run(&compute_trigger_sql).map_err(|e| format!("Failed to create compute trigger: {e}"))?;

    // Install AFTER trigger for cascade updates
    // tg_cascade_path is in treekey schema
    let cascade_trigger_sql = format!(
        "CREATE OR REPLACE TRIGGER \"{cascade_trigger_name}\" \
         AFTER UPDATE ON {schema_table} \
         FOR EACH ROW EXECUTE FUNCTION treekey.tg_cascade_path()"
    );

    Spi::run(&cascade_trigger_sql).map_err(|e| format!("Failed to create cascade trigger: {e}"))?;

    Ok(())
}

/// Reload configuration cache after catalog modifications.
///
/// Marks the configuration cache as dirty, forcing trigger functions
/// to re-read the catalog on next execution.
///
/// Call this after modifying entries in the `managed_identifiers` or
/// `managed_paths` catalog tables to ensure triggers see the updates.
///
/// # SQL Signature
/// ```sql
/// pg_treekey.reload_config() -> void
/// ```
#[pg_extern(schema = "treekey")]
pub fn reload_config() {
    config_cache::mark_dirty();
}

/// No-op trigger function placeholder for testing.
///
/// Used to test trigger installation for unexpected trigger modes.
#[pg_extern(schema = "treekey")]
pub const fn tg_noop() {
    // Placeholder trigger function - does nothing
}
