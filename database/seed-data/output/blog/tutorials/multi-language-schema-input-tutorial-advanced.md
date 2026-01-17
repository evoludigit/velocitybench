```markdown
---
title: "Multi-Language Schema Input: How FraiseQL Compiles Schemas from Any Source"
date: 2024-05-20
tags:
  - database-design
  - API-patterns
  - schema-management
  - backend-engineering
---

# Multi-Language Schema Input: Compiling Schemas from Any Source

In today’s distributed systems, schema management is no longer a monolithic task confined to a single team or language. Teams use PostgreSQL, SQLServer, Snowflake, Prisma, TypeORM, or even custom in-house DSLs to define their data models. Yet, every time you introduce a new schema source—whether it's a GraphQL schema, an Entity Framework migration, or a raw SQL dump—the team grapples with the same question: *How do we unify these disparate sources into a coherent compilation pipeline?*

The **Multi-Language Schema Input (MLSI)** pattern addresses this by normalizing schemas from diverse languages into a **language-agnostic intermediate representation (IR)** before compilation. This approach decouples schema definition from implementation, allowing teams to flexibly integrate multiple schema sources while ensuring consistency. In this post, we’ll explore how FraiseQL implements this pattern, its tradeoffs, and how you can apply it in your own systems.

---

## The Problem: The Schema Monolith

Before diving into solutions, let’s acknowledge the core issue: **schema languages are rigid and siloed**. When a team uses Prisma for one microservice and SQLAlchemy for another, they face these challenges:

1. **Tooling Fragmentation**: Each schema language comes with its own CLI, migration system, and validation rules. Merging them requires custom glue code or ad-hoc scripts.
2. **Inconsistent Semantics**: A `VARCHAR(255)` in PostgreSQL isn’t the same as a `String` in TypeORM. Even "similar" types (e.g., `INT` vs. `BigInt`) can cause subtle bugs when translated.
3. **Circular Dependencies**: If Service A defines a schema in Prisma but Service B expects SQL tables, you’re forced to write a bidirectional translator—adding complexity and potential drift.
4. **No Shared Library**: Without a common intermediate layer, changes to one schema language require rippling updates across dependent services.

### Example: SQL vs. TypeORM Divergence
Imagine a `User` table defined in two ways:
```sql
-- SQL schema (PostgreSQL)
CREATE TABLE User (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
```typescript
// TypeORM schema (JavaScript)
@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @CreateDateColumn()
  created_at: Date;
}
```
At first glance, they seem identical—but when compiled to a database, subtle differences emerge:
- `SERIAL` vs. `@PrimaryGeneratedColumn()`: The latter might use `AUTO_INCREMENT` in SQLServer, not `SERIAL`.
- `TIMESTAMP WITH TIME ZONE` is PostgreSQL-specific; TypeORM might default to `TIMESTAMP` elsewhere.
- The `UNIQUE` constraint is explicit in SQL but implicit in TypeORM (unless you consider `@Column({ unique: true })`).

Without a common ground, these differences accumulate as tech debt.

---

## The Solution: Multi-Language Schema Input

The MLSI pattern solves this by introducing an **intermediate representation (IR)**—a schema definition that is:
- **Language-agnostic**: Describes tables, columns, relationships, and constraints in terms of primitives (e.g., `Column`, `Table`, `ForeignKey`).
- **Compilable to any target**: The IR can be emitted to SQL, Prisma, TypeORM, or even a protobuf-based API schema.
- **Validatable**: A schema compiler validates the IR for consistency before generating targets.

### How FraiseQL Implements MLSI
FraiseQL’s compilation pipeline works like this:
1. **Input Parsers**: Each schema source (SQL, Prisma, TypeORM, etc.) is parsed into a domain-specific model.
2. **Normalization**: The DSM is translated to the **FraiseQL IR**, resolving ambiguities (e.g., mapping `INT` to a `Number` type with constraints).
3. **Validation**: The IR is checked for:
   - Type conflicts (e.g., a `String` column in one source vs. a `VARCHAR(10)` in another).
   - Missing constraints (e.g., `NOT NULL` implied but not explicitly stated).
4. **Compilation**: The IR is emitted to one or more target languages/formats.

### Key Components of MLSI
| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **Input Parsers**       | Converts schema sources (SQL, Prisma, etc.) into a domain-specific model.|
| **Normalizer**          | Translates DSMs to the IR, handling type mappings and constraint resolution. |
| **Validator**           | Ensures the IR adheres to business rules (e.g., no cyclic dependencies). |
| **Emitters**            | Generates target schemas (SQL, Prisma, etc.) from the IR.              |

---

## Code Examples: Putting MLSI into Practice

Let’s walk through a concrete example: compiling a schema from **SQL** and **Prisma** into a unified IR, then emitting it to **PostgreSQL** and **Prisma**.

### 1. Input Schemas
#### SQL Schema (PostgreSQL)
```sql
-- schema.sql
CREATE TABLE User (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE Post (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  author_id INTEGER REFERENCES User(id)
);
```

#### Prisma Schema
```prisma
// schema.prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique @notNull
  posts Post[]
  createdAt DateTime @default(now())
}

model Post {
  id     Int     @id @default(autoincrement())
  title  String  @notNull
  author User    @relation(fields: [authorId], references: [id])
  authorId Int
}
```

---

### 2. Parsing to Domain-Specific Models (DSM)
First, we parse each schema into a DSM. Here’s a simplified example using TypeScript:

```typescript
// src/parsers/sql.ts
interface SQLColumn {
  name: string;
  type: string; // e.g., "VARCHAR(255)"
  constraints: {
    notNull?: boolean;
    unique?: boolean;
    default?: string;
  };
}

interface SQLTable {
  name: string;
  columns: SQLColumn[];
  foreignKeys?: SQLForeignKey[];
}

interface SQLForeignKey {
  column: string;
  refTable: string;
  refColumn: string;
}

// Parse the SQL schema
const sqlSchema: SQLTable[] = parseSQL(`
  CREATE TABLE User (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  CREATE TABLE Post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INTEGER REFERENCES User(id)
  );
`);
```

```typescript
// src/parsers/prisma.ts
interface PrismaModel {
  name: string;
  fields: PrismaField[];
  relations?: PrismaRelation[];
}

interface PrismaField {
  name: string;
  type: string; // e.g., "Int", "String"
  attributes: {
    id?: true;
    default?: string;
    unique?: boolean;
    notNull?: boolean;
  };
}

interface PrismaRelation {
  field: string;
  relName: string;
  refField: string;
  refModel: string;
}

// Parse the Prisma schema
const prismaSchema: PrismaModel[] = parsePrisma(`
  model User {
    id    Int     @id @default(autoincrement())
    email String  @unique @notNull
    posts Post[]
    createdAt DateTime @default(now())
  }

  model Post {
    id     Int     @id @default(autoincrement())
    title  String  @notNull
    author User    @relation(fields: [authorId], references: [id])
    authorId Int
  }
`);
```

---

### 3. Normalizing to the IR
The IR is a simplified, language-agnostic representation. Here’s how we map the DSMs to it:

```typescript
// src/ir.ts
interface Column {
  name: string;
  type: {
    primitive: "String" | "Number" | "Boolean" | "DateTime";
    precision?: number; // e.g., VARCHAR(255) → precision = 255
  };
  constraints: {
    notNull?: boolean;
    unique?: boolean;
    autoIncrement?: boolean;
    default?: string;
  };
}

interface Table {
  name: string;
  columns: Column[];
  primaryKey?: string[];
  foreignKeys?: ForeignKey[];
}

interface ForeignKey {
  column: string;
  refTable: string;
  refColumn: string;
}

// Normalize SQL to IR
function normalizeSQLToIR(sqlSchema: SQLTable[]): Table[] {
  return sqlSchema.map(table => ({
    name: table.name,
    columns: table.columns.map(col => ({
      name: col.name,
      type: mapSQLTypeToIR(col.type),
      constraints: {
        notNull: col.constraints.notNull,
        unique: col.constraints.unique,
        autoIncrement: col.name === "id" && col.type.startsWith("SERIAL"),
        default: col.constraints.default,
      },
    })),
    primaryKey: ["id"],
    foreignKeys: table.foreignKeys?.map(fk => ({
      column: fk.column,
      refTable: fk.refTable,
      refColumn: fk.refColumn,
    })),
  }));
}

// Helpful type mappings
function mapSQLTypeToIR(sqlType: string): Column["type"] {
  if (sqlType.startsWith("VARCHAR")) {
    const precision = parseInt(sqlType.match(/\((\d+)\)/)![1]);
    return { primitive: "String", precision };
  }
  if (sqlType.startsWith("SERIAL") || sqlType === "INTEGER") {
    return { primitive: "Number" };
  }
  if (sqlType.startsWith("TIMESTAMP")) {
    return { primitive: "DateTime" };
  }
  throw new Error(`Unsupported SQL type: ${sqlType}`);
}

// Normalize Prisma to IR
function normalizePrismaToIR(prismaSchema: PrismaModel[]): Table[] {
  return prismaSchema.map(model => ({
    name: model.name,
    columns: model.fields.map(field => ({
      name: field.name,
      type: {
        primitive: mapPrismaTypeToIR(field.type),
        precision: field.type.includes("String") ? 255 : undefined,
      },
      constraints: {
        notNull: field.attributes.notNull,
        unique: field.attributes.unique,
        autoIncrement: field.attributes.id && field.type === "Int",
        default: field.attributes.default,
      },
    })),
    primaryKey: model.fields.find(f => f.attributes.id)?.name ? ["id"] : undefined,
    foreignKeys: model.relations?.map(rel => ({
      column: rel.field,
      refTable: rel.refModel,
      refColumn: rel.refField,
    })),
  }));
}

// Helper for Prisma types
function mapPrismaTypeToIR(prismaType: string): Column["type"]["primitive"] {
  switch (prismaType) {
    case "Int": return "Number";
    case "String": return "String";
    case "DateTime": return "DateTime";
    default: throw new Error(`Unsupported Prisma type: ${prismaType}`);
  }
}
```

---

### 4. Resolving Conflicts in the IR
When merging schemas from SQL and Prisma, conflicts often arise. For example:
- **Type Precision**: Prisma’s `String` defaults to 255, but SQL might specify `VARCHAR(10)`.
- **Primary Key**: Prisma uses `@id`, while SQL might use `SERIAL`.
- **Foreign Keys**: SQL might use `author_id`, but Prisma uses `authorId`.

The normalizer resolves these by:
1. **Defaulting to the most permissive type**: If SQL defines `VARCHAR(10)` and Prisma defines `String`, use `String` (assuming the app won’t store 1000-character emails).
2. **Standardizing names**: Convert `authorId` to `author_id` for SQL compatibility.
3. **Validating constraints**: Ensure `NOT NULL` is consistent across sources.

Example conflict resolution:
```typescript
// Resolve type conflicts
function resolveColumnType(
  sqlType: Column["type"],
  prismaType: Column["type"]
): Column["type"] {
  if (sqlType.primitive === prismaType.primitive) {
    // Prefer SQL's precision if specified
    return sqlType.precision ? { ...sqlType, precision: sqlType.precision } : prismaType;
  }
  // Fallback: use Prisma's default
  return prismaType;
}
```

---

### 5. Validating the IR
Before emitting, validate the IR for:
- **Consistency**: All primary keys must be unique across tables.
- **Cyclic Dependencies**: Tables shouldn’t reference each other in a loop.
- **Missing Constraints**: `NOT NULL` columns should not have `DEFAULT` values unless explicitly allowed.

```typescript
// src/validator.ts
function validateIR(tables: Table[]): void {
  const tableNames = tables.map(t => t.name);

  // Check for cyclic dependencies
  for (const table of tables) {
    if (table.foreignKeys) {
      for (const fk of table.foreignKeys) {
        if (!tableNames.includes(fk.refTable)) {
          throw new Error(`Foreign key refs non-existent table: ${fk.refTable}`);
        }
      }
    }
  }

  // Check for uniqueness of primary keys
  const primaryKeys = new Set<string>();
  for (const table of tables) {
    if (table.primaryKey) {
      for (const pk of table.primaryKey) {
        const key = `${table.name}.${pk}`;
        if (primaryKeys.has(key)) {
          throw new Error(`Duplicate primary key: ${key}`);
        }
        primaryKeys.add(key);
      }
    }
  }
}
```

---

### 6. Emitting to Targets
Finally, emit the IR to your desired targets. Here’s how to generate **PostgreSQL SQL** and **Prisma**:

#### PostgreSQL SQL Emitter
```typescript
function emitPostgreSQL(tables: Table[]): string {
  return tables.map(table => {
    const columnDefs = table.columns.map(col => {
      let type = col.type.primitive;
      if (col.type.precision) {
        type += `(${col.type.precision})`;
      }
      const constraints = [];
      if (col.constraints.notNull) constraints.push("NOT NULL");
      if (col.constraints.unique) constraints.push("UNIQUE");
      if (col.constraints.autoIncrement) constraints.push("SERIAL");
      if (col.constraints.default) constraints.push(`DEFAULT ${col.constraints.default}`);
      return `${col.name} ${type} ${constraints.join(" ")}`;
    }).join(",\n  ");

    const primaryKey = table.primaryKey
      ? `PRIMARY KEY (${table.primaryKey.join(", ")})`
      : "";

    const foreignKeys = table.foreignKeys
      ? table.foreignKeys.map(fk =>
          `FOREIGN KEY (${fk.column}) REFERENCES ${fk.refTable}(${fk.refColumn})`
        ).join(",\n  ")
      : "";

    return `
CREATE TABLE ${table.name} (
  ${columnDefs}
  ${primaryKey}
  ${foreignKeys}
);
`;
  }).join("\n\n");
}

// Usage
const ir = normalizeAndMergeSQLAndPrisma(sqlSchema, prismaSchema);
validateIR(ir);
const postgresSQL = emitPostgreSQL(ir);
console.log(postgresSQL);
```

#### Prisma Emitter
```typescript
function emitPrisma(tables: Table[]): string {
  return `// @prisma-client\nmodel ${tables.map(t => t.name).join("\n")}\n{\n` +
    tables.map(table => {
      const fields = table.columns.map(col => {
        let type = col.type.primitive;
        if (col.type.precision === 255) type = "String"; // Prisma's default
        const attributes = [];
        if (col.constraints.notNull) attributes.push("@notNull");
        if (col.constraints.unique) attributes.push("@unique");
        if (col.constraints.autoIncrement) attributes.push("@default(autoincrement())");
        if (col.constraints.default) attributes.push(`@default(${col.constraints.default})`);
        return `  ${col.name} ${type} ${attributes.join(" ")}`;
      }).join(",\n");

      const relations = table.foreignKeys?.map(fk => {
        return `
  ${fk.column} ${fk.refColumn} @relation(fields: [${fk.column}], references: [${fk.refColumn}])
  ${fk.refTable}[]`;
      }).join("\n");

      return `${table.name} {\n${fields}\n${relations}\n}`;
    }).join("\n") + "\n}";
}
```

---

## Implementation Guide: Adopting MLSI

### Step 1: Define Your IR
Start with a minimal IR that captures:
- Tables, columns, and types.
- Constraints (`NOT NULL`, `UNIQUE`, `FOREIGN KEY`).
- Relationships (e.g., `@relation`).

Example IR:
```typescript
interface IR {
  tables: Table[];
  // Add metadata, rollback info, etc.
}
```

### Step 2: Build Parsers for Your Schema Sources
Write parsers for each source language (SQL, Prisma, TypeORM, etc.). Use existing tools where possible:
- **SQL**: Leverage `pg-format` or `pg-query-parser` for PostgreSQL.
- **Prisma**: Use `prisma-schema-parser` or write a custom parser for `.prisma` files.
- **TypeORM**: Reverse-engineer the ORM’s metadata (e.g., via `@Entity` decorators).

### Step 3: Normalize to IR
Implement type mappings (e.g., `VARCHAR(255)` → `String(255)`) and constraint resolution. Handle edge cases:
- **Ambiguous Types**: Default to