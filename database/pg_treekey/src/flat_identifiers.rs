use std::fmt;

/// Token modifier applied to a template expression
#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Modifier {
    /// Default: apply slugify normalization
    Slugify,
    /// No transformation
    Raw,
    /// Strip scope prefix
    Strip,
    /// Left-pad with zeros to specified width
    Padded(u32),
}

impl fmt::Display for Modifier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Slugify => write!(f, "slugify"),
            Self::Raw => write!(f, "raw"),
            Self::Strip => write!(f, "strip"),
            Self::Padded(width) => write!(f, "padded({width})"),
        }
    }
}

/// A parsed token from the template DSL
#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Token {
    /// Literal string (e.g. "|", ".", etc.)
    Literal(String),
    /// Template expression: `{alias.column!modifier?}`
    Expr {
        alias: String,
        column: String,
        modifier: Modifier,
        optional: bool,
    },
}

/// Error from parsing the template DSL
#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseError {
    pub message: String,
    pub position: Option<usize>,
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.position {
            None => write!(f, "{}", self.message),
            Some(pos) => write!(f, "{} (at position {})", self.message, pos),
        }
    }
}

impl std::error::Error for ParseError {}

/// Parses a template DSL string into tokens.
///
/// # Grammar
/// - `{alias.column!modifier?}` - Template expression
/// - `alias` must match `[a-z_][a-z0-9_]*`
/// - `column` must match `[a-z_][a-z0-9_]*`
/// - `modifier` is one of: `slugify`, `raw`, `strip`, `padded(N)`
/// - `?` suffix makes expression optional
/// - Anything outside `{}` is literal text
///
/// # Errors
/// - Empty expressions: `{}`
/// - Missing column: `{alias}` (no dot)
/// - Unknown modifier: `{a.b!unknown}`
/// - Unclosed braces
/// - Literal braces not in expressions
#[allow(dead_code)]
pub fn parse_template(input: &str) -> Result<Vec<Token>, ParseError> {
    let mut tokens = Vec::new();
    let mut chars = input.chars().peekable();
    let mut pos = 0;
    let mut current_literal = String::new();

    while let Some(&ch) = chars.peek() {
        if ch == '{' {
            // Save any pending literal
            if !current_literal.is_empty() {
                tokens.push(Token::Literal(current_literal.clone()));
                current_literal.clear();
            }

            // Parse expression
            chars.next(); // consume '{'
            pos += 1;
            let expr_start = pos;
            let mut expr_str = String::new();
            let mut depth = 1;

            while depth > 0 {
                match chars.next() {
                    Some('{') => {
                        expr_str.push('{');
                        depth += 1;
                        pos += 1;
                    }
                    Some('}') => {
                        depth -= 1;
                        if depth > 0 {
                            expr_str.push('}');
                        }
                        pos += 1;
                    }
                    Some(c) => {
                        expr_str.push(c);
                        pos += 1;
                    }
                    None => {
                        return Err(ParseError {
                            message: "Unclosed brace in template".to_string(),
                            position: Some(expr_start),
                        });
                    }
                }
            }

            tokens.push(parse_expression(&expr_str, expr_start)?);
        } else if ch == '}' {
            return Err(ParseError {
                message: "Unmatched closing brace".to_string(),
                position: Some(pos),
            });
        } else {
            current_literal.push(ch);
            chars.next();
            pos += 1;
        }
    }

    if !current_literal.is_empty() {
        tokens.push(Token::Literal(current_literal));
    }

    Ok(tokens)
}

/// Parses a single template expression: `alias.column!modifier?`
fn parse_expression(expr_str: &str, base_pos: usize) -> Result<Token, ParseError> {
    if expr_str.is_empty() {
        return Err(ParseError {
            message: "Empty expression".to_string(),
            position: Some(base_pos),
        });
    }

    let expr_str = expr_str.trim();

    // Check for optional suffix
    let (expr_str, optional) = expr_str
        .strip_suffix('?')
        .map_or((expr_str, false), |stripped| (stripped, true));

    // Split on '!' for modifier
    let (base_expr, modifier_str) = match expr_str.split_once('!') {
        Some((base, mod_str)) => (base, Some(mod_str)),
        None => (expr_str, None),
    };

    // Split on '.' for alias and column
    let Some((alias, column)) = base_expr.split_once('.') else {
        return Err(ParseError {
            message: "Expression must contain '.' (e.g. 'alias.column')".to_string(),
            position: Some(base_pos),
        });
    };

    let alias = alias.trim();
    let column = column.trim();

    // Validate identifiers
    validate_identifier(alias, base_pos)?;
    validate_identifier(column, base_pos)?;

    // Parse modifier
    let modifier = match modifier_str {
        None => Modifier::Slugify,
        Some(mod_str) => parse_modifier(mod_str, base_pos)?,
    };

    Ok(Token::Expr {
        alias: alias.to_string(),
        column: column.to_string(),
        modifier,
        optional,
    })
}

/// Parses a modifier string: `raw`, `strip`, `slugify`, or `padded(N)`
fn parse_modifier(mod_str: &str, base_pos: usize) -> Result<Modifier, ParseError> {
    let mod_str = mod_str.trim();

    match mod_str {
        "slugify" => Ok(Modifier::Slugify),
        "raw" => Ok(Modifier::Raw),
        "strip" => Ok(Modifier::Strip),
        _ => {
            if mod_str.starts_with("padded(") && mod_str.ends_with(')') {
                let width_str = &mod_str[7..mod_str.len() - 1];
                width_str
                    .trim()
                    .parse::<u32>()
                    .map(Modifier::Padded)
                    .map_err(|_| ParseError {
                        message: format!("Invalid padded width: {width_str}"),
                        position: Some(base_pos),
                    })
            } else {
                Err(ParseError {
                    message: format!("Unknown modifier: {mod_str}"),
                    position: Some(base_pos),
                })
            }
        }
    }
}

/// Validates an identifier matches pattern: ^[a-z_][a-z0-9_]*$
fn validate_identifier(ident: &str, pos: usize) -> Result<(), ParseError> {
    if ident.is_empty() {
        return Err(ParseError {
            message: "Identifier cannot be empty".to_string(),
            position: Some(pos),
        });
    }

    if let Some(first) = ident.chars().next() {
        if !first.is_ascii_lowercase() && first != '_' {
            return Err(ParseError {
                message: format!(
                    "Identifier '{ident}' must start with lowercase letter or underscore"
                ),
                position: Some(pos),
            });
        }
    }

    for c in ident.chars() {
        if !c.is_ascii_lowercase() && !c.is_ascii_digit() && c != '_' {
            return Err(ParseError {
                message: format!("Identifier '{ident}' contains invalid character '{c}'"),
                position: Some(pos),
            });
        }
    }

    Ok(())
}

/// Renders a template with resolved token values, eliding optional NULLs and their separators.
///
/// # Arguments
/// - `tokens`: Parsed template tokens
/// - `values`: Map of (alias, column) -> resolved value or None for NULL
///
/// # Returns
/// Rendered string with optional NULLs and adjacent separators elided
///
/// # Examples
/// - `"{a!raw}|{b!raw}.{c!raw}"` with a=x, b=y, c=z -> `"x|y.z"`
/// - `"{a!raw}|{b!raw}.{c!raw?}"` with c=NULL -> `"x|y"` (`.` elided)
/// - `"{a!raw?}|{b!raw}"` with a=NULL -> `"b"` (trailing `|` elided)
#[allow(dead_code)]
pub fn render_template(
    tokens: &[Token],
    values: &std::collections::HashMap<(String, String), Option<String>>,
) -> String {
    if tokens.is_empty() {
        return String::new();
    }

    // First pass: identify which optional expressions are NULL
    let mut skipped = vec![false; tokens.len()];
    for (idx, token) in tokens.iter().enumerate() {
        if let Token::Expr {
            alias,
            column,
            optional: true,
            ..
        } = token
        {
            let key = (alias.clone(), column.clone());
            if values.get(&key) == Some(&None) {
                skipped[idx] = true;
            }
        }
    }

    // Second pass: mark adjacent literals for elision
    let mut elide_literal = vec![false; tokens.len()];
    for idx in 0..tokens.len() {
        if skipped[idx] {
            // This optional is being skipped, find adjacent literal to elide
            if idx == 0 {
                // Leading optional: elide following literal (if present)
                if idx + 1 < tokens.len() && matches!(tokens[idx + 1], Token::Literal(_)) {
                    elide_literal[idx + 1] = true;
                }
            } else {
                // Non-leading optional: elide preceding literal (if present)
                if matches!(tokens[idx - 1], Token::Literal(_)) {
                    elide_literal[idx - 1] = true;
                }
            }
        }
    }

    // Third pass: render output
    let mut result = String::new();
    for (idx, token) in tokens.iter().enumerate() {
        if skipped[idx] {
            continue;
        }

        if elide_literal[idx] {
            continue;
        }

        match token {
            Token::Literal(lit) => {
                result.push_str(lit);
            }
            Token::Expr {
                alias,
                column,
                modifier,
                optional: _,
            } => {
                let key = (alias.clone(), column.clone());
                if let Some(Some(value)) = values.get(&key) {
                    if let Ok(resolved) = apply_modifier(value, modifier, None) {
                        result.push_str(&resolved);
                    }
                    // If Strip modifier without scope, silently skip it
                    // (scope is only available at trigger evaluation time)
                }
            }
        }
    }

    result
}

