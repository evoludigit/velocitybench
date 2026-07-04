# pg_treekey — Product Requirements Document

## Problem

Enterprise PostgreSQL schemas with hierarchical data share three universal
maintenance burdens:

**1. ltree path boilerplate.**
Every hierarchical table (`tb_location`, `tb_organizational_unit`,
`tb_organization`, `tb_industry`, `tb_product`, ...) stores a materialized
`path LTREE` column that must equal `parent.path || pk`. This invariant is
maintained by hand: every mutation function calls `recalculate_tree_path()`
explicitly, and when a node moves, a loop updates all descendants. The logic is
identical across every hierarchical table — it is pure boilerplate.

**2. A bespoke identifier grammar with boilerplate primitives.**
Every entity has a human-readable `identifier` column computed from its own
fields and the identifiers of related entities. A consistent grammar has
emerged across 24 `recalcid_*` functions:

| Separator | Semantic role |
|-----------|--------------|
| `\|`      | scope boundary — `org_prefix \| content` |
| `.`       | hierarchy level — `parent.child` |
| `∘`       | object composition — `machine∘location∘orgunit` |
| `—`       | technical tuple — `router—gateway—ip` |
| `#n`      | deduplication suffix |

Each of those 24 functions reimplements the same three primitives:

- **Slugification** — `unaccent(lower(regexp_replace(...)))` inlined everywhere
- **Scope stripping** — `REGEXP_REPLACE(child.identifier, '^' || org.identifier || '\|', '')` inlined everywhere
- **Deduplication** — a `LOOP … EXIT WHEN NOT EXISTS … suffix + 1` inlined everywhere

**3. Identifier recomputation on any foreign key change.**
Because identifiers embed data from related entities, a change to
`machine.identifier` invalidates `allocation.identifier` for every allocation
that machine appears in. This cascading recomputation is currently manual and
error-prone.

---

## What pg_treekey is

A focused PostgreSQL extension (pgrx 0.16.1, Rust) with two layers:

**Layer 1 — Primitives** (always available, no configuration):
- `slugify()` — canonical slug, Unicode-correct, no `unaccent` dependency
- `scope_strip()` — remove leading scope prefix from an embedded identifier
- `identifier_next()` — find next available `base[#n]`
- `manage_path()` — install BEFORE + AFTER triggers for ltree path maintenance

**Layer 2 — Declarative registration** (optional, full automation):
- `register_identifier()` — declare the composition formula for any entity's
  identifier column; pg_treekey installs triggers that maintain it automatically
  and cascades recomputation when source data changes

When Layer 2 is used, the application's `recalcid_*` functions are **deleted
entirely**. The composition formula lives in the registration, not in SQL.

---

## What pg_treekey is not

- Not a full slug library (no routing, no URL generation).
- Not an ORM or code generator.
- Not a replacement for `ltree` — it depends on `ltree` and augments it.
- Not suitable for identifier formulas that require application-level business
  logic (e.g. conditional rules driven by runtime state outside the database).

---

## Primitives

### 1. `slugify(input text [, separator text]) → text`

Converts arbitrary text to a URL-safe slug.

**Algorithm:**
1. Unicode NFKD decomposition — decomposes accented characters into base +
   combining mark (`é` → `e` + combining acute).
2. Strip non-ASCII combining marks — keep the base character, drop the mark.
3. Lowercase.
4. Collapse runs of non-alphanumeric characters to `separator` (default `-`).
5. Trim leading/trailing `separator`.

**Rationale for Rust:**  The `unaccent` extension uses an incomplete dictionary
(`œ` unhandled, `ß` → `ss` missing, etc.). Rust's `unicode-normalization` crate
implements the full Unicode standard with no external dependency.

```sql
slugify('Île-de-France')         → 'ile-de-france'
slugify('Bâtiment B')            → 'batiment-b'
slugify('001 - Main Floor')      → '001-main-floor'
slugify('Hébergement & Accueil') → 'hebergement-accueil'
slugify('café', '.')             → 'cafe'
```

```sql
CREATE FUNCTION pg_treekey.slugify(
    input     text,
    separator text DEFAULT '-'
) RETURNS text LANGUAGE c STRICT IMMUTABLE PARALLEL SAFE;
```

---

### 2. `scope_strip(identifier text, scope text) → text`

Removes a leading `scope|` prefix from an embedded identifier. Returns
`identifier` unchanged if it does not start with `scope|`.

