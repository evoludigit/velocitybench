# Phase 1: Foundation & FraiseQL Schema Design

## Objective

Design and implement the FraiseQL schema that serves as the single source of truth for all language backends, ensuring all compilers generate identical APIs and behavior.

## Success Criteria

- [ ] FraiseQL schema defined in Python (using Python generator)
- [ ] Schema compiles to `schema.json` with zero errors
- [ ] Schema compiles to `schema.compiled.json` via CLI
- [ ] All 5 languages can generate equivalent schema (samples tested)
- [ ] Shared schema directory structure created
- [ ] Database schema matches FraiseQL definitions
- [ ] All types, queries, and mutations documented
- [ ] Build system integration complete

## TDD Cycles

### Cycle 1: Core Type Definitions

**RED**: Write test verifying FraiseQL schema loads and validates
```python
# tests/integration/test_fraiseql_schema.py
def test_schema_loads_and_validates():
    schema = load_fraiseql_schema()
    assert schema is not None
    assert schema.types is not None
    assert schema.root_query is not None
    # Must reference valid database tables
    for query in schema.root_query.fields:
        assert query.sql_source in database.list_objects()
```

**GREEN**: Create minimal Python schema
```python
# fraiseql-schema/schema.fraiseql.py
from fraiseql import type as fraiseql_type, query as fraiseql_query

@fraiseql_type
class User:
    id: int
    name: str
    email: str | None

@fraiseql_query(sql_source="v_users")
def users(limit: int = 10) -> list[User]:
    """Get users."""
    pass
```

**REFACTOR**: Add proper organization, docstrings, and validation

**CLEANUP**: Run linters, verify schema exports cleanly

---

### Cycle 2: Complex Types & Relationships

**RED**: Test nested types and relationships compile correctly
```python
def test_schema_relationships():
    schema = load_fraiseql_schema()
    post_type = schema.types["Post"]
    assert post_type.fields["author"].type.name == "User"
    assert post_type.fields["comments"].is_list == True
```

**GREEN**: Add related types (Post, Comment, etc.)
```python
@fraiseql_type
class Post:
    id: int
    title: str
    author: User  # Relationship
    comments: list[Comment]

@fraiseql_type
class Comment:
    id: int
    content: str
    author: User
    post: Post
```

**REFACTOR**: Add SQL bindings for relationships via joins

**CLEANUP**: Verify all relationships are bidirectional and consistent

---

### Cycle 3: Mutations & State Changes

**RED**: Test mutations compile with proper signatures
```python
def test_mutations_exist():
    schema = load_fraiseql_schema()
    assert "createUser" in schema.root_mutation.fields
    assert "updateUser" in schema.root_mutation.fields
    assert "deleteUser" in schema.root_mutation.fields
```

**GREEN**: Add mutation definitions
```python
@fraiseql_mutation(sql_source="fn_create_user")
def createUser(name: str, email: str) -> User:
    """Create new user."""
    pass

@fraiseql_mutation(sql_source="fn_update_user")
def updateUser(id: int, name: str | None = None) -> User:
    """Update user."""
    pass
```

**REFACTOR**: Add validation decorators and authorization metadata

**CLEANUP**: Ensure mutation signatures match database procedures

---

### Cycle 4: Analytics Support

**RED**: Test fact tables and aggregates compile
```python
def test_analytics_compiles():
    schema = load_fraiseql_schema()
    assert "salesByCategory" in schema.root_query.fields
    result_type = schema.root_query.fields["salesByCategory"].type
    assert "revenue" in result_type.fields
    assert "count" in result_type.fields
```

**GREEN**: Add fact table definitions
```python
from fraiseql import fact_table, aggregate_query

@fact_table(
    table_name="tf_sales",
    measures=["revenue", "quantity"],
    dimension_paths=[
        {"name": "category", "json_path": "metadata->>'category'"}
    ]
)
class SalesMetrics:
    revenue: float
    quantity: int

@aggregate_query(fact_table="tf_sales")
def salesByCategory(category: str) -> dict:
    """Sales aggregated by category."""
    pass
```

