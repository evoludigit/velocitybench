# Phase 1: Foundation & Schema Definition

## Objective

Define a unified GraphQL schema for benchmarking, author it in all 5 languages to validate generator equivalence, and establish compilation baseline.

## Success Criteria

- [ ] Schema defined in Python (primary)
- [ ] Schema equivalent defined in TypeScript, Go, Java, PHP
- [ ] All 5 versions compile to identical `schema.json`
- [ ] `schema.compiled.json` generates without errors
- [ ] Schema validation tests pass
- [ ] Documentation of schema structure complete

## TDD Cycles

### Cycle 1: Core Schema Definition (Python)

**RED**: Write test verifying schema exports valid JSON
```python
# tests/schema/test_schema_definition.py
import json
from pathlib import Path
from fraiseql import export_schema

def test_schema_exports_valid_json():
    export_schema("schema.json")

    schema_file = Path("schema.json")
    assert schema_file.exists()

    schema = json.loads(schema_file.read_text())
    assert schema["types"] is not None
    assert schema["query"] is not None
    assert schema["mutation"] is not None

def test_schema_has_required_types():
    schema = json.loads(Path("schema.json").read_text())
    required_types = {"User", "Post", "Comment"}
    defined_types = set(schema["types"].keys())

    for type_name in required_types:
        assert type_name in defined_types
```

**GREEN**: Create minimal schema
```python
# fraiseql-schema/schema.fraiseql.py
import fraiseql
from fraiseql.scalars import ID, DateTime

@fraiseql.type
class User:
    id: ID
    name: str
    email: str
    created_at: DateTime
    is_active: bool

@fraiseql.type
class Post:
    id: ID
    title: str
    content: str
    author_id: ID
    published: bool
    created_at: DateTime

@fraiseql.type
class Comment:
    id: ID
    content: str
    author_id: ID
    post_id: ID
    created_at: DateTime

@fraiseql.query(sql_source="v_users")
def users(limit: int = 10, offset: int = 0) -> list[User]:
    """Get all users."""
    pass

@fraiseql.query(sql_source="v_posts")
def posts(
    author_id: ID | None = None,
    published: bool | None = None,
    limit: int = 10
) -> list[Post]:
    """Get posts with optional filtering."""
    pass

@fraiseql.mutation(sql_source="fn_create_user", operation="CREATE")
def create_user(name: str, email: str) -> User:
    """Create new user."""
    pass

if __name__ == "__main__":
    fraiseql.export_schema("schema.json")
```

**REFACTOR**: Add proper field documentation, validation metadata

**CLEANUP**: Ensure schema.json exports cleanly, verify formatting

---

### Cycle 2: TypeScript Schema Equivalence

**RED**: Test TypeScript schema generates identical output
```typescript
// tests/schema/test_typescript_equivalence.ts
import { exportSchema } from "../../fraiseql-schema/schema.fraiseql";
import * as fs from "fs";

test("TypeScript schema exports valid JSON", async () => {
  await exportSchema("schema-ts.json");

  const content = fs.readFileSync("schema-ts.json", "utf-8");
  const schema = JSON.parse(content);

  expect(schema.types).toBeDefined();
  expect(schema.query).toBeDefined();
});

test("TypeScript schema matches Python structure", async () => {
  const python_schema = JSON.parse(
    fs.readFileSync("schema.json", "utf-8")
  );
  const ts_schema = JSON.parse(
    fs.readFileSync("schema-ts.json", "utf-8")
  );

  expect(Object.keys(ts_schema.types).sort()).toEqual(
    Object.keys(python_schema.types).sort()
  );
});
```

