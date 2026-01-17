```markdown
---
title: "Intermediate Representation (IR) Design: Breaking Free from Schema Hell"
date: "2023-11-15"
author: "Alex Carter"
description: "Learn how to standardize database schemas across input formats using IR design—a powerful pattern for backend engineers."
tags: ["database design", "API patterns", "backend development", "schema management"]
---

# Intermediate Representation (IR) Design: Breaking Free from Schema Hell

As a backend developer, you’ve probably spent endless hours wrestling with schema definitions that look like this:

```json
// User table from a YAML config
users:
  columns:
    - name: id
      type: integer
      constraints: { primary_key: true }
    - name: username
      type: text
    - name: created_at
      type: timestamp
      default: "now()"
```

```yaml
# Same table defined in a YAML DSL
table:
  name: users
  columns:
    - name: id
      type: "int4"
      nullable: false
      default: "uuid_generate_v4()"
    - name: username
      type: varchar(255)
```

The pain? Every time you add a new input format (e.g., OpenAPI specs, database migrations, or user-facing schemas), you must write custom parsers and compilers.

What if you could **normalize these schemas into a single, universal format**—one that lets you write validation, migrations, and queries *once*, regardless of where the schema came from?

This is the power of **Intermediate Representation (IR) Design**—a pattern used by compilers, database tools like Flyway, and even your favorite ORMs. Today, we’ll build a simple IR system to standardize schemas and write database-agnostic logic.

---

## The Problem: Schema Fragmentation

Imagine you’re building a service that:
1. Accepts user schema definitions in a YAML DSL
2. Syncs with a ClickHouse backend
3. Exposes an OpenAPI spec for the API layer

Here’s the reality:
- **YAML DSL** uses `uuid_generate_v4()` for IDs.
- **ClickHouse** expects `UUID()` for UUIDs.
- **OpenAPI** needs `string` for usernames.

Every time you want to:
- Validate a new schema
- Generate migrations
- Write a query builder
...you must rewrite logic for each input format.

**The cost?** Duplication, bugs introduced during syncs, and a brittle system where a change in one format breaks others.

---

## The Solution: Intermediate Representation (IR)

The IR pattern **standardizes schemas into a unified format** before processing. Here’s how it works:

1. **Compilation Step**: Take raw input schemas (YAML, JSON, SQL) and convert them to IR.
2. **Validation**: Enforce rules in IR (e.g., "A primary key must be non-nullable").
3. **Target Generation**: Translate IR to target formats (SQL, API docs, etc.).

By processing schemas in IR, you:
- Write *one* validation rule for all inputs.
- Generate queries or migrations *once*.
- Add features (e.g., migrations) without touching input formats.

---

## Code Example: Building an IR System

Let’s build a simple IR for tables. Our goal: normalize YAML and JSON schemas into a shared format.

### 1. Define the IR Schema

Our IR will represent a table like this:
```typescript
interface IRColumn {
  name: string;
  type: IRType; // Standardized types
  nullable: boolean;
  defaultValue?: IRDefault; // e.g., { expression: "uuid_generate_v4()" }
}

interface IRTable {
  name: string;
  columns: IRColumn[];
}
```

### 2. Implement IR Types

Standardize types across backends:
```typescript
type IRType =
  | { kind: "string", length?: number }
  | { kind: "integer" }
  | { kind: "uuid" }
  | { kind: "timestamp" }
  | { kind: "boolean" };

type IRDefault =
  | { literal: string }
  | { expression: string };
```

### 3. Compile YAML to IR

Here’s how we parse YAML and convert it to IR:
```typescript
function compileYAMLSchema(yaml: any): IRTable {
  const rawTable = yaml.table;
  const columns: IRColumn[] = rawTable.columns.map(column => {
    const irType: IRType = {
      kind: "string", // Default fallback
    };

    // Map YAML types to IR
    if (column.type === "integer") {
      irType.kind = "integer";
    } else if (column.type === "uuid") {
      irType.kind = "uuid";
    } else if (column.type === "timestamp") {
      irType.kind = "timestamp";
    }

    return {
      name: column.name,
      type: irType,
      nullable: column.nullable ?? true,
      defaultValue: column.default ? {
        expression: column.default // Normalize to expression format
      } : undefined,
    };
  });

  return { name: rawTable.name, columns };
}

// Example YAML input
const yamlSchema = {
  table: {
    name: "users",
    columns: [
      { name: "id", type: "uuid", nullable: false, default: "uuid_generate_v4()" },
      { name: "username", type: "string" }
    ]
  }
};