```sql
scope_strip('acme|model.SN123', 'acme')  → 'model.SN123'
scope_strip('other|x',          'acme')  → 'other|x'   -- not stripped
scope_strip('acme|x',           'acme')  → 'x'
```

```sql
CREATE FUNCTION pg_treekey.scope_strip(
    identifier text,
    scope      text
) RETURNS text LANGUAGE c STRICT IMMUTABLE PARALLEL SAFE;
```

---

### 3. `identifier_next(base text, taken text[]) → text`

Returns `base` if not in `taken`; otherwise `base#2`, `base#3`, … until free.

```sql
identifier_next('acme|r', ARRAY[]::text[])            → 'acme|r'
identifier_next('acme|r', ARRAY['acme|r'])             → 'acme|r#2'
identifier_next('acme|r', ARRAY['acme|r','acme|r#2']) → 'acme|r#3'
```

```sql
CREATE FUNCTION pg_treekey.identifier_next(
    base  text,
    taken text[]
) RETURNS text LANGUAGE c STRICT IMMUTABLE PARALLEL SAFE;
```

---

### 4. `manage_path(table_ref regclass, pk_col text, parent_fk_col text [, path_col text]) → void`

Installs trigger-based automatic ltree path maintenance on `table_ref`.

**BEFORE INSERT OR UPDATE OF `parent_fk_col`** — `tg_treekey_compute_path`:
```
NEW.path := CASE
    WHEN NEW.parent_fk IS NULL THEN NEW.pk::text::ltree
    ELSE (SELECT path FROM table WHERE pk = NEW.parent_fk) || NEW.pk::text
END
```

**AFTER UPDATE OF `path_col`** — `tg_treekey_cascade_path`:
```
IF NEW.path IS DISTINCT FROM OLD.path THEN
    UPDATE table SET parent_fk = parent_fk   -- re-fires BEFORE trigger
    WHERE parent_fk = NEW.pk                 -- direct children only
END IF
```

The cascade uses the BEFORE-trigger re-entry trick: forcing a no-op self-update
on each **direct child** causes the BEFORE trigger to recompute its path from
the parent's (now updated) path. Each child's path change then recursively fires
the AFTER trigger for *its* children, guaranteeing parent-before-child ordering.
The AFTER trigger is guarded by `NEW.path IS DISTINCT FROM OLD.path` — once a
subtree's paths are stable, no further triggers fire. This recursive approach
avoids `UPDATE ... ORDER BY` which is not valid PostgreSQL SQL.

```sql
SELECT pg_treekey.manage_path('tenant.tb_location',            'pk_location',            'fk_parent_location');
SELECT pg_treekey.manage_path('tenant.tb_organizational_unit', 'pk_organizational_unit', 'fk_parent_organizational_unit');
SELECT pg_treekey.manage_path('catalog.tb_industry',           'pk_industry',            'fk_parent_industry');
SELECT pg_treekey.manage_path('catalog.tb_product',            'pk_product',             'fk_parent_product');
```

---

## Declarative identifier registration

`register_identifier()` declares the full composition formula for any entity's
identifier column. pg_treekey installs a BEFORE trigger that evaluates the
formula automatically on every INSERT or UPDATE of a relevant column, and AFTER
triggers on source tables that cascade recomputation when embedded data changes.

### Template DSL

A template is a string containing literal separators and **token expressions**:

```
{alias.column[!modifier][?]}
```

| Part | Description |
|------|-------------|
| `alias` | Table alias from `sources`, or `self` for the entity's own columns |
| `column` | Column name on that alias |
| `!modifier` | Transformation applied to the value (see below) |
| `?` | Optional — if the value is NULL, this token **and the separator immediately preceding it** are omitted |

**Modifiers:**

| Modifier | Behaviour |
|----------|-----------|
| *(none)* | `slugify(value)` — default |
| `!raw` | Include value as-is, no transformation |
| `!strip` | `scope_strip(value, scope_value)` — requires `scope` declared |
| `!padded(n)` | `LPAD(value::text, n, '0')` |

Literal characters between tokens are included verbatim. All separator
characters from the grammar (`|`, `.`, `∘`, `—`, `#`) are valid literals.

### `register_identifier()` — flat mode

Used for all non-hierarchical entities.