**GREEN**: Create TypeScript schema
```typescript
// fraiseql-schema/schema.fraiseql.ts
import * as fraiseql from "fraiseql";

@fraiseql.Type()
class User {
  id!: fraiseql.ID;
  name!: string;
  email!: string;
  createdAt!: fraiseql.DateTime;
  isActive!: boolean;
}

@fraiseql.Type()
class Post {
  id!: fraiseql.ID;
  title!: string;
  content!: string;
  authorId!: fraiseql.ID;
  published!: boolean;
  createdAt!: fraiseql.DateTime;
}

@fraiseql.Type()
class Comment {
  id!: fraiseql.ID;
  content!: string;
  authorId!: fraiseql.ID;
  postId!: fraiseql.ID;
  createdAt!: fraiseql.DateTime;
}

@fraiseql.Query({ sqlSource: "v_users" })
users(limit: number = 10, offset: number = 0): User[] {
  return [];
}

@fraiseql.Query({ sqlSource: "v_posts" })
posts(
  authorId?: fraiseql.ID,
  published?: boolean,
  limit?: number
): Post[] {
  return [];
}

@fraiseql.Mutation({ sqlSource: "fn_create_user", operation: "CREATE" })
createUser(name: string, email: string): User {
  return new User();
}

if (require.main === module) {
  fraiseql.exportSchema("schema.json");
}
```

**REFACTOR**: Verify TypeScript structure matches Python

**CLEANUP**: Format and validate

---

### Cycle 3: Go, Java, PHP Schema Equivalence

**RED**: Test all languages generate identical schema
```python
# tests/schema/test_all_languages_equivalence.py
import json
import subprocess
from pathlib import Path

def test_all_languages_produce_identical_schema():
    """All languages must produce identical schema.json"""
    schemas = {}

    # Python
    subprocess.run(["python", "fraiseql-schema/schema.fraiseql.py"], check=True)
    schemas["python"] = json.loads(Path("schema.json").read_text())

    # TypeScript
    subprocess.run(["node", "fraiseql-schema/schema.fraiseql.ts"], check=True)
    schemas["typescript"] = json.loads(Path("schema-ts.json").read_text())

    # Go
    subprocess.run(
        ["go", "run", "fraiseql-schema/schema.fraiseql.go"],
        check=True,
        cwd="fraiseql-schema"
    )
    schemas["go"] = json.loads(Path("schema-go.json").read_text())

    # Java
    subprocess.run(
        ["mvn", "exec:java@export-schema"],
        check=True,
        cwd="fraiseql-schema/java"
    )
    schemas["java"] = json.loads(Path("schema-java.json").read_text())

    # PHP
    subprocess.run(
        ["php", "schema.fraiseql.php"],
        check=True,
        cwd="fraiseql-schema/php"
    )
    schemas["php"] = json.loads(Path("schema-php.json").read_text())

    # Compare all
    python_schema = schemas["python"]
    for lang, schema in schemas.items():
        if lang == "python":
            continue

        assert schema["types"].keys() == python_schema["types"].keys(), \
            f"{lang} has different types than Python"

        for type_name in python_schema["types"]:
            assert schema["types"][type_name] == python_schema["types"][type_name], \
                f"{lang} type {type_name} differs from Python"
```

**GREEN**: Create Go, Java, PHP schemas
```go
// fraiseql-schema/schema.fraiseql.go
package main

import (
    "github.com/fraiseql/fraiseql-go"
)

type User struct {
    ID        fraiseql.ID `fraiseql:"id"`
    Name      string      `fraiseql:"name"`
    Email     string      `fraiseql:"email"`
    CreatedAt string      `fraiseql:"createdAt"`
    IsActive  bool        `fraiseql:"isActive"`
}

type Post struct {
    ID        fraiseql.ID `fraiseql:"id"`
    Title     string      `fraiseql:"title"`
    Content   string      `fraiseql:"content"`
    AuthorID  fraiseql.ID `fraiseql:"authorId"`
    Published bool        `fraiseql:"published"`
    CreatedAt string      `fraiseql:"createdAt"`
}

type Query struct {
    Users fraiseql.Query[[]User] `fraiseql:"query,sql_source=v_users"`
    Posts fraiseql.Query[[]Post] `fraiseql:"query,sql_source=v_posts"`
}

func main() {
    fraiseql.ExportSchema(&Query{}, "schema-go.json")
}
```

