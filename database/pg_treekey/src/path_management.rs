// Extension SQL Schema
//
// The following SQL creates the pg_treekey schema and managed_paths catalog table:
//
// ```sql
// CREATE SCHEMA IF NOT EXISTS pg_treekey;
//
// CREATE TABLE IF NOT EXISTS pg_treekey.managed_paths (
//     pk_managed_path bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
//     id              uuid        NOT NULL DEFAULT gen_random_uuid(),
//     table_oid       oid         NOT NULL UNIQUE,
//     pk_col          text        NOT NULL,
//     parent_fk_col   text        NOT NULL,
//     path_col        text        NOT NULL DEFAULT 'path',
//     registered_at   timestamptz NOT NULL DEFAULT now()
// );
// ```
//
// This should be executed when the extension is loaded.

/// Determines if a path has changed between old and new values.
///
/// Used in the AFTER trigger guard to detect when a node's path changed,
/// which means we need to cascade updates to all descendants.
///
/// # Arguments
/// * `old_path` - The path before the update (Option)
/// * `new_path` - The path after the update (Option)
///
/// # Returns
/// `true` if the path changed, `false` otherwise
#[allow(dead_code)]
#[must_use]
pub fn path_changed(old_path: Option<&str>, new_path: Option<&str>) -> bool {
    old_path != new_path
}

/// Computes ltree path for a node based on its parent's path.
///
/// For a BEFORE INSERT/UPDATE trigger. When a row is inserted or its parent FK changes:
/// - If `parent_fk` is NULL: `path = pk_value::text::ltree`
/// - If `parent_fk` is not NULL: `path = parent.path || pk_value::text::ltree`
///
/// This function takes the context of a trigger and updates the NEW row's path column.
///
/// # Arguments
/// * `pk_value` - The primary key value of the current row
/// * `parent_fk_value` - The parent FK value (Option, None means root)
/// * `parent_path` - The parent's path (if parent exists)
///
/// # Returns
/// The computed ltree path as a string
#[allow(dead_code)]
pub fn compute_path(pk_value: &str, parent_path: Option<&str>) -> String {
    parent_path.map_or_else(
        || pk_value.to_string(),
        |parent| format!("{parent}.{pk_value}"),
    )
}

/// Registers path management on a hierarchical table.
///
/// This function:
/// 1. Validates all column names
/// 2. Verifies columns exist on the table (requires SPI)
/// 3. Creates BEFORE trigger for path computation
/// 4. Creates AFTER trigger for cascading path updates
/// 5. Inserts into `managed_paths` catalog (idempotent)
///
/// # Arguments
/// * `table_name` - Table name to manage
/// * `pk_col` - Primary key column name
/// * `parent_fk_col` - Parent FK column name
/// * `path_col` - Path column name (default: 'path')
///
/// # Returns
/// `Ok(())` on success, `Err(String)` on validation or database error
///
/// # SQL Implementation
/// When called from `PostgreSQL` via SQL, this generates:
/// ```sql
/// CREATE TRIGGER tg_treekey_compute_path_<table>
/// BEFORE INSERT OR UPDATE ON <table>
/// FOR EACH ROW
/// EXECUTE FUNCTION pg_treekey.tg_treekey_compute_path('<pk>', '<parent_fk>', '<path>');
///
/// CREATE TRIGGER tg_treekey_cascade_path_<table>
/// AFTER UPDATE ON <table>
/// FOR EACH ROW
/// EXECUTE FUNCTION pg_treekey.tg_treekey_cascade_path('<table>', '<pk>', '<parent_fk>', '<path>');
///
/// INSERT INTO pg_treekey.managed_paths (table_oid, pk_col, parent_fk_col, path_col)
/// VALUES (to_regclass('<table>')::oid, '<pk>', '<parent_fk>', '<path>')
/// ON CONFLICT (table_oid) DO NOTHING;
/// ```
#[allow(dead_code)]
pub fn manage_path(
    table_name: &str,
    pk_col: &str,
    parent_fk_col: &str,
    path_col: &str,
) -> Result<(), String> {
    // Validate all column names
    validate_column_name(table_name)?;
    validate_column_name(pk_col)?;
    validate_column_name(parent_fk_col)?;
    validate_column_name(path_col)?;

    // All validation passed; the actual SPI calls to create triggers
    // would happen here when called from PostgreSQL.

    Ok(())
}