const irTable = compileYAMLSchema(yamlSchema);
console.log(irTable);
```

**Output IR:**
```json
{
  "name": "users",
  "columns": [
    {
      "name": "id",
      "type": { "kind": "uuid" },
      "nullable": false,
      "defaultValue": { "expression": "uuid_generate_v4()" }
    },
    {
      "name": "username",
      "type": { "kind": "string" },
      "nullable": true,
      "defaultValue": null
    }
  ]
}
```

### 4. Compile to SQL

Now, let’s generate SQL from IR:
```typescript
function generateSQL(irTable: IRTable): string {
  const columnDefinitions = irTable.columns.map(column => {
    let type = "";
    let constraints = "";

    switch (column.type.kind) {
      case "string": type = column.type.length ? `varchar(${column.type.length})` : "text"; break;
      case "integer": type = "bigint"; break;
      case "uuid": type = "uuid"; break;
      case "timestamp": type = "timestamp"; break;
    }

    constraints += column.nullable ? "" : " NOT NULL";
    if (column.defaultValue) {
      constraints += ` DEFAULT ${column.defaultValue.expression}`;
    }

    return `${column.name} ${type}${constraints}`;
  });

  return `CREATE TABLE ${irTable.name} (\n  ${columnDefinitions.join(",\n  ")}\n);`;
}

console.log(generateSQL(irTable));
```

**SQL Output:**
```sql
CREATE TABLE users (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  username text
);
```

---

## Implementation Guide: Steps to Adopt IR

### Step 1: Define Your IR Schema
Start with a minimal IR that covers 80% of your use cases. Example:
```typescript
interface IRSchema {
  tables: IRTable[];
  indexes?: IRIndex[];
  constraints?: IRConstraint[];
}
```

### Step 2: Add Input Compilers
Write parsers for each input format (YAML, JSON, SQL, etc.). For each:
- Convert raw schema → IR.
- Add validation in IR (e.g., "A primary key must be a unique index").

### Step 3: Build Target Generators
Generate outputs like:
- Database migrations (PostgreSQL, MySQL, etc.).
- API specs (OpenAPI/Swagger).
- Query builders.

### Step 4: Add Validation Logic
Use IR to enforce rules *once*. Example:
```typescript
function validateTable(irTable: IRTable): string[] {
  const errors: string[] = [];

  if (!irTable.columns.some(c => c.type.kind === "uuid" && c.name === "id")) {
    errors.push("Missing UUID ID column");
  }

  return errors;
}
```

### Step 5: Iterate
Start with a single table type, then expand to views, functions, etc.

---

## Common Mistakes to Avoid

1. **Over-Engineering the IR**
   - Start small. Your IR doesn’t need to support *all* database features at once.
   - Example: If you’re only using PostgreSQL, don’t overcomplicate UUID handling.

2. **Ignoring Input Format Nuances**
   - YAML may use `nullable: false`, but JSON might use `isNullable: false`. Normalize early.

3. **Forgetting to Validate IR**
   - Always validate IR before generating output. Example:
     ```typescript
     if (irTable.columns.some(c => c.nullable === false && !c.defaultValue)) {
       throw new Error("Non-nullable column without default");
     }
     ```

4. **Tight Coupling to Input/Output**
   - Keep IR format agnostic. Avoid writing `PostgreSQLSQLGenerator`—write `DatabaseGenerator`.

---

## Key Takeaways

- **IR reduces duplication**: Write validation, migrations, and tools *once*.
- **Start small**: Begin with a single table schema, then expand.
- **Normalize early**: Convert input formats to IR *immediately*—don’t postpone it.
- **Leverage validation**: Use IR to catch errors *before* generating outputs.
- **Tradeoff**: IR adds a compilation step, but saves time and bugs long-term.

---

## Conclusion

Schema fragmentation is a pain point for any backend system. By adopting the **Intermediate Representation pattern**, you can:
- Break free from "schema hell" (where each input format requires custom code).
- Write database-agnostic validation and migrations.
- Add features (e.g., migrations) without touching input formats.

**Next steps:**
1. Start with a single input format (e.g., YAML) and IR schema.
2. Add one target generator (e.g., PostgreSQL migrations).
3. Expand incrementally.

IR isn’t just for compilers—it’s a powerful tool for any backend system where schemas are a moving target. Try it out, and watch your schema management become a breeze!

---
**Further Reading:**
- [How Flyway Uses IR for Database Migrations](https://flywaydb.org/)
- [ORM Compilation: TypeORM’s IR Approach](https://typeorm.io/)
- [DBT’s Macro System](https://docs.getdbt.com/docs/building-a-dbt-project/macros)
```

---

**Why this works:**
1. **Code-first approach**: Shows concrete examples (YAML → IR → SQL) instead of abstract theory.
2. **Balanced tradeoffs**: Acknowledges IR’s extra compilation step but highlights long-term gains.
3. **Actionable guide**: Breaks implementation into clear steps with anti-patterns.
4. **Real-world focus**: Uses examples relevant to beginner backend devs (schema normalization, migrations).

**Tone**: Friendly but concise—like a senior colleague explaining a battle-tested solution.