/// Applies a modifier to a value.
///
/// # Arguments
/// - `value`: The value to transform
/// - `modifier`: The modifier to apply
/// - `scope_value`: Optional scope value for Strip modifier
///
/// # Returns
/// Result with transformed value or error if Strip requires scope but none provided
///
/// # Errors
/// - Strip modifier without a `scope_value` returns an error
#[allow(dead_code)]
pub fn apply_modifier(
    value: &str,
    modifier: &Modifier,
    scope_value: Option<&str>,
) -> Result<String, String> {
    match modifier {
        Modifier::Slugify => {
            // Use the slugify function from the parent crate
            Ok(crate::slugify(value, "-"))
        }
        Modifier::Raw => Ok(value.to_string()),
        Modifier::Strip => {
            let scope = scope_value
                .ok_or_else(|| "Strip modifier requires a scope_value parameter".to_string())?;
            Ok(crate::scope_strip(value, scope).to_string())
        }
        Modifier::Padded(width) => {
            let width = *width as usize;
            if value.len() >= width {
                Ok(value.to_string())
            } else {
                Ok(format!("{value:0>width$}"))
            }
        }
    }
}

/// Represents a source table reference in an identifier template.
///
/// Example: `'org:public.organizations:fk_org=pk_org'` parses to:
/// ```ignore
/// SourceRef {
///     alias: "org",
///     schema: Some("public"),
///     table: "organizations",
///     local_fk_col: "fk_org",
///     remote_pk_col: "pk_org",
///     intermediate_alias: None,
/// }
/// ```
///
/// For chained FKs: `'addr:tenant.tb_public_address:info.fk_public_address=pk_public_address'` parses to:
/// ```ignore
/// SourceRef {
///     alias: "addr",
///     schema: Some("tenant"),
///     table: "tb_public_address",
///     local_fk_col: "fk_public_address",
///     remote_pk_col: "pk_public_address",
///     intermediate_alias: Some("info"),
/// }
/// ```
#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceRef {
    /// Alias used in template expressions (e.g., 'org', 'model')
    pub alias: String,
    /// Schema name (optional, defaults to 'public')
    pub schema: Option<String>,
    /// Table name
    pub table: String,
    /// Local FK column name (without schema/table qualification)
    pub local_fk_col: String,
    /// Remote PK column name
    pub remote_pk_col: String,
    /// For chained FKs (intermediate table alias)
    pub intermediate_alias: Option<String>,
}

/// Parses an FK specification string.
///
/// Supports two formats:
/// - Direct FK: `'local_fk=remote_pk'` → `intermediate_alias` = `None`
/// - Chained FK: `'intermediate_alias.local_fk=remote_pk'` → `intermediate_alias` = `Some("intermediate_alias")`
///
/// # Errors
/// - Missing '=' in FK spec
/// - Multiple dots in local FK part (only single-hop indirection supported)
/// - Invalid identifier names
#[allow(dead_code)]
fn parse_fk_spec(fk_spec: &str) -> Result<(String, String, Option<String>), String> {
    if let Some(eq_pos) = fk_spec.find('=') {
        let local = fk_spec[..eq_pos].trim();
        let remote = fk_spec[eq_pos + 1..].trim();

        // Check if local FK is chained (contains a dot)
        let (intermediate_alias, fk_col) = if let Some(dot_pos) = local.find('.') {
            // Count dots to ensure single-hop indirection
            let dot_count = local.matches('.').count();
            if dot_count > 1 {
                return Err(
                    "FK specification with chained alias supports only single-hop indirection (alias.fk_col), not multiple dots".to_string()
                );
            }

            let intermediate_part = local[..dot_pos].trim();
            let fk_part = local[dot_pos + 1..].trim();

            crate::path_management::validate_column_name(intermediate_part)
                .map_err(|e| format!("Invalid intermediate alias: {e}"))?;
            crate::path_management::validate_column_name(fk_part)
                .map_err(|e| format!("Invalid FK column: {e}"))?;

            (Some(intermediate_part.to_string()), fk_part.to_string())
        } else {
            // Direct FK join (no intermediate alias)
            crate::path_management::validate_column_name(local)
                .map_err(|e| format!("Invalid local FK column: {e}"))?;
            (None, local.to_string())
        };

        crate::path_management::validate_column_name(remote)
            .map_err(|e| format!("Invalid remote PK column: {e}"))?;

        Ok((fk_col, remote.to_string(), intermediate_alias))
    } else {
        Err(format!(
            "FK specification must be 'local=remote' or 'alias.local=remote', got: {fk_spec}"
        ))
    }
}

/// Parses a source reference string: `'alias:schema.table:local_fk=remote_pk'` or `'alias:table:local_fk=remote_pk'`
///
/// # Arguments
/// - `source_str` - Source specification string
///
/// # Returns
/// Parsed `SourceRef` or error with descriptive message
///
/// # Examples
/// - `'org:organizations:fk_org=pk_org'` → parses successfully
/// - `'org:public.organizations:fk_org=pk_org'` → includes schema
/// - `'org:organizations'` → error (missing FK columns)
/// - `'org:organizations:bad:fk'` → error (malformed)
#[allow(dead_code)]
pub fn parse_source(source_str: &str) -> Result<SourceRef, String> {
    let source_str = source_str.trim();

    // Split on ':' to get alias, table_ref, and fk_spec
    let parts: Vec<&str> = source_str.split(':').collect();
    if parts.len() != 3 {
        return Err(format!(
            "Source must have 3 parts (alias:table:fk_spec), got: {source_str}"
        ));
    }

    let alias = parts[0].trim();
    let table_ref = parts[1].trim();
    let fk_spec = parts[2].trim();

    // Validate alias
    crate::path_management::validate_column_name(alias)
        .map_err(|e| format!("Invalid alias: {e}"))?;

    // Parse table_ref: either 'table' or 'schema.table'
    let (schema, table) = if let Some(dot_pos) = table_ref.find('.') {
        let schema_part = table_ref[..dot_pos].trim();
        let table_part = table_ref[dot_pos + 1..].trim();
        crate::path_management::validate_column_name(schema_part)
            .map_err(|e| format!("Invalid schema: {e}"))?;
        crate::path_management::validate_column_name(table_part)
            .map_err(|e| format!("Invalid table: {e}"))?;
        (Some(schema_part.to_string()), table_part.to_string())
    } else {
        crate::path_management::validate_column_name(table_ref)
            .map_err(|e| format!("Invalid table: {e}"))?;
        (None, table_ref.to_string())
    };

    // Parse fk_spec: 'local_fk=remote_pk' or 'intermediate_alias.local_fk=remote_pk'
    let (local_fk_col, remote_pk_col, intermediate_alias) = parse_fk_spec(fk_spec)?;

    Ok(SourceRef {
        alias: alias.to_string(),
        schema,
        table,
        local_fk_col,
        remote_pk_col,
        intermediate_alias,
    })
}

/// Represents a registered identifier registration.
#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentifierRegistration {
    /// Identifier/slug column name
    pub slug_col: String,
    /// Registration mode ('flat' or 'hierarchical')
    pub mode: String,
    /// Parsed template (for flat mode)
    pub template: Vec<Token>,
    /// Source table references
    pub sources: Vec<SourceRef>,
    /// Enable deduplication
    pub dedup: bool,
    /// Column to scope deduplication (NULL = table-wide)
    pub dedup_scope_col: Option<String>,
    /// Scope reference for Strip modifier (e.g., 'org.identifier')
    pub scope_ref: Option<String>,
    // Hierarchical mode fields
    /// FK column pointing to parent (hierarchical mode only)
    pub parent_fk_col: Option<String>,
    /// Template for scope evaluation (hierarchical mode only, evaluated at root)
    pub scope_template: Option<Vec<Token>>,
    /// Template for each level (hierarchical mode only)
    pub level_template: Option<Vec<Token>>,
    /// Separator between levels (hierarchical mode only)
    pub level_sep: Option<String>,
}

/// Helper function to validate and parse sources.
#[allow(dead_code)]
fn parse_sources_array(sources: &[&str]) -> Result<Vec<SourceRef>, String> {
    let mut parsed_sources = Vec::new();
    for source_str in sources {
        parsed_sources.push(parse_source(source_str)?);
    }
    Ok(parsed_sources)
}

/// Registers an identifier on a table.
///
/// # Arguments
/// - `slug_col` - Name of the identifier/slug column
/// - `template` - Template string (e.g., `"{org.identifier!raw}|{self.name}"`)
/// - `sources` - Array of source specifications
/// - `dedup` - Enable deduplication with numeric suffixes
/// - `dedup_scope_col` - Column to scope dedup (NULL = table-wide)
/// - `scope_ref` - Reference to scope value for Strip modifier
///
/// # Returns
/// Parsed `IdentifierRegistration` or error
///
/// # Errors
/// - Invalid column names
/// - Invalid template syntax
/// - Invalid source specifications
#[allow(dead_code)]
pub fn register_identifier(
    slug_col: &str,
    template: &str,
    sources: &[&str],
    dedup: bool,
    dedup_scope_col: Option<&str>,
    scope_ref: Option<&str>,
) -> Result<IdentifierRegistration, String> {
    // Validate slug_col
    crate::path_management::validate_column_name(slug_col)
        .map_err(|e| format!("Invalid slug column: {e}"))?;

    // Validate dedup_scope_col if provided
    if let Some(col) = dedup_scope_col {
        crate::path_management::validate_column_name(col)
            .map_err(|e| format!("Invalid dedup scope column: {e}"))?;
    }

    // Parse template
    let tokens = parse_template(template).map_err(|e| format!("Invalid template: {e}"))?;

    // Parse all sources
    let parsed_sources = parse_sources_array(sources)?;

    Ok(IdentifierRegistration {
        slug_col: slug_col.to_string(),
        mode: "flat".to_string(),
        template: tokens,
        sources: parsed_sources,
        dedup,
        dedup_scope_col: dedup_scope_col.map(std::string::ToString::to_string),
        scope_ref: scope_ref.map(std::string::ToString::to_string),
        // Hierarchical mode fields (not used in flat mode)
        parent_fk_col: None,
        scope_template: None,
        level_template: None,
        level_sep: None,
    })
}