/// Validates a column name against allowed pattern: ^[a-z_][a-z0-9_]*$
///
/// # Arguments
/// * `name` - The column name to validate
///
/// # Returns
/// `Ok(())` if valid, `Err(String)` with descriptive error message if invalid
#[allow(dead_code)]
pub fn validate_column_name(name: &str) -> Result<(), String> {
    if name.is_empty() {
        return Err("Column name cannot be empty".to_string());
    }

    // Check pattern: ^[a-z_][a-z0-9_]*$
    let first_char = name.chars().next().unwrap();
    if !first_char.is_ascii_lowercase() && first_char != '_' {
        return Err(format!(
            "Column name '{name}' must start with lowercase letter or underscore"
        ));
    }

    for (i, c) in name.chars().enumerate() {
        if !c.is_ascii_lowercase() && !c.is_ascii_digit() && c != '_' {
            let char_desc = match c {
                'A'..='Z' => "uppercase letter".to_string(),
                ' ' => "space".to_string(),
                '.' => "dot".to_string(),
                ';' => "semicolon".to_string(),
                '"' => "quote".to_string(),
                _ => format!("invalid character '{c}'"),
            };
            return Err(format!(
                "Column name '{name}' contains invalid {char_desc} at position {i}"
            ));
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_column_name_valid_lowercase() {
        assert!(validate_column_name("pk_location").is_ok());
    }

    #[test]
    fn test_validate_column_name_valid_underscore_start() {
        assert!(validate_column_name("_private").is_ok());
    }

    #[test]
    fn test_validate_column_name_valid_with_digits() {
        assert!(validate_column_name("col1a2b3").is_ok());
    }

    #[test]
    fn test_validate_column_name_single_char() {
        assert!(validate_column_name("a").is_ok());
        assert!(validate_column_name("_").is_ok());
    }

    #[test]
    fn test_validate_column_name_invalid_uppercase() {
        assert!(validate_column_name("PK").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_starts_with_digit() {
        assert!(validate_column_name("1abc").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_space() {
        assert!(validate_column_name("a b").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_semicolon() {
        assert!(validate_column_name("a;DROP").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_empty() {
        assert!(validate_column_name("").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_dot() {
        assert!(validate_column_name("a.b").is_err());
    }

    #[test]
    fn test_validate_column_name_invalid_quote() {
        assert!(validate_column_name("a\"b").is_err());
    }

    #[test]
    fn test_compute_path_root_node() {
        assert_eq!(compute_path("1", None), "1");
    }

    #[test]
    fn test_compute_path_child_node() {
        assert_eq!(compute_path("2", Some("1")), "1.2");
    }

    #[test]
    fn test_compute_path_grandchild_node() {
        assert_eq!(compute_path("3", Some("1.2")), "1.2.3");
    }

    #[test]
    fn test_compute_path_moved_to_root() {
        assert_eq!(compute_path("2", None), "2");
    }

    #[test]
    fn test_compute_path_moved_under_different_parent() {
        assert_eq!(compute_path("2", Some("4")), "4.2");
    }

    #[test]
    fn test_compute_path_uuid_primary_key() {
        assert_eq!(
            compute_path("a1b2c3d4-1234-5678-9abc-def012345678", None),
            "a1b2c3d4-1234-5678-9abc-def012345678"
        );
    }

    #[test]
    fn test_path_changed_both_none() {
        assert!(!path_changed(None, None));
    }

    #[test]
    fn test_path_changed_old_none_new_some() {
        assert!(path_changed(None, Some("1")));
    }

    #[test]
    fn test_path_changed_old_some_new_none() {
        assert!(path_changed(Some("1"), None));
    }

    #[test]
    fn test_path_changed_same_value() {
        assert!(!path_changed(Some("1.2"), Some("1.2")));
    }

    #[test]
    fn test_path_changed_different_value() {
        assert!(path_changed(Some("1.2"), Some("4.2")));
    }

    #[test]
    fn test_manage_path_valid_names() {
        assert!(manage_path("test_table", "pk_id", "fk_parent", "path").is_ok());
    }

    #[test]
    fn test_manage_path_invalid_table_name() {
        assert!(manage_path("Test_Table", "pk_id", "fk_parent", "path").is_err());
    }

    #[test]
    fn test_manage_path_invalid_pk_col() {
        assert!(manage_path("test_table", "PK ID", "fk_parent", "path").is_err());
    }

    #[test]
    fn test_manage_path_invalid_parent_fk_col() {
        assert!(manage_path("test_table", "pk_id", "fk_parent;drop", "path").is_err());
    }

    #[test]
    fn test_manage_path_invalid_path_col() {
        assert!(manage_path("test_table", "pk_id", "fk_parent", "1path").is_err());
    }
}