```sql
CREATE FUNCTION pg_treekey.register_identifier(
    table_ref  regclass,          -- target table
    slug_col   text,              -- column to maintain (e.g. 'identifier')
    template   text,              -- composition formula (see DSL above)
    sources    text[],            -- source declarations (see below)
    scope      text    DEFAULT NULL,  -- alias.column that holds the scope prefix
    dedup      boolean DEFAULT false, -- append #n on conflict
    dedup_scope_col text DEFAULT NULL -- column scoping uniqueness (e.g. 'fk_customer_org')
) RETURNS void LANGUAGE c;
```

**`sources` array format** — each entry: `'alias:schema.table:local_fk=remote_pk'`

```
'org:management.tb_organization:fk_customer_org=pk_organization'
'model:catalog.tb_model:fk_model=pk_model'
'self'   -- always implicitly available; listed only for documentation
```

The `alias:table:fk=pk` declaration gives the extension everything needed to:
1. Build the JOIN clause for the BEFORE trigger query
2. Know which source table + column to watch for cascade recomputation

---

### Flat mode examples

**`tb_machine`** — `org|model.serial`

```sql
SELECT pg_treekey.register_identifier(
    table_ref := 'tenant.tb_machine',
    slug_col  := 'identifier',
    template  := '{org.identifier!raw}|{model.identifier!strip}.{self.serial_number!raw}',
    sources   := ARRAY[
        'org:management.tb_organization:fk_customer_org=pk_organization',
        'model:catalog.tb_model:fk_model=pk_model'
    ],
    scope     := 'org.identifier',
    dedup     := false
);
```

**`tb_network_configuration`** — `org|router—gateway—ip`

```sql
SELECT pg_treekey.register_identifier(
    table_ref := 'tenant.tb_network_configuration',
    slug_col  := 'identifier',
    template  := '{org.identifier!raw}|{r.hostname!raw}—{g.ip_address!raw}—{self.ip_address!raw}',
    sources   := ARRAY[
        'org:management.tb_organization:fk_customer_org=pk_organization',
        'r:tenant.tb_router:fk_router=pk_router',
        'g:tenant.tb_gateway:fk_gateway=pk_gateway'
    ],
    scope     := 'org.identifier',
    dedup     := true,
    dedup_scope_col := 'fk_customer_org'
);
```

**`tb_allocation`** — `org|daterange∘machine∘location∘orgunit?∘netconf?`

```sql
SELECT pg_treekey.register_identifier(
    table_ref := 'tenant.tb_allocation',
    slug_col  := 'identifier',
    template  := '{org.identifier!raw}|{self.allocation_daterange!raw}∘{m.identifier!strip}∘{loc.identifier!strip}∘{ou.identifier!strip?}∘{nc.identifier!strip?}',
    sources   := ARRAY[
        'org:management.tb_organization:fk_customer_org=pk_organization',
        'm:tenant.tb_machine:fk_machine=pk_machine',
        'loc:tenant.tb_location:fk_location=pk_location',
        'ou:tenant.tb_organizational_unit:fk_organizational_unit=pk_organizational_unit',
        'nc:tenant.tb_network_configuration:fk_network_configuration=pk_network_configuration'
    ],
    scope     := 'org.identifier',
    dedup     := true,
    dedup_scope_col := 'fk_customer_org'
);
```

**`tb_dataflow_field`** — `dataflow|field[|source_fieldname]` (conditional tail)

```sql
SELECT pg_treekey.register_identifier(
    table_ref := 'tenant.tb_dataflow_field',
    slug_col  := 'identifier',
    template  := '{d.identifier!raw}|{f.identifier!raw}|{self.source_fieldname!raw?}',
    sources   := ARRAY[
        'd:tenant.tb_dataflow:fk_dataflow=pk_dataflow',
        'f:catalog.tb_printoptim_field:fk_printoptim_field=pk_printoptim_field'
    ],
    scope     := NULL,   -- no org scope stripping needed
    dedup     := false
);
-- Note: the trailing '|' before {self.source_fieldname!raw?} is the separator
-- that gets dropped when source_fieldname IS NULL.
```

---

### Hierarchical mode

Used when the identifier is built by traversing the parent chain recursively.
The formula at each node is evaluated, and levels are joined with a separator.

```sql
CREATE FUNCTION pg_treekey.register_identifier(
    table_ref       regclass,
    slug_col        text,
    mode            text,          -- 'hierarchical'
    parent_fk_col   text,          -- FK to parent row in same table
    scope_template  text,          -- evaluated once at root level (the prefix)
    level_template  text,          -- evaluated at every level
    level_sep       text DEFAULT '.',
    sources         text[],
    scope           text DEFAULT NULL,
    dedup           boolean DEFAULT false,
    dedup_scope_col text DEFAULT NULL
) RETURNS void LANGUAGE c;
```