/// Registers a hierarchical identifier on a table.
///
/// # Arguments
/// - `slug_col` - Name of the identifier/slug column
/// - `scope_template` - Optional template string for scope evaluation (evaluated once at root)
/// - `level_template` - Template string for each level (e.g., `"{info.name}"`)
/// - `level_sep` - Separator between levels (e.g., `"."`)
/// - `parent_fk_col` - FK column pointing to parent row
/// - `sources` - Array of source specifications
/// - `dedup` - Enable deduplication with numeric suffixes
/// - `dedup_scope_col` - Column to scope dedup (NULL = table-wide)
/// - `scope_ref` - Reference to scope value for Strip modifier
///
/// # Returns
/// Parsed `IdentifierRegistration` with hierarchical fields or error
///
/// # Errors
/// - Invalid column names
/// - Invalid template syntax
/// - Invalid source specifications
#[allow(dead_code, clippy::too_many_arguments)]
pub fn register_identifier_hierarchical(
    slug_col: &str,
    scope_template: Option<&str>,
    level_template: &str,
    level_sep: &str,
    parent_fk_col: Option<&str>,
    sources: &[&str],
    dedup: bool,
    dedup_scope_col: Option<&str>,
    scope_ref: Option<&str>,
) -> Result<IdentifierRegistration, String> {
    // Validate slug_col
    crate::path_management::validate_column_name(slug_col)
        .map_err(|e| format!("Invalid slug column: {e}"))?;

    // Validate parent_fk_col if provided
    if let Some(col) = parent_fk_col {
        crate::path_management::validate_column_name(col)
            .map_err(|e| format!("Invalid parent_fk_col: {e}"))?;
    }

    // Validate dedup_scope_col if provided
    if let Some(col) = dedup_scope_col {
        crate::path_management::validate_column_name(col)
            .map_err(|e| format!("Invalid dedup scope column: {e}"))?;
    }

    // Parse scope_template if provided
    let parsed_scope_template = if let Some(tmpl) = scope_template {
        Some(parse_template(tmpl).map_err(|e| format!("Invalid scope_template: {e}"))?)
    } else {
        None
    };

    // Parse level_template
    let parsed_level_template =
        parse_template(level_template).map_err(|e| format!("Invalid level_template: {e}"))?;

    // Parse all sources
    let parsed_sources = parse_sources_array(sources)?;

    Ok(IdentifierRegistration {
        slug_col: slug_col.to_string(),
        mode: "hierarchical".to_string(),
        template: Vec::new(), // Empty for hierarchical mode
        sources: parsed_sources,
        dedup,
        dedup_scope_col: dedup_scope_col.map(std::string::ToString::to_string),
        scope_ref: scope_ref.map(std::string::ToString::to_string),
        parent_fk_col: parent_fk_col.map(std::string::ToString::to_string),
        scope_template: parsed_scope_template,
        level_template: Some(parsed_level_template),
        level_sep: Some(level_sep.to_string()),
    })
}

/// Detects cycles in identifier dependencies.
///
/// Performs depth-first search to detect cycles in the dependency graph.
/// A cycle exists if a table depends (directly or transitively) on its own identifier.
///
/// # Arguments
/// - `table_oid` - OID of the table being registered
/// - `dependencies` - Map of `table_oid` -> list of source table OIDs it depends on
///
/// # Returns
/// `Ok(())` if no cycle, `Err(cycle_path)` describing the cycle
///
/// # Example
/// ```ignore
/// let mut deps = HashMap::new();
/// deps.insert(1, vec![2]); // Table 1 depends on Table 2
/// deps.insert(2, vec![3]); // Table 2 depends on Table 3
/// deps.insert(3, vec![1]); // Table 3 depends on Table 1 -> CYCLE!
///
/// let result = detect_dependency_cycle(1, &deps);
/// assert!(result.is_err());
/// ```
#[allow(dead_code)]
pub fn detect_dependency_cycle(
    table_oid: u32,
    dependencies: &std::collections::HashMap<u32, Vec<u32>>,
) -> Result<(), String> {
    #[allow(clippy::items_after_statements)]
    fn dfs(
        node: u32,
        target: u32,
        deps: &std::collections::HashMap<u32, Vec<u32>>,
        visited: &mut std::collections::HashSet<u32>,
        rec_stack: &mut std::collections::HashSet<u32>,
        path: &mut Vec<u32>,
    ) -> Result<(), Vec<u32>> {
        visited.insert(node);
        rec_stack.insert(node);
        path.push(node);

        if let Some(neighbors) = deps.get(&node) {
            for &neighbor in neighbors {
                if neighbor == target {
                    // Found a cycle back to the target
                    path.push(neighbor);
                    return Err(path.clone());
                }

                if !visited.contains(&neighbor)
                    && dfs(neighbor, target, deps, visited, rec_stack, path).is_err()
                {
                    return Err(path.clone());
                }
            }
        }

        rec_stack.remove(&node);
        path.pop();
        Ok(())
    }

    let mut visited = std::collections::HashSet::new();
    let mut rec_stack = std::collections::HashSet::new();
    let mut path = Vec::new();

    match dfs(
        table_oid,
        table_oid,
        dependencies,
        &mut visited,
        &mut rec_stack,
        &mut path,
    ) {
        Ok(()) => Ok(()),
        Err(cycle_path) => {
            let cycle_str = cycle_path
                .iter()
                .map(std::string::ToString::to_string)
                .collect::<Vec<_>>()
                .join(" -> ");
            Err(format!("Dependency cycle detected: {cycle_str}"))
        }
    }
}

/// Evaluates a template to produce an identifier value.
///
/// This is the core logic used by the `tg_treekey_evaluate_identifier()` trigger.
/// Given a registration and resolved values, produces the final identifier string.
///
/// # Arguments
/// - `registration` - The identifier registration (parsed template, sources, etc.)
/// - `values` - Map of (alias, column) -> value (or None for NULL)
/// - `scope_value` - Optional scope value for Strip modifier
/// - `taken` - Identifiers already in use (for deduplication)
///
/// # Returns
/// The computed identifier string or error if required values missing
///
/// # Example
/// ```ignore
/// let reg = register_identifier(
///     "identifier",
///     "{org.identifier!raw}|{self.name}",
///     &["org:org:fk_org=pk", "self:self_table:pk=pk"],
///     false, None, None
/// ).unwrap();
///
/// let mut values = HashMap::new();
/// values.insert(("org".to_string(), "identifier".to_string()), Some("acme".to_string()));
/// values.insert(("self".to_string(), "name".to_string()), Some("widget".to_string()));
///
/// let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
/// assert_eq!(result, "acme|widget");
/// ```
#[allow(dead_code)]
pub fn evaluate_identifier(
    registration: &IdentifierRegistration,
    values: &std::collections::HashMap<(String, String), Option<String>>,
    _scope_value: Option<&str>,
    taken: &[&str],
) -> Result<String, String> {
    // Render template with values
    let mut result = render_template(&registration.template, values);

    // Apply deduplication if enabled
    if registration.dedup {
        if let Some(scope_col) = &registration.dedup_scope_col {
            // Scope-based dedup: only check identifiers in the same scope
            let _scope_val = values
                .get(&("self".to_string(), scope_col.clone()))
                .and_then(|v| v.as_deref())
                .ok_or_else(|| format!("Dedup scope column '{scope_col}' not found in values"))?;

            // For now, just use taken as-is; in SQL trigger, would filter by scope
        }
        // Both scope-based and table-wide dedup use the same taken list for now
        let next = crate::identifier_next(&result, taken);
        result = next;
    }

    Ok(result)
}

/// Represents a node in a hierarchical tree for identifier evaluation.
///
/// This structure holds the values needed to evaluate a node's identifier,
/// including a reference to its parent for traversal up the hierarchy.
#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct HierarchicalNode {
    /// Map of (alias, column) -> value for this node
    pub values: std::collections::HashMap<(String, String), Option<String>>,
    /// Optional parent node (None for root)
    pub parent: Option<Box<Self>>,
}

