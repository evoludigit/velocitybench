//! Trigger functions for automatic identifier and path management.
//!
//! This module implements the actual `PostgreSQL` trigger functions that run
//! on each row INSERT/UPDATE to:
//! 1. Generate identifiers based on templates
//! 2. Compute ltree paths from parent chains
//! 3. Cascade path and identifier updates to descendants

#![allow(unsafe_code)] // Required for tuple manipulation in triggers
#![allow(clippy::unnecessary_wraps)] // Result wrapper required by pg_trigger API

use pgrx::prelude::*;
use std::cell::Cell;
use std::collections::HashMap;
use std::num::NonZeroUsize;

// Recursion guard for cascade triggers.
// When true:
//  - tg_identifier_hierarchical skips recomputation (lets cascade value pass through)
//  - tg_cascade_identifier and tg_cascade_path skip recursive cascading
thread_local! {
    static IN_CASCADE: Cell<bool> = const { Cell::new(false) };
}

/// Collect (alias → [col, ...]) from a slice of template tokens.
///
/// Used to determine which source columns need to be fetched before
/// evaluating a template.
fn collect_alias_cols(tokens: &[crate::flat_identifiers::Token]) -> HashMap<String, Vec<String>> {
    let mut alias_cols: HashMap<String, Vec<String>> = HashMap::new();
    for token in tokens {
        if let crate::flat_identifiers::Token::Expr { alias, column, .. } = token {
            let cols = alias_cols.entry(alias.clone()).or_default();
            if !cols.contains(column) {
                cols.push(column.clone());
            }
        }
    }
    alias_cols
}

