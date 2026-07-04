# pg_treekey

A PostgreSQL extension for hierarchical tree key management. Automatically maintains tree paths using ltree and generates scoped, normalized identifiers.

## Features

- **Automatic path management**: Maintains `ltree` paths as you insert/update parent-child relationships
- **Hierarchical identifier generation**: Creates normalized, scoped identifiers using a template DSL
- **Template-based slugification**: Converts text to slugs using NFKD decomposition and ligature expansion
- **Safe SQL generation**: Table and column names validated against strict whitelist; all data values use parameterized bindings—no injection vectors
- **Memory-safe**: Written in Rust with careful unsafe code justification in trigger functions only

## Installation

### Prerequisites

- PostgreSQL 18+ with development headers
- Rust 1.70+ with `cargo`
- `cargo-pgrx` CLI tool
- ltree extension (usually pre-installed with PostgreSQL)

### Build and Install

```bash
# Build the extension
cargo build --release

# Install to your PostgreSQL installation
cargo pgrx install

# Create the extension in your database
CREATE EXTENSION pg_treekey;
```

Then verify installation:

```sql
\df pg_treekey.*
```

## Quick Start

### 1. Automatic Path Management

Track parent-child relationships with automatic `ltree` path updates:

```sql
-- Enable automatic path maintenance on categories table
SELECT pg_treekey.manage_path('public.categories', 'id', 'parent_id', 'path');

-- Insert data—paths are computed automatically
INSERT INTO categories (id, parent_id, name) VALUES
  (1, NULL, 'Electronics'),
  (2, 1, 'Computers'),
  (3, 2, 'Laptops');

-- Query by path
SELECT id, name, path FROM categories WHERE path <@ '1.2';
```

### 2. Hierarchical Identifier Registration

Register templates to auto-generate scoped, normalized identifiers:

```sql
-- Register a template for SKUs
SELECT pg_treekey.register_identifier(
  'products',
  'sku',
  '[category.name|slugify]-[name|slugify]-[id|padded(4)]'
);

-- Insert a product—SKU is auto-generated from template
INSERT INTO products (id, name, category_id, sku) 
VALUES (1, 'Dell XPS 13', 42, DEFAULT);

-- Auto-generated: electronics-dell-xps-13-0001
SELECT id, name, sku FROM products WHERE id = 1;
```

## Template DSL

The template syntax supports expressions with optional modifiers:

```
[field]              → Use field value as-is
[field|slugify]      → NFKD decompose, strip accents, lowercase
[field|raw]          → No transformation
[field|padded(4)]    → Zero-pad numeric value to 4 characters
[field|strip]        → Remove scope prefix (e.g., "foo" from "foo|bar")
```

### Examples

```
[first_name|slugify]-[last_name|slugify]
→ "Jean-Claude" becomes "jean-claude"

[product_name|slugify]-[sku|raw]
→ "Café Mocha" + "SKU-001" becomes "cafe-mocha-SKU-001"

[year|raw].[month|padded(2)].[day|padded(2)]
→ 2025/3/5 becomes "2025.03.05"
```

### Ligature Expansion

Text is normalized using NFKD decomposition after ligature expansion:

- `fi` → `f` + `i` (so "wifi" → "wifi", not "w1f1")
- `æ` → `a` + `e` (so "Æliza" → "aeliza")
- `œ` → `o` + `e` (so "œuvre" → "oeuvre")

## API Reference

### `manage_path(table, pk_col, parent_fk_col, path_col)`

Registers automatic path maintenance for a parent-child table.

**Arguments:**
- `table` – Table name or `regclass` (resolves to public.table_name by default)
- `pk_col` – Primary key column name
- `parent_fk_col` – Parent foreign key column name
- `path_col` – ltree column to maintain (default: 'path')

**Example:**
```sql
SELECT pg_treekey.manage_path('org_units', 'id', 'parent_unit_id', 'hierarchy');
```

### `register_identifier(table, slug_col, template [, mode])`

Registers an identifier template and enables auto-generation.

**Arguments:**
- `table` – Table name
- `slug_col` – Column to populate with generated identifier
- `template` – DSL template string (see Template DSL above)
- `mode` – Registration mode: `'flat'` (default) or `'hierarchical'`

**Flat mode:** Each row gets its own independent identifier
**Hierarchical mode:** Identifiers incorporate parent-scoped paths

**Example (flat):**
```sql
SELECT pg_treekey.register_identifier(
  'users',
  'username',
  '[first_name|slugify].[last_name|slugify]'
);
```

**Example (hierarchical with chained FK):**
```sql
SELECT pg_treekey.register_identifier(
  'categories',
  'full_key',
  '[parent.name|slugify]/[name|slugify]',
  'hierarchical'
);
```

## Design Notes

### Column Name Validation

All column and table names are validated before use:
- Must match `^[a-z_][a-z0-9_]*$` (lowercase identifiers only)
- Rejects uppercase, spaces, quotes, semicolons, and other special characters
- Error messages include the specific invalid character and position

### SPI Query Safety

All dynamic SQL is constructed with parameterized bindings. Template literals (table names, column names) are concatenated only after validation.

### Trigger Model

A single generic Rust trigger function interprets stored templates at fire time. Templates and parsed state are cached in backend-local shared memory after first read.

### Limitations

- Literal braces `{` and `}` in templates are not supported (reserved for future expression syntax)
- Chained foreign key sources are limited to single hops (e.g., `parent.name` is allowed, but `parent.parent.name` is not)
- Source tables must be in the same database (cross-database joins not supported)

## Testing

Run the test suite:

```bash
cargo test
```

All 153 tests pass, covering:
- Slugification with ligatures and accents
- Template parsing and validation
- Hierarchical path computation
- Edge cases (NULL values, empty strings, very long identifiers)

## Security

- **Minimal unsafe code** – Unsafe blocks only in trigger functions for tuple manipulation; all unsafe code has explicit `SAFETY:` justification comments
- **SQL injection prevention** – Table and column names validated against strict regex `^[a-z_][a-z0-9_]*$`; all data values use parameterized bindings
- **Input validation** – Column names validated before use; templates parsed and validated before execution
- **Catalog access control** – Catalog tables (`managed_identifiers`, `managed_paths`) revoked from public; only extension functions can modify them

## License

MIT