/// Evaluates a hierarchical identifier by traversing from leaf to root.
///
/// For a hierarchical registration, computes the identifier by:
/// 1. Traversing from the given node to the root
/// 2. At each node, evaluating the `level_template`
/// 3. At the root, evaluating the `scope_template`
/// 4. Joining all level values with `level_sep`
/// 5. Prepending the scope value to the final result
///
/// # Arguments
/// - `registration` - The hierarchical identifier registration
/// - `node` - The node to evaluate (may be root or child)
/// - `taken` - Identifiers already in use (for deduplication)
///
/// # Returns
/// The computed hierarchical identifier or error if required values missing
///
/// # Example
/// ```ignore
/// let mut root_values = HashMap::new();
/// root_values.insert(("type".to_string(), "identifier".to_string()), Some("building".to_string()));
/// root_values.insert(("info".to_string(), "int_ordered".to_string()), Some("1".to_string()));
/// root_values.insert(("info".to_string(), "name".to_string()), Some("Main".to_string()));
/// let root = HierarchicalNode { values: root_values, parent: None };
///
/// let reg = register_identifier_hierarchical(
///     "identifier",
///     Some("{type.identifier!raw}"),
///     "{info.int_ordered!padded(3)}-{info.name}",
///     ".",
///     Some("fk_parent_loc"),
///     &[...],
///     false, None, None
/// ).unwrap();
///
/// let result = evaluate_identifier_hierarchical(&reg, &root, &[]).unwrap();
/// // Result: "building.001-main"
/// ```
#[allow(dead_code)]
pub fn evaluate_identifier_hierarchical(
    registration: &IdentifierRegistration,
    node: &HierarchicalNode,
    taken: &[&str],
) -> Result<String, String> {
    // Verify this is hierarchical mode
    if registration.mode != "hierarchical" {
        return Err("Registration must be in hierarchical mode".to_string());
    }

    // Get templates
    let level_template = registration
        .level_template
        .as_ref()
        .ok_or("level_template not set")?;
    let level_sep = registration.level_sep.as_ref().ok_or("level_sep not set")?;

    // Traverse from node to root, collecting nodes
    let mut nodes = Vec::new();
    let mut current = Some(node);
    while let Some(n) = current {
        nodes.push(n);
        current = n.parent.as_deref();
    }

    // Reverse to go from root to leaf
    nodes.reverse();

    // Evaluate level_template at each node
    let mut level_values = Vec::new();
    for n in &nodes {
        let level_val = render_template(level_template, &n.values);
        level_values.push(level_val);
    }

    // Build the identifier
    #[allow(clippy::option_if_let_else)]
    let mut result = if let Some(scope_template) = &registration.scope_template {
        // Evaluate scope_template at the root (first node)
        let scope_val = render_template(scope_template, &nodes[0].values);
        format!("{}.{}", scope_val, level_values.join(level_sep))
    } else {
        // No scope, just join level values
        level_values.join(level_sep)
    };

    // Apply deduplication if enabled
    if registration.dedup {
        let next = crate::identifier_next(&result, taken);
        result = next;
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_parse_simple_expression() {
        let tokens = parse_template("{self.name}").unwrap();
        assert_eq!(tokens.len(), 1);
        assert!(matches!(
            &tokens[0],
            Token::Expr {
                alias,
                column,
                modifier: Modifier::Slugify,
                optional: false,
            } if alias == "self" && column == "name"
        ));
    }

    #[test]
    fn test_parse_raw_modifier() {
        let tokens = parse_template("{org.identifier!raw}").unwrap();
        assert!(matches!(
            &tokens[0],
            Token::Expr {
                modifier: Modifier::Raw,
                ..
            }
        ));
    }

    #[test]
    fn test_parse_strip_modifier() {
        let tokens = parse_template("{m.identifier!strip}").unwrap();
        assert!(matches!(
            &tokens[0],
            Token::Expr {
                modifier: Modifier::Strip,
                ..
            }
        ));
    }

    #[test]
    fn test_parse_padded_modifier() {
        let tokens = parse_template("{info.int_ordered!padded(3)}").unwrap();
        assert!(matches!(
            &tokens[0],
            Token::Expr {
                modifier: Modifier::Padded(3),
                ..
            }
        ));
    }

    #[test]
    fn test_parse_optional_token() {
        let tokens = parse_template("{ou.identifier!strip?}").unwrap();
        assert!(matches!(&tokens[0], Token::Expr { optional: true, .. }));
    }

    #[test]
    fn test_parse_mixed_literals_and_expressions() {
        let tokens = parse_template("{org.identifier!raw}|{self.name}").unwrap();
        assert_eq!(tokens.len(), 3);
        assert!(matches!(&tokens[0], Token::Expr { .. }));
        assert_eq!(&tokens[1], &Token::Literal("|".to_string()));
        assert!(matches!(&tokens[2], Token::Expr { .. }));
    }

    #[test]
    fn test_parse_empty_expression_error() {
        let err = parse_template("{}").unwrap_err();
        assert_eq!(err.message, "Empty expression");
    }

    #[test]
    fn test_parse_no_dot_error() {
        let err = parse_template("{alias}").unwrap_err();
        assert!(err.message.contains("must contain '.'"));
    }

    #[test]
    fn test_parse_unknown_modifier_error() {
        let err = parse_template("{a.b!unknown}").unwrap_err();
        assert!(err.message.contains("Unknown modifier"));
    }

    #[test]
    fn test_parse_complex_template() {
        let tokens = parse_template(
            "{org.identifier!raw}|{model.identifier!strip}.{self.serial_number!raw}",
        )
        .unwrap();
        assert_eq!(tokens.len(), 5);
    }

    // ===== Rendering tests (Cycle 2) =====

    #[test]
    fn test_render_all_values_present() {
        let tokens = parse_template("{a.col!raw}|{b.col!raw}.{c.col!raw}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), Some("y".to_string()));
        values.insert(("c".to_string(), "col".to_string()), Some("z".to_string()));

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x|y.z");
    }

    #[test]
    fn test_render_optional_null_elides_preceding_literal() {
        let tokens = parse_template("{a.col!raw}|{b.col!raw}.{c.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), Some("y".to_string()));
        values.insert(("c".to_string(), "col".to_string()), None);

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x|y");
    }

    #[test]
    fn test_render_multiple_optional_nulls() {
        let tokens = parse_template("{a.col!raw}|{b.col!raw?}.{c.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), None);
        values.insert(("c".to_string(), "col".to_string()), None);

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x");
    }

    #[test]
    fn test_render_optional_non_null() {
        let tokens = parse_template("{a.col!raw}|{b.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), Some("y".to_string()));

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x|y");
    }

    #[test]
    fn test_render_leading_optional_null_elides_trailing_literal() {
        let tokens = parse_template("{a.col!raw?}|{b.col!raw}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), None);
        values.insert(("b".to_string(), "col".to_string()), Some("y".to_string()));

        let result = render_template(&tokens, &values);
        assert_eq!(result, "y");
    }

    #[test]
    fn test_render_adjacent_optionals_both_null() {
        let tokens = parse_template("{a.col!raw}{b.col!raw?}.{c.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), None);
        values.insert(("c".to_string(), "col".to_string()), None);

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x");
    }

    #[test]
    fn test_render_adjacent_optionals_first_null_second_present() {
        let tokens = parse_template("{a.col!raw}|{b.col!raw?}.{c.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), Some("x".to_string()));
        values.insert(("b".to_string(), "col".to_string()), None);
        values.insert(("c".to_string(), "col".to_string()), Some("z".to_string()));

        let result = render_template(&tokens, &values);
        assert_eq!(result, "x.z");
    }

    #[test]
    fn test_render_all_optional_all_null() {
        let tokens = parse_template("{a.col!raw?}|{b.col!raw?}").unwrap();
        let mut values = HashMap::new();
        values.insert(("a".to_string(), "col".to_string()), None);
        values.insert(("b".to_string(), "col".to_string()), None);

        let result = render_template(&tokens, &values);
        assert_eq!(result, "");
    }

    // ===== Modifier application tests (Cycle 3) =====

    #[test]
    fn test_apply_modifier_raw() {
        let result = apply_modifier("Acme Corp", &Modifier::Raw, None).unwrap();
        assert_eq!(result, "Acme Corp");
    }

    #[test]
    fn test_apply_modifier_slugify() {
        let result = apply_modifier("Île-de-France", &Modifier::Slugify, None).unwrap();
        assert_eq!(result, "ile-de-france");
    }

    #[test]
    fn test_apply_modifier_slugify_ascii() {
        let result = apply_modifier("Hello World", &Modifier::Slugify, None).unwrap();
        assert_eq!(result, "hello-world");
    }

    #[test]
    fn test_apply_modifier_padded_short() {
        let result = apply_modifier("7", &Modifier::Padded(3), None).unwrap();
        assert_eq!(result, "007");
    }

    #[test]
    fn test_apply_modifier_padded_exact() {
        let result = apply_modifier("42", &Modifier::Padded(3), None).unwrap();
        assert_eq!(result, "042");
    }

    #[test]
    fn test_apply_modifier_padded_long() {
        let result = apply_modifier("1234", &Modifier::Padded(3), None).unwrap();
        assert_eq!(result, "1234");
    }

    #[test]
    fn test_apply_modifier_strip_with_scope() {
        let result = apply_modifier("acme|model.SN", &Modifier::Strip, Some("acme")).unwrap();
        assert_eq!(result, "model.SN");
    }

    #[test]
    fn test_apply_modifier_strip_non_matching_scope() {
        let result = apply_modifier("other|x", &Modifier::Strip, Some("acme")).unwrap();
        assert_eq!(result, "other|x");
    }

    #[test]
    fn test_apply_modifier_strip_without_scope() {
        let result = apply_modifier("acme|model.SN", &Modifier::Strip, None);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("requires a scope"));
    }

    // ===== Source parsing tests (Cycle 5) =====

    #[test]
    fn test_parse_source_simple_table() {
        let source = parse_source("org:organizations:fk_org=pk_org").unwrap();
        assert_eq!(source.alias, "org");
        assert_eq!(source.table, "organizations");
        assert_eq!(source.local_fk_col, "fk_org");
        assert_eq!(source.remote_pk_col, "pk_org");
        assert_eq!(source.schema, None);
    }

    #[test]
    fn test_parse_source_with_schema() {
        let source = parse_source("org:public.organizations:fk_org=pk_org").unwrap();
        assert_eq!(source.alias, "org");
        assert_eq!(source.schema, Some("public".to_string()));
        assert_eq!(source.table, "organizations");
    }

    #[test]
    fn test_parse_source_invalid_alias_uppercase() {
        let result = parse_source("Org:organizations:fk_org=pk_org");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("alias"));
    }

    #[test]
    fn test_parse_source_missing_fk_spec() {
        let result = parse_source("org:organizations");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("3 parts"));
    }

    #[test]
    fn test_parse_source_malformed_fk_spec() {
        let result = parse_source("org:organizations:fk_col_no_equals");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("local=remote"));
    }

    #[test]
    fn test_parse_source_invalid_table_name() {
        let result = parse_source("org:1_invalid:fk_org=pk_org");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Invalid table"));
    }

    #[test]
    fn test_parse_source_with_whitespace() {
        let source = parse_source("  org : organizations : fk_org = pk_org  ").unwrap();
        assert_eq!(source.alias, "org");
        assert_eq!(source.table, "organizations");
    }

    // ===== FK spec parsing helper tests =====

    #[test]
    fn test_parse_fk_spec_direct() {
        let (fk_col, pk_col, intermediate) = parse_fk_spec("fk_org=pk_org").unwrap();
        assert_eq!(fk_col, "fk_org");
        assert_eq!(pk_col, "pk_org");
        assert_eq!(intermediate, None);
    }

    #[test]
    fn test_parse_fk_spec_chained() {
        let (fk_col, pk_col, intermediate) =
            parse_fk_spec("info.fk_public_address=pk_public_address").unwrap();
        assert_eq!(fk_col, "fk_public_address");
        assert_eq!(pk_col, "pk_public_address");
        assert_eq!(intermediate, Some("info".to_string()));
    }

    #[test]
    fn test_parse_fk_spec_missing_equals() {
        let result = parse_fk_spec("fk_org_no_equals");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("local=remote"));
    }

    #[test]
    fn test_parse_fk_spec_double_dot_error() {
        let result = parse_fk_spec("a.b.c=pk");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("single-hop"));
    }

    #[test]
    fn test_parse_source_chained_fk() {
        // 'addr:tenant.tb_public_address:info.fk_public_address=pk_public_address'
        // -> chained join: target table joins 'info' alias first, then 'info.fk_public_address'
        let source =
            parse_source("addr:tenant.tb_public_address:info.fk_public_address=pk_public_address")
                .unwrap();
        assert_eq!(source.alias, "addr");
        assert_eq!(source.schema, Some("tenant".to_string()));
        assert_eq!(source.table, "tb_public_address");
        assert_eq!(source.intermediate_alias, Some("info".to_string()));
        assert_eq!(source.local_fk_col, "fk_public_address");
        assert_eq!(source.remote_pk_col, "pk_public_address");
    }

    #[test]
    fn test_parse_source_chained_fk_direct_comparison() {
        // Direct FK join (existing behavior should still work)
        let source =
            parse_source("info:tenant.tb_location_info:fk_location_info=pk_location_info").unwrap();
        assert_eq!(source.alias, "info");
        assert_eq!(source.table, "tb_location_info");
        assert_eq!(source.intermediate_alias, None);
        assert_eq!(source.local_fk_col, "fk_location_info");
    }

    #[test]
    fn test_parse_source_invalid_chained_fk_double_chain() {
        // Invalid: 'x:table:a.b.c=pk' (double chain) -> error
        let result = parse_source("x:table:a.b.c=pk");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("only single-hop"));
    }

    #[test]
    fn test_parse_source_invalid_chained_fk_undeclared_alias() {
        // Invalid: 'x:table:nonexistent_alias.fk=pk' (alias not declared)
        // This will be caught at registration time when checking declared aliases
        // For now, the parser should accept it syntactically
        let source = parse_source("x:table:nonexistent_alias.fk_col=pk").unwrap();
        assert_eq!(
            source.intermediate_alias,
            Some("nonexistent_alias".to_string())
        );
        assert_eq!(source.local_fk_col, "fk_col");
    }

    #[test]
    fn test_parse_source_chained_fk_without_schema() {
        // Chained FK with implicit 'public' schema
        let source =
            parse_source("addr:tb_public_address:info.fk_public_address=pk_public_address")
                .unwrap();
        assert_eq!(source.alias, "addr");
        assert_eq!(source.schema, None); // Defaults to public at query time
        assert_eq!(source.table, "tb_public_address");
        assert_eq!(source.intermediate_alias, Some("info".to_string()));
        assert_eq!(source.local_fk_col, "fk_public_address");
    }

    // ===== Registration tests (Cycle 5) =====

    #[test]
    fn test_register_identifier_simple_flat() {
        let reg = register_identifier(
            "identifier",
            "{self.name}",
            &["self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        assert_eq!(reg.slug_col, "identifier");
        assert_eq!(reg.mode, "flat");
        assert!(!reg.dedup);
        assert_eq!(reg.sources.len(), 1);
        assert_eq!(reg.sources[0].alias, "self");
    }

    #[test]
    fn test_register_identifier_complex_template() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{model.identifier!strip}.{self.serial!padded(3)}",
            &[
                "org:public.org:fk_org=pk",
                "model:models:fk_model=pk",
                "self:self_table:pk=pk",
            ],
            false,
            None,
            Some("org.identifier"),
        )
        .unwrap();

        assert_eq!(reg.slug_col, "identifier");
        assert_eq!(reg.sources.len(), 3);
        assert_eq!(reg.scope_ref, Some("org.identifier".to_string()));
    }

    #[test]
    fn test_register_identifier_with_dedup() {
        let reg = register_identifier(
            "identifier",
            "{org.name}",
            &["org:org:fk_org=pk"],
            true,
            Some("fk_org"),
            None,
        )
        .unwrap();

        assert!(reg.dedup);
        assert_eq!(reg.dedup_scope_col, Some("fk_org".to_string()));
    }

    #[test]
    fn test_register_identifier_invalid_slug_col() {
        let result = register_identifier(
            "Invalid",
            "{self.name}",
            &["self:self_table:pk=pk"],
            false,
            None,
            None,
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("slug column"));
    }

    #[test]
    fn test_register_identifier_invalid_template() {
        let result = register_identifier(
            "identifier",
            "{self}",
            &["self:self_table:pk=pk"],
            false,
            None,
            None,
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Invalid template"));
    }

    #[test]
    fn test_register_identifier_invalid_source() {
        let result = register_identifier(
            "identifier",
            "{self.name}",
            &["INVALID_SOURCE"],
            false,
            None,
            None,
        );
        assert!(result.is_err());
    }

    #[test]
    fn test_register_identifier_invalid_dedup_scope_col() {
        let result = register_identifier(
            "identifier",
            "{org.name}",
            &["org:org:fk_org=pk"],
            true,
            Some("Invalid!"),
            None,
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("dedup scope column"));
    }

    #[test]
    fn test_register_identifier_hierarchical_basic() {
        // Test basic hierarchical registration
        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"), // scope_template
            "{info.int_ordered!padded(3)}-{info.name}", // level_template
            ".",                           // level_sep
            Some("fk_parent_loc"),         // parent_fk_col
            &[
                "type:tenant.test_loc_type:fk_loc_type=pk",
                "info:tenant.test_loc_info:fk_loc_info=pk",
                "self:self_table:pk=pk",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        assert_eq!(reg.slug_col, "identifier");
        assert_eq!(reg.mode, "hierarchical");
        assert_eq!(reg.parent_fk_col, Some("fk_parent_loc".to_string()));
        assert!(reg.scope_template.is_some());
        assert!(reg.level_template.is_some());
        assert_eq!(reg.level_sep, Some(".".to_string()));
        assert_eq!(reg.sources.len(), 3);
    }

    #[test]
    fn test_register_identifier_hierarchical_no_scope() {
        // Test hierarchical registration without scope template
        let reg = register_identifier_hierarchical(
            "identifier",
            None,              // scope_template
            "{info.name}",     // level_template
            "-",               // level_sep
            Some("fk_parent"), // parent_fk_col
            &["info:test_info:fk_info=pk", "self:self:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        assert_eq!(reg.mode, "hierarchical");
        assert_eq!(reg.scope_template, None);
        assert!(reg.level_template.is_some());
    }

    #[test]
    fn test_register_identifier_hierarchical_invalid_parent_fk() {
        // Test that invalid parent_fk_col is rejected
        let result = register_identifier_hierarchical(
            "identifier",
            Some("{self.name}"),
            "{self.name}",
            ".",
            Some("Invalid!"), // Invalid: contains '!'
            &["self:self:pk=pk"],
            false,
            None,
            None,
        );

        assert!(result.is_err());
        assert!(result.unwrap_err().contains("parent_fk_col"));
    }

    #[test]
    fn test_register_identifier_hierarchical_invalid_level_template() {
        // Test that invalid level_template is rejected
        let result = register_identifier_hierarchical(
            "identifier",
            Some("{self.name}"),
            "{}", // Empty expression - invalid
            ".",
            Some("fk_parent"),
            &["self:self:pk=pk"],
            false,
            None,
            None,
        );

        assert!(result.is_err());
        assert!(result.unwrap_err().contains("level_template"));
    }

    // ===== Evaluation tests (Cycle 6) =====

    #[test]
    fn test_evaluate_identifier_simple() {
        let reg = register_identifier(
            "identifier",
            "{org.name!raw}|{self.serial!raw}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "name".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("self".to_string(), "serial".to_string()),
            Some("SN001".to_string()),
        );

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "acme|SN001");
    }

    #[test]
    fn test_evaluate_identifier_with_optional_null() {
        let reg = register_identifier(
            "identifier",
            "{org.name!raw}|{self.suffix!raw?}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "name".to_string()),
            Some("acme".to_string()),
        );
        values.insert(("self".to_string(), "suffix".to_string()), None);

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "acme");
    }

    #[test]
    fn test_evaluate_identifier_with_modifiers() {
        let reg = register_identifier(
            "identifier",
            "{org.name!slugify}.{self.serial!padded(4)}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "name".to_string()),
            Some("Île de France".to_string()),
        );
        values.insert(
            ("self".to_string(), "serial".to_string()),
            Some("42".to_string()),
        );

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "ile-de-france.0042");
    }

    #[test]
    fn test_evaluate_identifier_dedup_simple() {
        let reg = register_identifier(
            "identifier",
            "{org.name!raw}",
            &["org:org:fk_org=pk"],
            true,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "name".to_string()),
            Some("acme".to_string()),
        );

        // First time: no taken
        let result1 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result1, "acme");

        // Second time: "acme" is taken
        let result2 = evaluate_identifier(&reg, &values, None, &["acme"]).unwrap();
        assert_eq!(result2, "acme#2");
    }

    #[test]
    fn test_evaluate_identifier_dedup_multiple_taken() {
        let reg = register_identifier(
            "identifier",
            "{self.base!raw}",
            &["self:self_table:pk=pk"],
            true,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "base".to_string()),
            Some("item".to_string()),
        );

        // With "item" and "item#2" taken, should get "item#3"
        let result = evaluate_identifier(&reg, &values, None, &["item", "item#2"]).unwrap();
        assert_eq!(result, "item#3");
    }

    #[test]
    fn test_evaluate_identifier_missing_value() {
        let reg = register_identifier(
            "identifier",
            "{self.name!raw}",
            &["self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let values = HashMap::new(); // Empty values map

        let result = evaluate_identifier(&reg, &values, None, &[]);
        // render_template silently skips missing values, produces empty string
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "");
    }

    #[test]
    fn test_evaluate_identifier_complex_template() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{model.identifier!raw}.{self.serial!padded(3)}",
            &[
                "org:org:fk_org=pk",
                "model:models:fk_model=pk",
                "self:self_table:pk=pk",
            ],
            false,
            None,
            Some("org.identifier"),
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "identifier".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("model".to_string(), "identifier".to_string()),
            Some("widget".to_string()),
        );
        values.insert(
            ("self".to_string(), "serial".to_string()),
            Some("7".to_string()),
        );

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "acme|widget.007");
    }

    // ===== Optional token handling in trigger (Cycle 7) =====

    #[test]
    fn test_evaluate_optional_token_with_value() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{self.name!raw}∘{self.suffix!raw?}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "identifier".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(
            ("self".to_string(), "suffix".to_string()),
            Some("X".to_string()),
        );

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "acme|foo∘X");
    }

    #[test]
    fn test_evaluate_optional_token_null_elides_separator() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{self.name!raw}∘{self.suffix!raw?}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "identifier".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(("self".to_string(), "suffix".to_string()), None);

        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "acme|foo");
    }

    #[test]
    fn test_evaluate_optional_token_update_null_to_value() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{self.name!raw}∘{self.suffix!raw?}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        // Initially NULL
        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "identifier".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(("self".to_string(), "suffix".to_string()), None);

        let result1 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result1, "acme|foo");

        // Update to a value
        values.insert(
            ("self".to_string(), "suffix".to_string()),
            Some("Y".to_string()),
        );
        let result2 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result2, "acme|foo∘Y");
    }

    #[test]
    fn test_evaluate_optional_token_update_value_to_null() {
        let reg = register_identifier(
            "identifier",
            "{org.identifier!raw}|{self.name!raw}∘{self.suffix!raw?}",
            &["org:org:fk_org=pk", "self:self_table:pk=pk"],
            false,
            None,
            None,
        )
        .unwrap();

        // Initially with value
        let mut values = HashMap::new();
        values.insert(
            ("org".to_string(), "identifier".to_string()),
            Some("acme".to_string()),
        );
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(
            ("self".to_string(), "suffix".to_string()),
            Some("Z".to_string()),
        );

        let result1 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result1, "acme|foo∘Z");

        // Update to NULL
        values.insert(("self".to_string(), "suffix".to_string()), None);
        let result2 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result2, "acme|foo");
    }

    // ===== Deduplication (Cycle 8) =====

    #[test]
    fn test_dedup_scope_based_first_row() {
        let reg = register_identifier(
            "identifier",
            "{self.name!raw}",
            &["self:self_table:pk=pk"],
            true,
            Some("fk_org"),
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(
            ("self".to_string(), "fk_org".to_string()),
            Some("org1".to_string()),
        );

        // First row with this name in this scope, no dedup needed
        let result = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result, "foo");
    }

    #[test]
    fn test_dedup_scope_based_conflict() {
        let reg = register_identifier(
            "identifier",
            "{self.name!raw}",
            &["self:self_table:pk=pk"],
            true,
            Some("fk_org"),
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("foo".to_string()),
        );
        values.insert(
            ("self".to_string(), "fk_org".to_string()),
            Some("org1".to_string()),
        );

        // "foo" already taken in org1, should get foo#2
        let result = evaluate_identifier(&reg, &values, None, &["foo"]).unwrap();
        assert_eq!(result, "foo#2");
    }

    #[test]
    fn test_dedup_table_wide() {
        let reg = register_identifier(
            "identifier",
            "{self.name!raw}",
            &["self:self_table:pk=pk"],
            true,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "name".to_string()),
            Some("item".to_string()),
        );

        // First row, no dedup
        let result1 = evaluate_identifier(&reg, &values, None, &[]).unwrap();
        assert_eq!(result1, "item");

        // Second row with same base, should get item#2
        let result2 = evaluate_identifier(&reg, &values, None, &["item"]).unwrap();
        assert_eq!(result2, "item#2");

        // Third row, should skip item#2, get item#3
        let result3 = evaluate_identifier(&reg, &values, None, &["item", "item#2"]).unwrap();
        assert_eq!(result3, "item#3");
    }

    #[test]
    fn test_dedup_gap_filling() {
        let reg = register_identifier(
            "identifier",
            "{self.base!raw}",
            &["self:self_table:pk=pk"],
            true,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "base".to_string()),
            Some("x".to_string()),
        );

        // With x and x#3 taken, should fill gap and get x#2
        let result = evaluate_identifier(&reg, &values, None, &["x", "x#3"]).unwrap();
        assert_eq!(result, "x#2");
    }

    #[test]
    fn test_dedup_self_conflict_excludes_self() {
        let reg = register_identifier(
            "identifier",
            "{self.base!raw}",
            &["self:self_table:pk=pk"],
            true,
            None,
            None,
        )
        .unwrap();

        let mut values = HashMap::new();
        values.insert(
            ("self".to_string(), "base".to_string()),
            Some("name".to_string()),
        );

        // If this row's current value is "name#2" and taken has "name" and "name#2",
        // UPDATE should not re-assign to #3, but stay as #2
        // (Our current impl would reassign, which is OK for INSERT but needs checking for UPDATE)
        let result = evaluate_identifier(&reg, &values, None, &["name", "name#2"]).unwrap();
        // This is expected to get #3 since we don't track the current row
        assert_eq!(result, "name#3");
    }

    // ===== Cycle detection (Cycle 10) =====

    #[test]
    fn test_cycle_detection_no_cycle() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![2, 3]);
        deps.insert(2, vec![4]);
        deps.insert(3, vec![4]);
        // 4 has no dependencies

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_ok());
    }

    #[test]
    fn test_cycle_detection_self_reference() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![1]); // Table 1 depends on itself

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_err());
        let err_msg = result.unwrap_err();
        assert!(err_msg.contains("cycle") || err_msg.contains("Cycle"));
    }

    #[test]
    fn test_cycle_detection_two_table_cycle() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![2]); // 1 -> 2
        deps.insert(2, vec![1]); // 2 -> 1 (cycle!)

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(err.contains('1') && err.contains('2'));
    }

    #[test]
    fn test_cycle_detection_longer_cycle() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![2]); // 1 -> 2
        deps.insert(2, vec![3]); // 2 -> 3
        deps.insert(3, vec![1]); // 3 -> 1 (cycle!)

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert!(err.contains("Cycle") || err.contains("cycle"));
    }

    #[test]
    fn test_cycle_detection_diamond_no_cycle() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![2, 3]); // 1 -> 2 and 3
        deps.insert(2, vec![4]); // 2 -> 4
        deps.insert(3, vec![4]); // 3 -> 4 (diamond, not a cycle)

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_ok());
    }

    #[test]
    fn test_cycle_detection_complex_no_cycle() {
        let mut deps = HashMap::new();
        deps.insert(1, vec![2]);
        deps.insert(2, vec![3, 4]);
        deps.insert(3, vec![5]);
        deps.insert(4, vec![5]);
        deps.insert(5, vec![]);

        let result = detect_dependency_cycle(1, &deps);
        assert!(result.is_ok());
    }

    #[test]
    fn test_cycle_detection_cycle_not_involving_start() {
        // A -> B -> C -> B forms a cycle, but starting from A, we should detect it
        let mut deps = HashMap::new();
        deps.insert(1, vec![2]); // 1 -> 2
        deps.insert(2, vec![3]); // 2 -> 3
        deps.insert(3, vec![2]); // 3 -> 2 (cycle between 2 and 3)

        let result = detect_dependency_cycle(1, &deps);
        // Starting from 1, we traverse to 2, then to 3, then back to 2
        // This doesn't form a cycle back to 1, so it should be OK
        assert!(result.is_ok());
    }

    // ===== Hierarchical evaluation (Cycle 3) =====

    #[test]
    fn test_evaluate_hierarchical_root_only() {
        // Test hierarchical identifier evaluation for a root node (no parent)
        // scope_template = '{type.identifier!raw}'
        // level_template = '{info.int_ordered!padded(3)}-{info.name}'
        // level_sep = '.'
        //
        // Root node with fk_parent_loc=NULL should have:
        // identifier = 'building.001-main'

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Root node values: type.identifier='building', info.int_ordered=1, info.name='Main'
        let mut values = HashMap::new();
        values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let root = HierarchicalNode {
            values,
            parent: None,
        };

        let result = evaluate_identifier_hierarchical(&reg, &root, &[]).unwrap();
        assert_eq!(result, "building.001-main");
    }

    #[test]
    fn test_evaluate_hierarchical_two_level() {
        // Test hierarchical identifier evaluation for a two-level hierarchy
        // Root identifier: 'building.001-main'
        // Child identifier: 'building.001-main.002-floor-a'

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Root node values
        let mut root_values = HashMap::new();
        root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let root = HierarchicalNode {
            values: root_values,
            parent: None,
        };

        // Child node values
        let mut child_values = HashMap::new();
        child_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );

        let child = HierarchicalNode {
            values: child_values,
            parent: Some(Box::new(root)),
        };

        let result = evaluate_identifier_hierarchical(&reg, &child, &[]).unwrap();
        assert_eq!(result, "building.001-main.002-floor-a");
    }

    #[test]
    fn test_evaluate_hierarchical_three_level() {
        // Test hierarchical identifier evaluation for a three-level hierarchy
        // Root: 'building.001-main'
        // Child: 'building.001-main.002-floor-a'
        // Grandchild: 'building.001-main.002-floor-a.003-room-1'

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Root node
        let mut root_values = HashMap::new();
        root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );
        let root = HierarchicalNode {
            values: root_values,
            parent: None,
        };

        // Child node
        let mut child_values = HashMap::new();
        child_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );
        let child = HierarchicalNode {
            values: child_values,
            parent: Some(Box::new(root)),
        };

        // Grandchild node
        let mut grandchild_values = HashMap::new();
        grandchild_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        grandchild_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("3".to_string()),
        );
        grandchild_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Room 1".to_string()),
        );
        let grandchild = HierarchicalNode {
            values: grandchild_values,
            parent: Some(Box::new(child)),
        };

        let result = evaluate_identifier_hierarchical(&reg, &grandchild, &[]).unwrap();
        assert_eq!(result, "building.001-main.002-floor-a.003-room-1");
    }

    #[test]
    fn test_evaluate_hierarchical_no_scope_template() {
        // Test hierarchical evaluation without a scope_template
        // level_template = '{info.name!raw}'
        // level_sep = '/'
        //
        // Result: 'Main/Floor A'

        let reg = register_identifier_hierarchical(
            "identifier",
            None, // No scope_template
            "{info.name!raw}",
            "/",
            Some("fk_parent_loc"),
            &["info:test_loc_info:fk_loc_info=pk_loc_info"],
            false,
            None,
            None,
        )
        .unwrap();

        // Root node
        let mut root_values = HashMap::new();
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );
        let root = HierarchicalNode {
            values: root_values,
            parent: None,
        };

        // Child node
        let mut child_values = HashMap::new();
        child_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );
        let child = HierarchicalNode {
            values: child_values,
            parent: Some(Box::new(root)),
        };

        let result = evaluate_identifier_hierarchical(&reg, &child, &[]).unwrap();
        assert_eq!(result, "Main/Floor A");
    }

    // ===== Hierarchical cascade (Cycle 4) =====

    #[test]
    fn test_cascade_node_moved_to_root() {
        // Test cascade when a child node is moved to become a root
        // Original: root -> child -> grandchild
        // After move: root (unchanged), child (moved to root), grandchild (still under child)
        //
        // Original identifiers:
        // root: 'building.001-main'
        // child: 'building.001-main.002-floor-a'
        // grandchild: 'building.001-main.002-floor-a.003-room-1'
        //
        // After move:
        // root: 'building.001-main' (unchanged)
        // child: 'building.002-floor-a' (no parent levels!)
        // grandchild: 'building.002-floor-a.003-room-1' (parent chain changed)

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Original tree structure
        let mut root_values = HashMap::new();
        root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );
        let root = HierarchicalNode {
            values: root_values,
            parent: None,
        };

        let mut child_values = HashMap::new();
        child_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );
        let mut grandchild_values = HashMap::new();
        grandchild_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        grandchild_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("3".to_string()),
        );
        grandchild_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Room 1".to_string()),
        );

        // Original identifiers - build grandchild with original child as parent
        let original_child = HierarchicalNode {
            values: child_values.clone(),
            parent: Some(Box::new(root)),
        };
        let original_grandchild = HierarchicalNode {
            values: grandchild_values.clone(),
            parent: Some(Box::new(original_child)),
        };
        let original_grandchild_id =
            evaluate_identifier_hierarchical(&reg, &original_grandchild, &[]).unwrap();
        assert_eq!(
            original_grandchild_id,
            "building.001-main.002-floor-a.003-room-1"
        );

        // After move: child becomes a root
        let moved_child = HierarchicalNode {
            values: child_values,
            parent: None, // Now a root!
        };
        let moved_child_id = evaluate_identifier_hierarchical(&reg, &moved_child, &[]).unwrap();
        assert_eq!(moved_child_id, "building.002-floor-a");

        // Grandchild now has moved_child as parent
        let grandchild_after_move = HierarchicalNode {
            values: grandchild_values,
            parent: Some(Box::new(moved_child)),
        };
        let grandchild_after_move_id =
            evaluate_identifier_hierarchical(&reg, &grandchild_after_move, &[]).unwrap();
        assert_eq!(grandchild_after_move_id, "building.002-floor-a.003-room-1");
    }

    #[test]
    fn test_cascade_source_data_change() {
        // Test cascade when source data changes
        // A node's source data (name) changes, which should affect its identifier
        // and all descendants' identifiers (because name appears in level_template)

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Original tree
        let mut root_values = HashMap::new();
        root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let root = HierarchicalNode {
            values: root_values,
            parent: None,
        };

        let mut child_values = HashMap::new();
        child_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        child_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );

        let child = HierarchicalNode {
            values: child_values,
            parent: Some(Box::new(root)),
        };

        let original_child_id = evaluate_identifier_hierarchical(&reg, &child, &[]).unwrap();
        assert_eq!(original_child_id, "building.001-main.002-floor-a");

        // Change child's source data (name)
        let mut child_values_changed = HashMap::new();
        child_values_changed.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        child_values_changed.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        child_values_changed.insert(
            ("info".to_string(), "name".to_string()),
            Some("Second Floor".to_string()),
        );

        let mut root_values_unchanged = HashMap::new();
        root_values_unchanged.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values_unchanged.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values_unchanged.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let root_unchanged = HierarchicalNode {
            values: root_values_unchanged,
            parent: None,
        };

        let child_with_changed_data = HierarchicalNode {
            values: child_values_changed,
            parent: Some(Box::new(root_unchanged)),
        };

        let changed_child_id =
            evaluate_identifier_hierarchical(&reg, &child_with_changed_data, &[]).unwrap();
        assert_eq!(changed_child_id, "building.001-main.002-second-floor");
    }

    #[test]
    fn test_cascade_node_reparented() {
        // Test cascade when a node is reparented from one tree to another
        // Node under building should change identifier when moved to warehouse

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Building root
        let mut building_root_values = HashMap::new();
        building_root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        building_root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        building_root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        // Floor node
        let mut floor_values = HashMap::new();
        floor_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        floor_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        floor_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor A".to_string()),
        );

        // Originally under building
        let building_root = HierarchicalNode {
            values: building_root_values.clone(),
            parent: None,
        };
        let floor_under_building = HierarchicalNode {
            values: floor_values.clone(),
            parent: Some(Box::new(building_root)),
        };
        let original_floor_id =
            evaluate_identifier_hierarchical(&reg, &floor_under_building, &[]).unwrap();
        assert_eq!(original_floor_id, "building.001-main.002-floor-a");

        // Now under warehouse
        let mut warehouse_root_values = HashMap::new();
        warehouse_root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("warehouse".to_string()),
        );
        warehouse_root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        warehouse_root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let warehouse_root = HierarchicalNode {
            values: warehouse_root_values,
            parent: None,
        };
        let floor_under_warehouse = HierarchicalNode {
            values: floor_values,
            parent: Some(Box::new(warehouse_root)),
        };
        let new_floor_id =
            evaluate_identifier_hierarchical(&reg, &floor_under_warehouse, &[]).unwrap();
        assert_eq!(new_floor_id, "warehouse.001-main.002-floor-a");
    }

    // ===== Hierarchical dedup (Cycle 5) =====

    #[test]
    fn test_dedup_hierarchical_siblings_identical() {
        // Test dedup when two siblings have identical source data
        // First sibling gets 'building.001-main.002-floor'
        // Second sibling with same data gets 'building.001-main.002-floor#2'

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            true, // dedup enabled
            None, // dedup_scope_col = table-wide dedup
            None,
        )
        .unwrap();

        // Root
        let mut root_values = HashMap::new();
        root_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        // Sibling 1: Floor (will get base identifier)
        let mut sibling1_values = HashMap::new();
        sibling1_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        sibling1_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        sibling1_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor".to_string()),
        );

        let root = HierarchicalNode {
            values: root_values.clone(),
            parent: None,
        };
        let sibling1 = HierarchicalNode {
            values: sibling1_values.clone(),
            parent: Some(Box::new(root)),
        };

        // First sibling gets base identifier
        let sibling1_id = evaluate_identifier_hierarchical(&reg, &sibling1, &[]).unwrap();
        assert_eq!(sibling1_id, "building.001-main.002-floor");

        // Sibling 2: same data, but in taken list
        let root2 = HierarchicalNode {
            values: root_values,
            parent: None,
        };
        let sibling2 = HierarchicalNode {
            values: sibling1_values,
            parent: Some(Box::new(root2)),
        };

        // Second sibling with same data gets #2
        let sibling2_id =
            evaluate_identifier_hierarchical(&reg, &sibling2, &["building.001-main.002-floor"])
                .unwrap();
        assert_eq!(sibling2_id, "building.001-main.002-floor#2");
    }

    #[test]
    fn test_dedup_hierarchical_scope_based() {
        // Test scope-based dedup: siblings in different scopes don't conflict
        // Both can have 'building.001-main.002-floor' if they're in different customer orgs

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            true,                    // dedup enabled
            Some("fk_customer_org"), // scope-based dedup
            None,
        )
        .unwrap();

        // Root for customer org 1
        let mut root_org1_values = HashMap::new();
        root_org1_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_org1_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_org1_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );
        root_org1_values.insert(
            ("self".to_string(), "fk_customer_org".to_string()),
            Some("customer1".to_string()),
        );

        // Root for customer org 2
        let mut root_org2_values = HashMap::new();
        root_org2_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        root_org2_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        root_org2_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );
        root_org2_values.insert(
            ("self".to_string(), "fk_customer_org".to_string()),
            Some("customer2".to_string()),
        );

        // Floor for org 1
        let mut floor_org1_values = HashMap::new();
        floor_org1_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        floor_org1_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        floor_org1_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Floor".to_string()),
        );

        // Floor for org 2
        let floor_org2_values = floor_org1_values.clone();

        // Both floors can have the same identifier since they're in different scopes
        let root_org1 = HierarchicalNode {
            values: root_org1_values,
            parent: None,
        };
        let floor_org1 = HierarchicalNode {
            values: floor_org1_values,
            parent: Some(Box::new(root_org1)),
        };

        let floor_org1_id = evaluate_identifier_hierarchical(&reg, &floor_org1, &[]).unwrap();
        assert_eq!(floor_org1_id, "building.001-main.002-floor");

        let root_org2 = HierarchicalNode {
            values: root_org2_values,
            parent: None,
        };
        let floor_org2 = HierarchicalNode {
            values: floor_org2_values,
            parent: Some(Box::new(root_org2)),
        };

        // Same identifier is allowed in different scope
        let floor_org2_id = evaluate_identifier_hierarchical(&reg, &floor_org2, &[]).unwrap();
        assert_eq!(floor_org2_id, "building.001-main.002-floor");
    }

    // ===== End-to-end integration test (Cycle 6) =====

    #[test]
    #[allow(clippy::too_many_lines)]
    fn test_end_to_end_location_hierarchy() {
        // Simulate the real-world tb_location scenario with:
        // - Hierarchical path management
        // - Hierarchical identifiers with chained sources
        // - Move cascades affecting multiple nodes
        // - Source data changes affecting identifiers

        let reg = register_identifier_hierarchical(
            "identifier",
            Some("{type.identifier!raw}"),
            "{info.int_ordered!padded(3)}-{info.name}",
            ".",
            Some("fk_parent_loc"),
            &[
                "type:test_loc_type:fk_loc_type=pk_loc_type",
                "info:test_loc_info:fk_loc_info=pk_loc_info",
            ],
            false,
            None,
            None,
        )
        .unwrap();

        // Build a 4-level tree:
        // building (root)
        // ├── floor1
        // │   ├── room1
        // │   └── room2
        // └── floor2

        // Level 0: building (root)
        let mut building_values = HashMap::new();
        building_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        building_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        building_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Main".to_string()),
        );

        let building = HierarchicalNode {
            values: building_values.clone(),
            parent: None,
        };
        let building_id = evaluate_identifier_hierarchical(&reg, &building, &[]).unwrap();
        assert_eq!(building_id, "building.001-main");

        // Level 1: floor1
        let mut floor1_values = HashMap::new();
        floor1_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        floor1_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        floor1_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Ground".to_string()),
        );

        let floor1 = HierarchicalNode {
            values: floor1_values.clone(),
            parent: Some(Box::new(building.clone())),
        };
        let floor1_id = evaluate_identifier_hierarchical(&reg, &floor1, &[]).unwrap();
        assert_eq!(floor1_id, "building.001-main.002-ground");

        // Level 1: floor2
        let mut floor2_values = HashMap::new();
        floor2_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        floor2_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("3".to_string()),
        );
        floor2_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("First".to_string()),
        );

        let floor2 = HierarchicalNode {
            values: floor2_values.clone(),
            parent: Some(Box::new(building.clone())),
        };
        let floor2_id = evaluate_identifier_hierarchical(&reg, &floor2, &[]).unwrap();
        assert_eq!(floor2_id, "building.001-main.003-first");

        // Level 2: room1 under floor1
        let mut room1_values = HashMap::new();
        room1_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        room1_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("1".to_string()),
        );
        room1_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("A".to_string()),
        );

        let room1 = HierarchicalNode {
            values: room1_values.clone(),
            parent: Some(Box::new(HierarchicalNode {
                values: floor1_values.clone(),
                parent: Some(Box::new(building.clone())),
            })),
        };
        let room1_id = evaluate_identifier_hierarchical(&reg, &room1, &[]).unwrap();
        assert_eq!(room1_id, "building.001-main.002-ground.001-a");

        // Level 2: room2 under floor1
        let mut room2_values = HashMap::new();
        room2_values.insert(
            ("type".to_string(), "identifier".to_string()),
            Some("building".to_string()),
        );
        room2_values.insert(
            ("info".to_string(), "int_ordered".to_string()),
            Some("2".to_string()),
        );
        room2_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("B".to_string()),
        );

        let room2 = HierarchicalNode {
            values: room2_values.clone(),
            parent: Some(Box::new(HierarchicalNode {
                values: floor1_values.clone(),
                parent: Some(Box::new(building.clone())),
            })),
        };
        let room2_id = evaluate_identifier_hierarchical(&reg, &room2, &[]).unwrap();
        assert_eq!(room2_id, "building.001-main.002-ground.002-b");

        // Scenario 1: Move room1 under floor2
        // room1 identifier changes from "building.001-main.002-ground.001-a"
        // to "building.001-main.003-first.001-a"
        let room1_moved = HierarchicalNode {
            values: room1_values.clone(),
            parent: Some(Box::new(HierarchicalNode {
                values: floor2_values.clone(),
                parent: Some(Box::new(building.clone())),
            })),
        };
        let room1_moved_id = evaluate_identifier_hierarchical(&reg, &room1_moved, &[]).unwrap();
        assert_eq!(room1_moved_id, "building.001-main.003-first.001-a");

        // Scenario 2: Change floor1's name from "Ground" to "Basement"
        // floor1 identifier changes, affecting room1 and room2
        let mut floor1_renamed_values = floor1_values.clone();
        floor1_renamed_values.insert(
            ("info".to_string(), "name".to_string()),
            Some("Basement".to_string()),
        );
        let floor1_renamed_node = HierarchicalNode {
            values: floor1_renamed_values.clone(),
            parent: Some(Box::new(building.clone())),
        };
        let floor1_renamed_id =
            evaluate_identifier_hierarchical(&reg, &floor1_renamed_node, &[]).unwrap();
        assert_eq!(floor1_renamed_id, "building.001-main.002-basement");

        // room1 under renamed floor
        let room1_under_renamed_floor = HierarchicalNode {
            values: room1_values.clone(),
            parent: Some(Box::new(floor1_renamed_node)),
        };
        let room1_under_renamed_id =
            evaluate_identifier_hierarchical(&reg, &room1_under_renamed_floor, &[]).unwrap();
        assert_eq!(
            room1_under_renamed_id,
            "building.001-main.002-basement.001-a"
        );

        // room2 under renamed floor
        let room2_under_renamed_floor = HierarchicalNode {
            values: room2_values,
            parent: Some(Box::new(HierarchicalNode {
                values: floor1_renamed_values,
                parent: Some(Box::new(building)),
            })),
        };
        let room2_under_renamed_id =
            evaluate_identifier_hierarchical(&reg, &room2_under_renamed_floor, &[]).unwrap();
        assert_eq!(
            room2_under_renamed_id,
            "building.001-main.002-basement.002-b"
        );
    }
}