/// Resolve source values for a pg_treekey registration from the NEW trigger tuple.
///
/// Handles:
/// - `self` alias: columns read directly from the NEW tuple
/// - FK aliases: FK value fetched from the NEW tuple, then the remote row is queried
///
/// Returns a map keyed by `(alias, column)` with `Option<String>` values
/// (None if the column is NULL or FK is NULL).
fn resolve_sources_for_registration(
    pk_reg: i64,
    tuple: &PgHeapTuple<'_, AllocatedByRust>,
    raw_htup: *mut pg_sys::HeapTupleData,
    raw_tupdesc: pg_sys::TupleDesc,
    alias_cols: &HashMap<String, Vec<String>>,
) -> HashMap<(String, String), Option<String>> {
    let mut values: HashMap<(String, String), Option<String>> = HashMap::new();

    // Handle 'self' alias: read columns directly from the NEW tuple
    if let Some(self_cols) = alias_cols.get("self") {
        for col_name in self_cols {
            // SAFETY: raw_htup and raw_tupdesc are valid for the duration of the trigger
            let val =
                unsafe { get_self_col_text(tuple, col_name, raw_htup, raw_tupdesc) };
            values.insert(("self".to_string(), col_name.clone()), val);
        }
    }

    // Handle FK aliases: query managed_identifier_sources for this registration
    let sources_count: i64 = Spi::get_one::<i64>(&format!(
        "SELECT COUNT(*) FROM treekey.managed_identifier_sources \
         WHERE fk_managed_identifier = {pk_reg}"
    ))
    .unwrap_or(Some(0))
    .unwrap_or(0);

    for i in 0..sources_count {
        let alias: String = match Spi::get_one::<String>(&format!(
            "SELECT alias FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} \
             ORDER BY pk_managed_identifier_source LIMIT 1 OFFSET {i}"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        if alias == "self" {
            continue;
        }

        let Some(cols_needed) = alias_cols.get(&alias).cloned() else {
            continue;
        };

        let local_fk_col: String = match Spi::get_one::<String>(&format!(
            "SELECT local_fk_col FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        let remote_pk_col: String = match Spi::get_one::<String>(&format!(
            "SELECT remote_pk_col FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        let source_oid_raw: i32 = match Spi::get_one::<i32>(&format!(
            "SELECT source_oid::int FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };
        let source_oid = pg_sys::Oid::from(source_oid_raw as u32);

        // Get FK value from the NEW tuple (supports BIGINT and INTEGER FK columns)
        let fk_val_i64: Option<i64> = tuple.get_by_name::<i64>(&local_fk_col).ok().flatten();
        let fk_val = fk_val_i64.or_else(|| {
            tuple
                .get_by_name::<i32>(&local_fk_col)
                .ok()
                .flatten()
                .map(i64::from)
        });

        if let Some(fk_val) = fk_val {
            let source_table: String = match Spi::get_one::<String>(&format!(
                "SELECT n.nspname || '.' || c.relname \
                 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace \
                 WHERE c.oid = {source_oid}"
            )) {
                Ok(Some(v)) => v,
                _ => continue,
            };

            for col_name in &cols_needed {
                let val: Option<String> = Spi::get_one::<String>(&format!(
                    "SELECT {col_name}::text FROM {source_table} \
                     WHERE {remote_pk_col} = {fk_val} LIMIT 1"
                ))
                .ok()
                .flatten();
                values.insert((alias.clone(), col_name.clone()), val);
            }
        } else {
            // FK is NULL → None for all needed columns (enables optional elision)
            for col_name in &cols_needed {
                values.insert((alias.clone(), col_name.clone()), None);
            }
        }
    }

    values
}

/// Get the text representation of a column value using PostgreSQL's type output function.
///
/// This handles any column type (TEXT, VARCHAR, INET, MACADDR, etc.) by
/// calling PostgreSQL's registered output function for the column's type OID.
///
/// # Safety
/// - `htup` must be a valid, non-null pointer to a `HeapTupleData`
/// - `tupdesc` must be a valid, non-null pointer to the corresponding `TupleDescData`
/// - `attno` must be a valid 1-based attribute number within `tupdesc`
/// - `typoid` must be the correct type OID for the column at `attno`
unsafe fn get_datum_as_text(
    htup: *mut pg_sys::HeapTupleData,
    tupdesc: pg_sys::TupleDesc,
    attno: NonZeroUsize,
    typoid: pg_sys::Oid,
) -> Option<String> {
    // SAFETY: caller asserts htup, tupdesc, and attno are valid
    let datum = pgrx::heap_getattr_raw(htup, attno, tupdesc)?;

    // Resolve the type's output function OID
    let mut typoutput = pg_sys::InvalidOid;
    let mut typisvarlena = false;
    // SAFETY: typoid is a valid PostgreSQL type OID
    pg_sys::getTypeOutputInfo(typoid, &mut typoutput, &mut typisvarlena);

    if typoutput == pg_sys::InvalidOid {
        return None;
    }

    // SAFETY: OidOutputFunctionCall returns a palloc'd CStr for any valid type
    let cstr = pg_sys::OidOutputFunctionCall(typoutput, datum);
    Some(
        // SAFETY: OidOutputFunctionCall returns a valid, null-terminated C string
        std::ffi::CStr::from_ptr(cstr)
            .to_string_lossy()
            .into_owned(),
    )
}

/// Get a column value from the NEW trigger tuple as a String.
///
/// Tries the fast `get_by_name::<String>` path first (works for TEXT/VARCHAR).
/// Falls back to the type-generic datum→text conversion for INET, MACADDR, etc.
///
/// Returns `None` if the column is NULL or does not exist.
unsafe fn get_self_col_text(
    tuple: &PgHeapTuple<'_, AllocatedByRust>,
    col_name: &str,
    raw_htup: *mut pg_sys::HeapTupleData,
    raw_tupdesc: pg_sys::TupleDesc,
) -> Option<String> {
    // Fast path: TEXT, VARCHAR, and other text-compatible types
    if let Ok(v) = tuple.get_by_name::<String>(col_name) {
        return v;
    }
    // Fallback: generic datum → text (handles INET, MACADDR, etc.)
    let Some((attno, attr)) = tuple.get_attribute_by_name(col_name) else {
        return None;
    };
    get_datum_as_text(raw_htup, raw_tupdesc, attno, attr.type_oid().value())
}

/// Trigger function for flat identifier generation.
///
/// Called BEFORE INSERT or UPDATE on tables registered with
/// `register_identifier(..., mode = 'flat')`.
///
/// Reads the template and source registrations from the catalog, collects
/// column values (handling any PostgreSQL type), and writes the rendered
/// identifier to the slug column.
#[pg_trigger]
#[allow(unused_unsafe)] // into_owned() requires unsafe block
pub fn tg_identifier_flatmode<'a>(
    trigger: &'a PgTrigger<'a>,
) -> Result<Option<PgHeapTuple<'a, impl WhoAllocated>>, PgHeapTupleError> {
    // SAFETY: trigger.new() returns the NEW tuple for BEFORE triggers.
    // into_owned() creates an owned Rust-allocated copy we can modify.
    let mut tuple = unsafe {
        trigger
            .new()
            .expect("No NEW tuple found in trigger")
            .into_owned()
    };

    let rel_id = match trigger.relid() {
        Ok(oid) => oid,
        Err(_) => return Ok(Some(tuple)),
    };

    // ── Look up catalog registration ────────────────────────────────────────
    let pk_reg: i64 = match Spi::get_one(&format!(
        "SELECT pk_managed_identifier FROM treekey.managed_identifiers \
         WHERE table_oid = {rel_id}::oid AND mode = 'flat' LIMIT 1"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(Some(tuple)),
    };

    let slug_col: String = match Spi::get_one(&format!(
        "SELECT slug_col FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(Some(tuple)),
    };

    let template_str: String = match Spi::get_one(&format!(
        "SELECT COALESCE(template, '') FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(Some(tuple)),
    };

    // ── Parse template ───────────────────────────────────────────────────────
    let template = match crate::flat_identifiers::parse_template(&template_str) {
        Ok(t) => t,
        Err(_) => return Ok(Some(tuple)),
    };

    // ── Collect (alias, column) pairs required by the template ───────────────
    let mut alias_cols: HashMap<String, Vec<String>> = HashMap::new();
    for token in &template {
        if let crate::flat_identifiers::Token::Expr { alias, column, .. } = token {
            let cols = alias_cols.entry(alias.clone()).or_default();
            if !cols.contains(column) {
                cols.push(column.clone());
            }
        }
    }

    let mut values: HashMap<(String, String), Option<String>> = HashMap::new();

    // ── Handle 'self' alias: fetch from the NEW tuple ────────────────────────
    if let Some(self_cols) = alias_cols.get("self") {
        // Get the raw trigger data for type-generic column access
        let trigger_data = trigger.trigger_data();
        // SAFETY: trigger_data is valid; tg_trigtuple/tg_newtuple are NEW rows
        let (raw_htup, raw_tupdesc) = unsafe {
            let htup = if pgrx::trigger_fired_by_insert(trigger_data.tg_event) {
                trigger_data.tg_trigtuple
            } else {
                trigger_data.tg_newtuple
            };
            let desc = (*trigger_data.tg_relation).rd_att;
            (htup, desc)
        };

        for col_name in self_cols {
            // SAFETY: raw_htup and raw_tupdesc are valid for the duration of the trigger
            let val = unsafe { get_self_col_text(&tuple, col_name, raw_htup, raw_tupdesc) };
            values.insert(("self".to_string(), col_name.clone()), val);
        }
    }

    // ── Handle FK source aliases ─────────────────────────────────────────────
    let sources_count: i64 = Spi::get_one(&format!(
        "SELECT COUNT(*) FROM treekey.managed_identifier_sources \
         WHERE fk_managed_identifier = {pk_reg}"
    ))
    .unwrap_or(Some(0))
    .unwrap_or(0);

    for i in 0..sources_count {
        let alias: String = match Spi::get_one(&format!(
            "SELECT alias FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} \
             ORDER BY pk_managed_identifier_source LIMIT 1 OFFSET {i}"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        // Skip 'self' — handled above
        if alias == "self" {
            continue;
        }

        // Skip aliases not referenced in the template
        let Some(cols_needed) = alias_cols.get(&alias).cloned() else {
            continue;
        };

        let local_fk_col: String = match Spi::get_one(&format!(
            "SELECT local_fk_col FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        let remote_pk_col: String = match Spi::get_one(&format!(
            "SELECT remote_pk_col FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };

        let source_oid_raw: i32 = match Spi::get_one(&format!(
            "SELECT source_oid::int FROM treekey.managed_identifier_sources \
             WHERE fk_managed_identifier = {pk_reg} AND alias = '{alias}' LIMIT 1"
        )) {
            Ok(Some(v)) => v,
            _ => continue,
        };
        let source_oid = pg_sys::Oid::from(source_oid_raw as u32);

        // Get the FK column value from the NEW tuple (supports BIGINT and INTEGER FKs)
        let fk_val_i64: Option<i64> = tuple.get_by_name::<i64>(&local_fk_col).ok().flatten();
        let fk_val_i32: Option<i64> = if fk_val_i64.is_none() {
            tuple
                .get_by_name::<i32>(&local_fk_col)
                .ok()
                .flatten()
                .map(i64::from)
        } else {
            None
        };
        let fk_val = fk_val_i64.or(fk_val_i32);

        if let Some(fk_val) = fk_val {
            // Resolve source table name from OID
            let source_table: String = match Spi::get_one::<String>(&format!(
                "SELECT n.nspname || '.' || c.relname \
                 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace \
                 WHERE c.oid = {source_oid}"
            )) {
                Ok(Some(v)) => v,
                _ => continue,
            };

            // Fetch each needed column with ::text cast (handles any type, e.g. INET)
            for col_name in &cols_needed {
                let val: Option<String> = Spi::get_one::<String>(&format!(
                    "SELECT {col_name}::text \
                     FROM {source_table} \
                     WHERE {remote_pk_col} = {fk_val} LIMIT 1"
                ))
                .ok()
                .flatten();
                values.insert((alias.clone(), col_name.clone()), val);
            }
        } else {
            // FK is NULL → insert explicit None for each needed column so the
            // template's optional elision (`?`) works correctly
            for col_name in &cols_needed {
                values.insert((alias.clone(), col_name.clone()), None);
            }
        }
    }

    // ── Read dedup settings ──────────────────────────────────────────────────
    let dedup: bool = Spi::get_one::<bool>(&format!(
        "SELECT dedup FROM treekey.managed_identifiers WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or(false);

    // ── Build taken list for dedup ───────────────────────────────────────────
    // Query existing identifiers in the same dedup scope so identifier_next()
    // can assign the correct #N suffix without hitting the UNIQUE constraint.
    let taken: Vec<String> = if dedup {
        let dedup_scope_col: Option<String> = Spi::get_one::<String>(&format!(
            "SELECT dedup_scope_col FROM treekey.managed_identifiers \
             WHERE pk_managed_identifier = {pk_reg}"
        ))
        .ok()
        .flatten();

        let table_name: String = Spi::get_one::<String>(&format!(
            "SELECT n.nspname || '.' || c.relname \
             FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace \
             WHERE c.oid = {rel_id}"
        ))
        .ok()
        .flatten()
        .unwrap_or_default();

        if table_name.is_empty() {
            Vec::new()
        } else {
            // Build scope filter: restricts taken list to the same FK group
            let scope_filter = if let Some(ref scope_col) = dedup_scope_col {
                let scope_val_i64: Option<i64> =
                    tuple.get_by_name::<i64>(scope_col).ok().flatten();
                let scope_val_i32: Option<i64> = if scope_val_i64.is_none() {
                    tuple
                        .get_by_name::<i32>(scope_col)
                        .ok()
                        .flatten()
                        .map(i64::from)
                } else {
                    None
                };
                scope_val_i64
                    .or(scope_val_i32)
                    .map(|v| format!("AND {scope_col} = {v}"))
                    .unwrap_or_default()
            } else {
                String::new()
            };

            // On UPDATE: exclude the old identifier so we don't dedup against ourselves
            let is_update = unsafe {
                pgrx::trigger_fired_by_update(trigger.trigger_data().tg_event)
            };
            let exclude_filter = if is_update {
                let old_id: Option<String> = unsafe {
                    trigger
                        .old()
                        .and_then(|old| old.get_by_name::<String>(&slug_col).ok().flatten())
                };
                old_id
                    .map(|id| {
                        let escaped = id.replace('\'', "''");
                        format!("AND {slug_col} != '{escaped}'")
                    })
                    .unwrap_or_default()
            } else {
                String::new()
            };

            let query = format!(
                "SELECT COALESCE(ARRAY_AGG({slug_col}), ARRAY[]::text[]) \
                 FROM {table_name} WHERE 1=1 {scope_filter} {exclude_filter}"
            );

            Spi::get_one::<Vec<String>>(&query)
                .ok()
                .flatten()
                .unwrap_or_default()
        }
    } else {
        Vec::new()
    };

    // ── Evaluate and write identifier ────────────────────────────────────────
    // dedup_scope_col is None here because we already pre-filtered `taken` by
    // scope in the SQL query above; passing it would cause evaluate_identifier
    // to look up self.<scope_col> in `values`, which is not present.
    let reg = crate::flat_identifiers::IdentifierRegistration {
        slug_col: slug_col.clone(),
        mode: "flat".to_string(),
        template,
        sources: Vec::new(),
        dedup,
        dedup_scope_col: None,
        scope_ref: None,
        parent_fk_col: None,
        scope_template: None,
        level_template: None,
        level_sep: None,
    };

    let taken_refs: Vec<&str> = taken.iter().map(String::as_str).collect();
    let identifier =
        match crate::flat_identifiers::evaluate_identifier(&reg, &values, None, &taken_refs) {
            Ok(id) => id,
            Err(_) => return Ok(Some(tuple)),
        };

    let _ = tuple.set_by_name(&slug_col, identifier);
    Ok(Some(tuple))
}

/// Trigger function for hierarchical identifier generation.
///
/// Called BEFORE INSERT or UPDATE on tables registered with
/// `register_identifier(..., mode = 'hierarchical')`.
///
/// For root nodes (parent FK is NULL):
///   `identifier = scope_template_value + '|' + level_template_value`
///
/// For child nodes (parent FK is not NULL):
///   `identifier = parent.identifier + level_sep + level_template_value`
///
/// When `IN_CASCADE` is true (a cascade update is in progress), the trigger
/// is skipped so the cascade's directly-set value passes through unchanged.
#[pg_trigger]
#[allow(unused_unsafe)] // into_owned() requires unsafe block, but clippy thinks it doesn't
pub fn tg_identifier_hierarchical<'a>(
    trigger: &'a PgTrigger<'a>,
) -> Result<Option<PgHeapTuple<'a, impl WhoAllocated>>, PgHeapTupleError> {
    // Skip recomputation when a cascade is writing directly to slug_col.
    // This lets the cascade's prefix-replaced value pass through unchanged.
    if IN_CASCADE.get() {
        let tuple = unsafe {
            trigger
                .new()
                .expect("No NEW tuple found in trigger")
                .into_owned()
        };
        return Ok(Some(tuple));
    }

    // SAFETY: trigger.new() returns the NEW tuple for BEFORE triggers.
    // into_owned() creates an owned copy allocated by Rust that we can modify.
    let mut tuple = unsafe {
        trigger
            .new()
            .expect("No NEW tuple found in trigger")
            .into_owned()
    };

    let rel_id = match trigger.relid() {
        Ok(oid) => oid,
        Err(_) => return Ok(Some(tuple)),
    };

    // ── Catalog lookup ───────────────────────────────────────────────────────
    let pk_reg: i64 = match Spi::get_one::<i64>(&format!(
        "SELECT pk_managed_identifier FROM treekey.managed_identifiers \
         WHERE table_oid = {rel_id}::oid AND mode = 'hierarchical' LIMIT 1"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(Some(tuple)),
    };

    let slug_col: String = match Spi::get_one::<String>(&format!(
        "SELECT slug_col FROM treekey.managed_identifiers WHERE pk_managed_identifier = {pk_reg}"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(Some(tuple)),
    };

    let level_template_str: String = Spi::get_one::<String>(&format!(
        "SELECT COALESCE(level_template, '') FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or_default();

    let scope_template_str: String = Spi::get_one::<String>(&format!(
        "SELECT COALESCE(scope_template, '') FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or_default();

    let parent_fk_col: String = Spi::get_one::<String>(&format!(
        "SELECT COALESCE(parent_fk_col, '') FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or_default();

    let level_sep: String = Spi::get_one::<String>(&format!(
        "SELECT COALESCE(level_sep, '.') FROM treekey.managed_identifiers \
         WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or_else(|| ".".to_string());

    let dedup: bool = Spi::get_one::<bool>(&format!(
        "SELECT dedup FROM treekey.managed_identifiers WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten()
    .unwrap_or(false);

    let dedup_scope_col: Option<String> = Spi::get_one::<String>(&format!(
        "SELECT dedup_scope_col FROM treekey.managed_identifiers WHERE pk_managed_identifier = {pk_reg}"
    ))
    .ok()
    .flatten();

    // ── Parse templates ──────────────────────────────────────────────────────
    let level_template = match crate::flat_identifiers::parse_template(&level_template_str) {
        Ok(t) => t,
        Err(_) => return Ok(Some(tuple)),
    };

    let scope_template = if scope_template_str.is_empty() {
        None
    } else {
        match crate::flat_identifiers::parse_template(&scope_template_str) {
            Ok(t) => Some(t),
            Err(_) => return Ok(Some(tuple)),
        }
    };

    // ── Collect aliases needed across both templates ──────────────────────────
    let mut alias_cols = collect_alias_cols(&level_template);
    if let Some(ref st) = scope_template {
        for (alias, cols) in collect_alias_cols(st) {
            let entry = alias_cols.entry(alias).or_default();
            for col in cols {
                if !entry.contains(&col) {
                    entry.push(col);
                }
            }
        }
    }

    // ── Get raw trigger pointers for type-generic column access ──────────────
    let trigger_data = trigger.trigger_data();
    let (raw_htup, raw_tupdesc) = unsafe {
        let htup = if pgrx::trigger_fired_by_insert(trigger_data.tg_event) {
            trigger_data.tg_trigtuple
        } else {
            trigger_data.tg_newtuple
        };
        let desc = (*trigger_data.tg_relation).rd_att;
        (htup, desc)
    };

    // ── Resolve FK sources → values map ─────────────────────────────────────
    let values = resolve_sources_for_registration(
        pk_reg,
        &tuple,
        raw_htup,
        raw_tupdesc,
        &alias_cols,
    );

    // ── Evaluate level template → level segment ───────────────────────────────
    let level_reg = crate::flat_identifiers::IdentifierRegistration {
        slug_col: slug_col.clone(),
        mode: "hierarchical".to_string(),
        template: level_template,
        sources: Vec::new(),
        dedup: false,
        dedup_scope_col: None,
        scope_ref: None,
        parent_fk_col: None,
        scope_template: None,
        level_template: None,
        level_sep: None,
    };

    let level_segment =
        match crate::flat_identifiers::evaluate_identifier(&level_reg, &values, None, &[]) {
            Ok(s) => s,
            Err(_) => return Ok(Some(tuple)),
        };

    // ── Get parent FK value from the NEW tuple ────────────────────────────────
    let parent_fk_val: Option<i64> = if parent_fk_col.is_empty() {
        None
    } else {
        tuple
            .get_by_name::<i64>(&parent_fk_col)
            .ok()
            .flatten()
            .or_else(|| {
                tuple
                    .get_by_name::<i32>(&parent_fk_col)
                    .ok()
                    .flatten()
                    .map(i64::from)
            })
    };

    // ── Build the identifier from parent chain ────────────────────────────────
    let base_identifier = if let Some(parent_pk) = parent_fk_val {
        // Child node: fetch parent's identifier and prepend it
        let pk_col: String = Spi::get_one::<String>(&format!(
            "SELECT pk_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
        ))
        .ok()
        .flatten()
        .unwrap_or_default();

        if pk_col.is_empty() {
            // manage_path not registered for this table — fall back to just level segment
            level_segment.clone()
        } else {
            let table_name: String = match Spi::get_one::<String>(&format!(
                "SELECT n.nspname || '.' || c.relname FROM pg_class c \
                 JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.oid = {rel_id}"
            )) {
                Ok(Some(v)) => v,
                _ => return Ok(Some(tuple)),
            };

            let parent_slug: Option<String> = Spi::get_one::<String>(&format!(
                "SELECT {slug_col} FROM {table_name} WHERE {pk_col} = {parent_pk} LIMIT 1"
            ))
            .ok()
            .flatten();

            match parent_slug {
                Some(pid) => format!("{pid}{level_sep}{level_segment}"),
                None => level_segment.clone(),
            }
        }
    } else {
        // Root node: evaluate scope template and prepend it
        if let Some(scope_tmpl) = scope_template {
            let scope_reg = crate::flat_identifiers::IdentifierRegistration {
                slug_col: slug_col.clone(),
                mode: "hierarchical".to_string(),
                template: scope_tmpl,
                sources: Vec::new(),
                dedup: false,
                dedup_scope_col: None,
                scope_ref: None,
                parent_fk_col: None,
                scope_template: None,
                level_template: None,
                level_sep: None,
            };

            match crate::flat_identifiers::evaluate_identifier(&scope_reg, &values, None, &[]) {
                Ok(scope_prefix) => format!("{scope_prefix}|{level_segment}"),
                Err(_) => level_segment.clone(),
            }
        } else {
            level_segment.clone()
        }
    };

    // ── Dedup: resolve unique identifier if dedup is enabled ─────────────────
    let identifier = if dedup {
        // Build taken list scoped to the same parent group
        let table_name: Option<String> = Spi::get_one::<String>(&format!(
            "SELECT n.nspname || '.' || c.relname FROM pg_class c \
             JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.oid = {rel_id}"
        ))
        .ok()
        .flatten();

        let taken: Vec<String> = if let Some(ref tname) = table_name {
            // Scope filter: dedup within same parent (dedup_scope_col) if provided
            let scope_filter = if let Some(ref scope_col) = dedup_scope_col {
                let sv_i64: Option<i64> = tuple.get_by_name::<i64>(scope_col).ok().flatten();
                let sv = sv_i64.or_else(|| {
                    tuple
                        .get_by_name::<i32>(scope_col)
                        .ok()
                        .flatten()
                        .map(i64::from)
                });
                sv.map(|v| format!("AND {scope_col} = {v}"))
                    .unwrap_or_default()
            } else {
                String::new()
            };

            // On UPDATE: exclude OLD.identifier so we don't dedup against ourselves
            let is_update =
                unsafe { pgrx::trigger_fired_by_update(trigger.trigger_data().tg_event) };
            let exclude_filter = if is_update {
                let old_id: Option<String> = unsafe {
                    trigger
                        .old()
                        .and_then(|old| old.get_by_name::<String>(&slug_col).ok().flatten())
                };
                old_id
                    .map(|id| {
                        let escaped = id.replace('\'', "''");
                        format!("AND {slug_col} != '{escaped}'")
                    })
                    .unwrap_or_default()
            } else {
                String::new()
            };

            let query = format!(
                "SELECT COALESCE(ARRAY_AGG({slug_col}), ARRAY[]::text[]) \
                 FROM {tname} WHERE 1=1 {scope_filter} {exclude_filter}"
            );

            Spi::get_one::<Vec<String>>(&query)
                .ok()
                .flatten()
                .unwrap_or_default()
        } else {
            Vec::new()
        };

        let taken_refs: Vec<&str> = taken.iter().map(String::as_str).collect();
        crate::identifier_next(&base_identifier, &taken_refs)
    } else {
        base_identifier
    };

    let _ = tuple.set_by_name(&slug_col, identifier);
    Ok(Some(tuple))
}

/// Trigger function for cascading hierarchical identifier updates to descendants.
///
/// Called AFTER UPDATE on tables registered with `register_identifier(..., mode = 'hierarchical')`.
///
/// When a row's identifier changes, updates all descendant identifiers by replacing
/// the old identifier prefix with the new one. Uses the ltree `path` column
/// (from `manage_path`) to find descendants efficiently.
///
/// The `IN_CASCADE` guard suppresses `tg_identifier_hierarchical` recomputation on
/// each descendant during the cascade, so the directly-set prefix-replaced value
/// passes through without being overwritten.
#[pg_trigger]
#[allow(unused_unsafe)] // trigger.old()/new() require unsafe, but clippy may think otherwise
pub fn tg_cascade_identifier<'a>(
    trigger: &'a PgTrigger<'a>,
) -> Result<Option<PgHeapTuple<'a, impl WhoAllocated>>, PgHeapTupleError> {
    if IN_CASCADE.get() {
        return Ok(trigger.new());
    }

    let rel_id = match trigger.relid() {
        Ok(oid) => oid,
        Err(_) => return Ok(trigger.new()),
    };

    let old_tuple = unsafe { trigger.old().expect("No OLD tuple found in trigger") };
    let new_tuple = unsafe { trigger.new().expect("No NEW tuple found in trigger") };

    // ── Get registration ─────────────────────────────────────────────────────
    let pk_reg: i64 = match Spi::get_one::<i64>(&format!(
        "SELECT pk_managed_identifier FROM treekey.managed_identifiers \
         WHERE table_oid = {rel_id}::oid AND mode = 'hierarchical' LIMIT 1"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(trigger.new()),
    };

    let slug_col: String = match Spi::get_one::<String>(&format!(
        "SELECT slug_col FROM treekey.managed_identifiers WHERE pk_managed_identifier = {pk_reg}"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(trigger.new()),
    };

    let old_id: Option<String> = old_tuple.get_by_name(&slug_col).ok().flatten();
    let new_id: Option<String> = new_tuple.get_by_name(&slug_col).ok().flatten();

    if old_id == new_id {
        return Ok(trigger.new());
    }

    let (Some(old_id), Some(new_id)) = (old_id, new_id) else {
        return Ok(trigger.new());
    };

    // ── Get path and pk info from managed_paths ───────────────────────────────
    let pk_col: String = match Spi::get_one::<String>(&format!(
        "SELECT pk_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(trigger.new()), // No path registered — cannot find descendants
    };

    let path_col: String = match Spi::get_one::<String>(&format!(
        "SELECT path_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(trigger.new()),
    };

    let pk_val: i64 = match new_tuple
        .get_by_name::<i64>(&pk_col)
        .ok()
        .flatten()
        .or_else(|| {
            new_tuple
                .get_by_name::<i32>(&pk_col)
                .ok()
                .flatten()
                .map(i64::from)
        }) {
        Some(v) => v,
        None => return Ok(trigger.new()),
    };

    let table_name: String = match Spi::get_one::<String>(&format!(
        "SELECT n.nspname || '.' || c.relname FROM pg_class c \
         JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.oid = {rel_id}"
    )) {
        Ok(Some(v)) => v,
        _ => return Ok(trigger.new()),
    };

    IN_CASCADE.with(|flag| flag.set(true));

    // Replace the old identifier prefix with the new one in all descendants.
    // Uses LEFT() comparison instead of LIKE to avoid wildcard issues with
    // special characters (|, ., ?) in identifiers.
    //
    // substring(slug_col FROM N) is 1-based; old_len+1 starts after the old prefix.
    let old_len = old_id.len() as i64;
    let escaped_new = new_id.replace('\'', "''");
    let escaped_old = old_id.replace('\'', "''");

    let cascade_sql = format!(
        "UPDATE {table_name} \
         SET {slug_col} = '{escaped_new}' || substring({slug_col} FROM {pos}) \
         WHERE {path_col} <@ (SELECT {path_col} FROM {table_name} WHERE {pk_col} = {pk_val}) \
           AND {pk_col} != {pk_val} \
           AND LEFT({slug_col}, {old_len}) = '{escaped_old}'",
        pos = old_len + 1
    );

    let _ = Spi::run(&cascade_sql);

    IN_CASCADE.with(|flag| flag.set(false));

    Ok(trigger.new())
}

/// Trigger function for ltree path computation.
///
/// Called BEFORE INSERT or UPDATE on tables registered with
/// `manage_path(...)`.
///
/// Computes the ltree path from the parent chain:
/// - If `parent_fk` is NULL: path = `pk_value::text`
/// - If `parent_fk` is not NULL: path = `parent_path` || '.' || `pk_value::text`
#[pg_trigger]
pub fn tg_compute_path<'a>(
    trigger: &'a PgTrigger<'a>,
) -> Result<Option<PgHeapTuple<'a, impl WhoAllocated>>, PgHeapTupleError> {
    // AFTER INSERT trigger — uses SPI UPDATE with ::ltree cast.
    //
    // Cannot use tuple.set_by_name() for ltree columns: pgrx stores a text Datum
    // but the column expects an ltree Datum (different varlena binary format).
    // SPI lets PostgreSQL handle the text→ltree cast cleanly.
    let new_tuple = unsafe { trigger.new().expect("No NEW tuple in trigger") };

    let rel_id = match trigger.relid() {
        Ok(oid) => oid,
        Err(_) => return Ok(trigger.new()),
    };

    let pk_col: String = match Spi::get_one::<String>(&format!(
        "SELECT pk_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    let parent_fk_col: String = match Spi::get_one::<String>(&format!(
        "SELECT parent_fk_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    let path_col: String = match Spi::get_one::<String>(&format!(
        "SELECT path_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    let table_name: String = match Spi::get_one::<String>(&format!(
        "SELECT n.nspname || '.' || c.relname FROM pg_class c \
         JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.oid = {rel_id}"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    // Read pk — BIGINT identity column, try i64 first then i32
    let pk_val: i64 = match new_tuple
        .get_by_name::<i64>(&pk_col)
        .ok()
        .flatten()
        .or_else(|| {
            new_tuple
                .get_by_name::<i32>(&pk_col)
                .ok()
                .flatten()
                .map(i64::from)
        }) {
        Some(v) => v,
        None => return Ok(trigger.new()),
    };

    // Read parent FK — optional BIGINT, try i64 first then i32
    let parent_fk_val: Option<i64> = new_tuple
        .get_by_name::<i64>(&parent_fk_col)
        .ok()
        .flatten()
        .or_else(|| {
            new_tuple
                .get_by_name::<i32>(&parent_fk_col)
                .ok()
                .flatten()
                .map(i64::from)
        });

    // Compute path: for root → pk as text; for child → parent_path.pk
    let path = if let Some(parent_fk) = parent_fk_val {
        let parent_path: Option<String> = Spi::get_one::<String>(&format!(
            "SELECT {path_col}::text FROM {table_name} WHERE {pk_col} = {parent_fk} LIMIT 1"
        ))
        .ok()
        .flatten();
        match parent_path {
            Some(pp) => format!("{pp}.{pk_val}"),
            None => pk_val.to_string(),
        }
    } else {
        pk_val.to_string()
    };

    // UPDATE via SPI — PostgreSQL handles the text→ltree cast
    let escaped = path.replace('\'', "''");
    let _ = Spi::run(&format!(
        "UPDATE {table_name} SET {path_col} = '{escaped}'::ltree WHERE {pk_col} = {pk_val}"
    ));

    Ok(trigger.new())
}

/// Trigger function for cascading path updates.
///
/// Called AFTER UPDATE on tables registered with `manage_path(...)`.
///
/// When a row's parent changes, cascades path updates to all descendants
/// using an `IN_CASCADE` guard to prevent infinite recursion.
#[pg_trigger]
#[allow(unused_unsafe)] // into_owned() requires unsafe block, but clippy thinks it doesn't
pub fn tg_cascade_path<'a>(
    trigger: &'a PgTrigger<'a>,
) -> Result<Option<PgHeapTuple<'a, impl WhoAllocated>>, PgHeapTupleError> {
    // Check IN_CASCADE guard - if true, parent cascade already covers descendants
    if IN_CASCADE.get() {
        return Ok(trigger.new());
    }

    // Get the table OID from the trigger context
    let rel_id = match trigger.relid() {
        Ok(oid) => oid,
        Err(_) => return Ok(trigger.new()),
    };

    // Get the old and new tuples
    let old_tuple = unsafe { trigger.old().expect("No OLD tuple found in trigger") };
    let new_tuple = unsafe { trigger.new().expect("No NEW tuple found in trigger") };

    // Query configuration
    let pk_col: String = match Spi::get_one(&format!(
        "SELECT pk_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    let path_col: String = match Spi::get_one(&format!(
        "SELECT path_col FROM treekey.managed_paths WHERE table_oid = {rel_id}::oid LIMIT 1"
    )) {
        Ok(Some(val)) => val,
        _ => return Ok(trigger.new()),
    };

    // Check if path changed
    let old_path: Option<String> = old_tuple.get_by_name(&path_col).ok().flatten();
    let new_path: Option<String> = new_tuple.get_by_name(&path_col).ok().flatten();

    if old_path == new_path {
        return Ok(trigger.new());
    }

    // Path changed - cascade updates to descendants
    if let (Some(old_p), Some(new_p)) = (old_path, new_path) {
        IN_CASCADE.with(|flag| flag.set(true));

        // Get schema and table name
        let table_name: String = match Spi::get_one(&format!(
            "SELECT n.nspname || '.' || c.relname FROM pg_class c \
             JOIN pg_namespace n ON n.oid = c.relnamespace \
             WHERE c.oid = {rel_id}"
        )) {
            Ok(Some(val)) => val,
            _ => {
                IN_CASCADE.with(|flag| flag.set(false));
                return Ok(trigger.new());
            }
        };

        // pk is BIGINT — try i64 first, fall back to i32
        let pk_val: i64 = match new_tuple
            .get_by_name::<i64>(&pk_col)
            .ok()
            .flatten()
            .or_else(|| {
                new_tuple
                    .get_by_name::<i32>(&pk_col)
                    .ok()
                    .flatten()
                    .map(i64::from)
            }) {
            Some(v) => v,
            None => {
                IN_CASCADE.with(|flag| flag.set(false));
                return Ok(trigger.new());
            }
        };

        // Update descendants — fix ::ltree cast (was missing a colon)
        let cascade_sql = format!(
            "UPDATE {table_name} \
             SET {path_col} = regexp_replace({path_col}::text, '^' || '{}', '{}')::ltree \
             WHERE {path_col} <@ '{}'::ltree AND {pk_col} != {pk_val}",
            old_p.replace('\'', "''"),
            new_p.replace('\'', "''"),
            old_p.replace('\'', "''"),
        );

        let _ = Spi::run(&cascade_sql);

        IN_CASCADE.with(|flag| flag.set(false));
    }

    Ok(trigger.new())
}