The trigger traverses the parent chain via recursive SPI query, evaluates
`level_template` at each node, concatenates with `level_sep`, and prepends the
root-evaluated `scope_template`.

**`tb_location`** — `address_id|type.000-slug.001-child`

```sql
SELECT pg_treekey.register_identifier(
    table_ref      := 'tenant.tb_location',
    slug_col       := 'identifier',
    mode           := 'hierarchical',
    parent_fk_col  := 'fk_parent_location',
    scope_template := '{addr.identifier!raw}|{type.identifier!raw}',
    level_template := '{info.int_ordered!padded(3)}-{info.name}',
    level_sep      := '.',
    sources        := ARRAY[
        'info:tenant.tb_location_info:fk_location_info=pk_location_info',
        'addr:tenant.tb_public_address:info.fk_public_address=pk_public_address',
        'type:catalog.tb_location_type:info.fk_location_type=pk_location_type'
    ],
    scope          := NULL,
    dedup          := true,
    dedup_scope_col := 'fk_customer_org'
);
```

In hierarchical mode the `scope_template` is evaluated only once for the subtree
root (using root node's joined values). The `level_template` is evaluated at
every node in the chain from root to leaf. The final identifier is:

```
scope_template_value + '.' + level_template(root) + '.' + level_template(child) + ...
```

**`tb_organizational_unit`** follows the same pattern:

```sql
SELECT pg_treekey.register_identifier(
    table_ref      := 'tenant.tb_organizational_unit',
    slug_col       := 'identifier',
    mode           := 'hierarchical',
    parent_fk_col  := 'fk_parent_organizational_unit',
    scope_template := '{org.identifier!raw}|{level.identifier!raw}',
    level_template := '{info.abbreviation!raw}-{info.name}',
    level_sep      := '.',
    sources        := ARRAY[
        'info:tenant.tb_organizational_unit_info:fk_organizational_unit_info=pk_organizational_unit_info',
        'org:management.tb_organization:info.fk_customer_org=pk_organization',
        'level:catalog.tb_organizational_unit_level:info.fk_organizational_unit_level=pk_organizational_unit_level'
    ],
    dedup          := true,
    dedup_scope_col := 'fk_customer_org'
);
```

---

### Cross-table invalidation (cascade recomputation)

When a source table's relevant column changes, all dependent identifiers must be
recomputed. pg_treekey installs this automatically from the `sources`
declaration.

Example: `tb_allocation` registers `m:tenant.tb_machine:fk_machine=pk_machine`
and references `{m.identifier!strip}`. pg_treekey therefore installs:

```sql
-- On tb_machine, AFTER UPDATE OF identifier:
CREATE TRIGGER tg_treekey_cascade_identifier_allocation_machine
AFTER UPDATE OF identifier ON tenant.tb_machine
FOR EACH ROW
WHEN (NEW.identifier IS DISTINCT FROM OLD.identifier)
EXECUTE FUNCTION tg_treekey_cascade_source_change(
    'tenant.tb_allocation',   -- dependent table
    'identifier',             -- column to recompute
    'fk_machine',             -- FK in dependent table
    'pk_machine'              -- PK in source table
);
```

The cascade trigger calls the same evaluation function as the BEFORE trigger on
`tb_allocation`, scoped to the rows affected by the source change.

This means: a machine is renamed → `tb_machine.identifier` changes → trigger
fires → all allocations for that machine recompute their identifier automatically.
No application code needed.

The dependency graph for cascade triggers is stored in `managed_identifier_sources`
(see Schema below) and is used by `DROP EXTENSION` cleanup.

---

## Effect on the application layer

### Before pg_treekey

- `core.recalculate_tree_path` — 80 lines, called from every mutation
- `core.recalcid_location` — 150 lines
- `core.recalcid_allocation` — 80 lines
- `core.recalcid_machine`, `recalcid_network_configuration`, … ×24
- `core.recalculation_context` — composite type threading scope through all of the above
- Cascade loops in `update_location`, `update_organizational_unit`, etc.
- Manual `PERFORM core.recalcid_*()` calls in every mutation

### After pg_treekey

**Deleted entirely:**
- `core.recalculate_tree_path`
- All 24 `core.recalcid_*` functions
- `core.recalculation_context` type
- All `PERFORM core.recalcid_*()` call sites in mutations
- All cascade loops in mutation functions

**What replaces them:**  
One `SELECT pg_treekey.register_identifier(...)` call per entity in the DDL.
Mutation functions write to base tables and return — identifier maintenance is
fully database-layer.

### pg_tviews integration

With `manage_path` maintaining `path` via triggers, the pg_tviews hierarchy
cascade limitation documented in tv_location is resolved:

1. Mutation updates `tb_location_info.name`
2. pg_tviews trigger fires → `tv_location` row refreshed ✓
3. `tg_treekey_cascade_path` fires → descendant `tb_location.path` updated
4. Each descendant update fires its own pg_tviews trigger → descendant rows refreshed ✓
5. `tg_treekey_cascade_identifier_*` fires → descendant `tb_location.identifier` recomputed ✓

No manual cascade loops. No known limitations on tv_location.

---

## Schema

```sql
CREATE SCHEMA pg_treekey;

-- Registered ltree path managements
CREATE TABLE pg_treekey.managed_paths (
    pk_managed_path bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id              uuid        NOT NULL DEFAULT gen_random_uuid(),
    table_oid       oid         NOT NULL UNIQUE,
    pk_col          text        NOT NULL,
    parent_fk_col   text        NOT NULL,
    path_col        text        NOT NULL DEFAULT 'path',
    registered_at   timestamptz NOT NULL DEFAULT now()
);

-- Registered identifier compositions
CREATE TABLE pg_treekey.managed_identifiers (
    pk_managed_identifier bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id              uuid         NOT NULL DEFAULT gen_random_uuid(),
    table_oid       oid          NOT NULL,
    slug_col        text         NOT NULL,
    mode            text         NOT NULL DEFAULT 'flat',   -- 'flat' | 'hierarchical'
    -- flat mode
    template        text,
    -- hierarchical mode
    parent_fk_col   text,
    scope_template  text,
    level_template  text,
    level_sep       text         NOT NULL DEFAULT '.',
    -- shared
    scope_ref       text,        -- alias.column for the scope value (used by !strip)
    dedup           boolean      NOT NULL DEFAULT false,
    dedup_scope_col text,
    registered_at   timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (table_oid, slug_col)
);

-- Source table declarations for each registered identifier
-- (drives JOIN generation and cross-table cascade trigger installation)
CREATE TABLE pg_treekey.managed_identifier_sources (
    pk_managed_identifier_source bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id                   uuid   NOT NULL DEFAULT gen_random_uuid(),
    fk_managed_identifier bigint NOT NULL
        REFERENCES pg_treekey.managed_identifiers(pk_managed_identifier),
    alias                text   NOT NULL,
    source_oid           oid    NOT NULL,   -- source table OID
    local_fk_col         text   NOT NULL,   -- FK column in the registered table
    remote_pk_col        text   NOT NULL,   -- PK column in the source table
    intermediate_alias   text,              -- NULL for direct FK; alias name for
                                            -- chained FK (e.g. 'info' when the
                                            -- source decl is 'info.fk_col=pk')
    watch_cols           text[],            -- source columns that trigger recomputation
                                            -- NULL = watch all (determined at parse time)
    UNIQUE (fk_managed_identifier, alias)
);
```

---

## Trigger evaluation model

The extension interprets templates at trigger-fire time rather than generating
PL/pgSQL code at registration time. The single generic Rust trigger function
`tg_treekey_evaluate_identifier()` is shared across all registrations:

1. Read registration from `managed_identifiers` (cached in shared memory after
   first read per backend).
2. Execute a single SPI query joining all declared sources to resolve token values.
3. Walk the parsed template, apply modifiers, concatenate output.
4. For hierarchical mode: execute a recursive SPI query traversing parent chain;
   evaluate `level_template` at each node; join with `level_sep`.
5. If `dedup`: collect existing identifiers for this scope, call `identifier_next()`.
6. Assign `NEW.slug_col := result`.

Template parsing and the source JOIN query are pre-computed at registration time
and stored in `managed_identifiers` as a compiled form, so trigger-fire cost is
one SPI query + string concatenation.

---

## Non-goals

- No support for non-integer PKs in `manage_path` (ltree nodes must be integers;
  UUID-keyed tables cannot use path management).
- No support for identifier formulas requiring runtime application state outside
  the database.
- No multi-column paths.
- No support for `path` columns using anything other than `pk::text` as node labels.
- `register_identifier` does not validate that the resulting identifier actually
  satisfies any UNIQUE constraint — that remains the schema's responsibility.

---

## Implementation plan

### Phase 1 — Core primitives
- `slugify()` (Rust, `unicode-normalization` crate)
- `scope_strip()` (Rust)
- `identifier_next()` (Rust)
- Unit tests via `pg_test`

### Phase 2 — Path management
- `tg_treekey_compute_path()` trigger (Rust, SPI)
- `tg_treekey_cascade_path()` trigger (Rust, SPI)
- `manage_path()` — installs triggers, records in `managed_paths`
- Integration tests: insert sets path; move node updates all descendants

### Phase 3 — Flat identifier registration
- Template parser (Rust): tokenise `{alias.column!modifier?}` + literals
- `register_identifier()` flat mode: parse template, validate sources,
  install BEFORE trigger, record in catalog
- `tg_treekey_evaluate_identifier()` generic trigger (Rust, SPI)
- Cross-table cascade trigger installation from sources
- Integration tests: all flat-mode entities (machine, allocation, netconf, dataflow)

### Phase 4 — Hierarchical identifier registration
- `register_identifier()` hierarchical mode: recursive SPI traversal
- Integration tests: location, organizational_unit

### Phase 5 — Integration in printoptim_backend
- Install extension
- Register all 10 hierarchical tables with `manage_path`
- Register all 24 entities with `register_identifier`
- Delete all `core.recalcid_*` functions
- Delete `core.recalculate_tree_path`
- Delete `core.recalculation_context`
- Remove all `PERFORM core.recalcid_*()` call sites from mutations
- Verify pg_tviews cascade now works correctly for tv_location

### Phase 6 — Finalize
- Documentation
- Security audit (identifier validation on column args; SPI injection surface)
- Archaeology removal

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| `pgrx = "=0.16.1"` | PostgreSQL extension framework |
| `unicode-normalization` | NFKD decomposition for `slugify` |
| `ltree` (built-in PostgreSQL extension) | Path column type for `manage_path` |

No runtime dependency on `unaccent`. No Cargo.lock divergence from pg_tviews.

---

## Security considerations

- `manage_path` and `register_identifier` accept `regclass` for the table
  argument — PostgreSQL resolves and permission-checks the OID before the
  function runs. Callers must have `TRIGGER` privilege on the target table.
- Column name arguments (`pk_col`, `parent_fk_col`, `slug_col`, alias names in
  `sources`) are used to construct DDL strings. They must match
  `^[a-z_][a-z0-9_]*$`; the function raises an error on invalid input.
- Template literals are stored verbatim and concatenated into identifier output —
  they are not executed as SQL. No injection surface.
- The SPI query built from `sources` declarations uses parameterised queries
  (`$1`, `$2`) for all runtime values — no dynamic SQL with user data.

---

## Success criteria

**Primitives:**
- [ ] `slugify('Île-de-France')` → `'ile-de-france'` with no `unaccent` installed
- [ ] `slugify('œuvre')` → `'oeuvre'` (handled correctly; `unaccent` would fail)
- [ ] `scope_strip('acme|x.y', 'acme')` → `'x.y'`
- [ ] `identifier_next('x', ARRAY['x','x#2'])` → `'x#3'`

**Path management:**
- [ ] INSERT into `tb_location` sets `path = pk::ltree` for root nodes
- [ ] INSERT into `tb_location` with parent sets `path = parent.path || pk`
- [ ] Moving a node updates all descendant paths within the same transaction
- [ ] `core.recalculate_tree_path` deleted from printoptim_backend

**Identifier registration:**
- [ ] `register_identifier` on `tb_machine`: INSERT computes correct identifier
- [ ] `register_identifier` on `tb_allocation`: changing `tb_machine.identifier` cascades to affected allocations
- [ ] `register_identifier` hierarchical on `tb_location`: moving a location recomputes identifiers for the full subtree
- [ ] All 24 `core.recalcid_*` functions deleted from printoptim_backend
- [ ] `core.recalculation_context` type deleted
- [ ] All `PERFORM core.recalcid_*()` call sites in mutations removed
- [ ] tv_location hierarchy cascade limitation resolved (pg_tviews + pg_treekey cooperate correctly)