**REFACTOR**: Add proper measure definitions and dimension bindings

**CLEANUP**: Verify fact tables match database structure

---

### Cycle 5: Schema Export & Compilation

**RED**: Test schema exports to JSON and compiles via CLI
```python
def test_schema_exports_to_json():
    export_fraiseql_schema("schema.json")
    assert Path("schema.json").exists()
    schema_data = json.loads(Path("schema.json").read_text())
    assert schema_data["types"]
    assert schema_data["query"]
    assert schema_data["mutation"]

def test_schema_compiles_with_cli():
    result = subprocess.run(
        ["fraiseql-cli", "compile", "schema.json"],
        capture_output=True
    )
    assert result.returncode == 0
    assert Path("schema.compiled.json").exists()
```

**GREEN**: Integrate schema export and CLI compilation

**REFACTOR**: Add proper error handling and validation

**CLEANUP**: Remove debug output, verify paths are correct

---

### Cycle 6: Multi-Language Schema Equivalence

**RED**: Test that Python, TypeScript, Go, Java, PHP schemas produce identical output
```python
def test_all_languages_generate_equivalent_schema():
    # Generate from Python
    python_schema = generate_schema_python()

    # Generate from TypeScript
    ts_schema = generate_schema_typescript()

    # Generate from Go, Java, PHP...

    # All must have identical structure
    assert python_schema.types == ts_schema.types
    assert python_schema.root_query == ts_schema.root_query
    assert python_schema.root_mutation == ts_schema.root_mutation
```

**GREEN**: Create schema definitions in all 5 languages
- `schema.fraiseql.py` (primary)
- `schema.fraiseql.ts` (TypeScript equivalent)
- `schema.fraiseql.go` (Go equivalent)
- `schema.fraiseql.java` (Java equivalent)
- `schema.fraiseql.php` (PHP equivalent)

**REFACTOR**: Unify definitions and document equivalence

**CLEANUP**: Verify all language versions compile without errors

---

## Directory Structure Created

```
velocitybench/
├── fraiseql-schema/
│   ├── README.md                 # Schema documentation
│   ├── schema.fraiseql.py        # Python source of truth
│   ├── schema.fraiseql.ts        # TypeScript equivalent
│   ├── schema.fraiseql.go        # Go equivalent
│   ├── schema.fraiseql.java      # Java equivalent
│   ├── schema.fraiseql.php       # PHP equivalent
│   ├── schema.json               # Exported intermediate
│   ├── schema.compiled.json      # Compiled optimized
│   ├── types.py                  # Type definitions (reusable)
│   ├── queries.py                # Query definitions
│   ├── mutations.py              # Mutation definitions
│   └── analytics.py              # Fact tables and aggregates
│
└── tests/integration/
    └── test_fraiseql_schema.py   # Schema validation tests
```

## Database Alignment

**Prerequisites**:
- Database schema matches all FraiseQL `sql_source` references
- All views (`v_*`) exist and return correct shape
- All procedures (`fn_*`) exist with correct signatures
- All tables referenced in fact tables exist

**Verification**:
```sql
-- All must return results
SELECT COUNT(*) FROM information_schema.views WHERE table_name LIKE 'v_%';
SELECT COUNT(*) FROM information_schema.routines WHERE routine_name LIKE 'fn_%';
SELECT COUNT(*) FROM tf_sales;  -- Fact tables
```

## Dependencies

- Requires: Database schema current
- Blocks: Phases 2-6 (all backend implementations)

## Status

[ ] Not Started | [~] In Progress | [ ] Complete

## Notes

- Schema is the **single source of truth** for all backends
- All language versions must be functionally identical
- No language-specific hacks or workarounds
- Build system must automatically verify parity