Similarly for Java and PHP.

**REFACTOR**: Verify all are structurally identical

**CLEANUP**: Format all schemas

---

### Cycle 4: Schema Compilation

**RED**: Test schema compiles to optimized format
```bash
#!/bin/bash
# tests/schema/test_compilation.sh
set -e

SCHEMA_PATH="schema.json"
COMPILED_PATH="schema.compiled.json"

# Schema must exist
if [ ! -f "$SCHEMA_PATH" ]; then
    echo "Schema not found: $SCHEMA_PATH"
    exit 1
fi

# Compile with fraiseql-cli
fraiseql-cli compile "$SCHEMA_PATH" -o "$COMPILED_PATH"

# Output must exist and be valid JSON
if [ ! -f "$COMPILED_PATH" ]; then
    echo "Compilation failed: $COMPILED_PATH not generated"
    exit 1
fi

# Validate JSON
if ! jq empty "$COMPILED_PATH"; then
    echo "Compiled schema is not valid JSON"
    exit 1
fi

echo "✓ Schema compiled successfully"
```

**GREEN**: Run compilation pipeline

**REFACTOR**: Add optimization validation

**CLEANUP**: Verify output quality

---

### Cycle 5: Database Schema Validation

**RED**: Test schema matches database structure
```python
# tests/schema/test_database_alignment.py
import psycopg2
import json
from pathlib import Path

def test_schema_sql_sources_exist_in_database():
    """All sql_source references must exist in database."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()

    schema = json.loads(Path("schema.json").read_text())

    # Check all views exist
    for query_name, query_def in schema["query"].items():
        sql_source = query_def.get("sql_source")
        if sql_source:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.views WHERE table_name = %s)",
                (sql_source,)
            )
            exists = cursor.fetchone()[0]
            assert exists, f"View not found: {sql_source}"

    # Check all functions exist for mutations
    for mutation_name, mutation_def in schema.get("mutation", {}).items():
        sql_source = mutation_def.get("sql_source")
        if sql_source:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.routines WHERE routine_name = %s)",
                (sql_source,)
            )
            exists = cursor.fetchone()[0]
            assert exists, f"Function not found: {sql_source}"

    cursor.close()
    conn.close()
```

**GREEN**: Verify database structure, update if needed

**REFACTOR**: Add comprehensive validation

**CLEANUP**: Document all references

---

## Deliverables

```
fraiseql-schema/
├── schema.fraiseql.py      # Python definition (primary)
├── schema.fraiseql.ts      # TypeScript equivalent
├── schema.fraiseql.go      # Go equivalent
├── schema.fraiseql.java    # Java equivalent
├── schema.fraiseql.php     # PHP equivalent
├── schema.json             # Exported (shared)
├── schema.compiled.json    # Compiled (runtime)
├── README.md               # Schema documentation
└── tests/
    ├── test_schema_definition.py
    ├── test_equivalence.py
    └── test_database_alignment.py
```

## Database Requirements

All referenced `sql_source` values must exist:

```sql
-- Views for queries
CREATE VIEW v_users AS SELECT * FROM users;
CREATE VIEW v_posts AS SELECT * FROM posts;

-- Functions for mutations
CREATE FUNCTION fn_create_user(name TEXT, email TEXT) RETURNS RECORD AS ...;
CREATE FUNCTION fn_create_post(title TEXT, content TEXT, author_id INT) RETURNS RECORD AS ...;
```

## Dependencies

- Requires: Database schema current with all views/functions
- Blocks: Phase 2 (FraiseQL server deployment)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Python is source of truth, all others must match
- All 5 languages generate identical schema.json
- Validation ensures database alignment before compilation
- Schema is stable foundation for all subsequent phases
