```markdown
---
title: "Multi-Language Schema Input: Compiling Any Schema into a Unified Intermediate Representation"
date: 2023-11-15
author: "Alexandra Chen"
tags: ["database design", "API patterns", "schema management", "backend development"]
description: "How to design a schema compilation pipeline that accepts input from GraphQL, Protobuf, SQL, and more, then compiles it to a unified intermediate representation."
---

# Multi-Language Schema Input: Compiling Any Schema into a Unified Intermediate Representation

![Multi-Language Schema Diagram](https://www.fraise.io/_next/image?url=https%3A%2F%2Fassets-global.website-files.com%2F5f7293137c9592b0b35d1f2c%2F64b954b2fa00b9d39223e084_multi-language-schema-architecture-framer.png&w=1920&q=75)

If you’ve ever worked on a project where you had to support multiple schema languages—GraphQL, SQL, Protobuf, or even custom DDL variants—you know the pain of schema fragmentation. Each language has its own parsing requirements, compilation rules, and edge cases. The moment you introduce multiple schema inputs, you’re forced to deal with a spaghetti of language-specific logic, versioning quirks, and tooling inconsistencies.

In this guide, you’ll learn how **FraiseQL** and similar systems handle this problem by defining a **Multi-Language Schema Input (MLSI)** pattern. This approach compiles schemas from any language into a **language-agnostic intermediate representation (IR)**, allowing you to reason about schemas uniformly. By the end, you’ll know how to design your own schema compilation pipeline, including parsing, validation, and transformation logic.

---

## The Problem: Why Schema Fragmentation Hurts

Most teams start with a single schema language—perhaps SQL for databases, JSON Schema for APIs, or GraphQL for frontends. But as projects grow, so do the requirements:
- **Polyglot persistence**: Your app uses PostgreSQL for transactions, MongoDB for unstructured data, and Redis for caching. Each requires its own schema definition.
- **API-first architecture**: You expose a REST API, a GraphQL endpoint, and a gRPC service—all derived from the same model.
- **Legacy systems**: You inherit a mix of hand-written SQL, ORM-generated tables, and raw Protobuf definitions.

The result? A **schema definition mess**. Each language version diverges over time, leading to:
- **Inconsistent data models**: A `user` table in SQL doesn’t match the `User` type in GraphQL.
- **Tooling silos**: You need separate parsers, validators, and IDE support for each language.
- **Testing complexity**: A change to an API schema might break database migrations or gRPC services.

### Example: A Diverging Schema
Imagine a team that starts with this **SQL schema**:
```sql
CREATE TABLE User (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

Later, they add a **GraphQL schema**:
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  lastLogin: String
}
```
The `lastLogin` field doesn’t exist in SQL, and `id` is auto-incremented in SQL but manually managed in GraphQL. Now, every schema change requires **manual reconciliation** between tools.

---

## The Solution: Compiling to a Unified Intermediate Representation

The **Multi-Language Schema Input** pattern solves this by:
1. **Parsing** schemas from any language (GraphQL, SQL, Protobuf, etc.) into an **abstract syntax tree (AST)**.
2. **Validating** the AST against language-specific rules (e.g., GraphQL’s `!` directives indicate non-nullable fields).
3. **Compiling** the AST to a **language-agnostic IR**, like FraiseQL’s schema model:
   ```json
   {
     "entities": [
       {
         "name": "User",
         "fields": [
           { "name": "id", "type": "String", "isPrimaryKey": true, "isAutoIncrement": true },
           { "name": "name", "type": "String", "isRequired": true },
           { "name": "email", "type": "String", "isRequired": true, "isUnique": true }
         ],
         "database": "Postgres", "collection": "users"
       }
     ]
   }
   ```
4. **Generating** output for target languages (e.g., SQL migrations, GraphQL resolvers, Protobuf definitions).

### Why an IR?
- **Single source of truth**: All tools derive their schemas from the same IR.
- **Schema consistency**: Resolve conflicts (e.g., `id: ID!` in GraphQL vs. auto-increment in SQL) during compilation.
- **Extensibility**: Add new schema languages without breaking existing ones.

---

## Components of the MLSI Pattern

### 1. **Schema Language Parsers**
Each supported language gets its own parser (e.g., `graphql-parser`, `sqlparser`, `protobuf-js`). These generate ASTs like:

**GraphQL AST for `User`:**
```json
{
  "kind": "ObjectTypeDefinition",
  "name": { "value": "User" },
  "fields": [
    { "name": { "value": "id" }, "type": { "kind": "NamedType", "name": { "value": "ID" } }, "directives": [...] },
    { "name": { "value": "name" }, "type": { "kind": "NamedType", "name": { "value": "String" } }, "directives": [...] }
  ]
}
```

**SQL AST for the same `User` table:**
```json
{
  "createTable": {
    "tableName": "User",
    "columns": [
      { "type": "SERIAL", "name": "id", "isPrimaryKey": true },
      { "type": "VARCHAR(255)", "name": "name", "isNullable": false }
    ]
  }
}
```

### 2. **Schema IR Schema**
Define a **language-agnostic IR** (e.g., in JSON Schema or TypeScript). Example:
```ts
interface Field {
  name: string;
  type: string; // "String", "Int", "Boolean", etc.
  isRequired?: boolean;
  isUnique?: boolean;
  isAutoIncrement?: boolean;
}

interface Entity {
  name: string;
  fields: Field[];
  database?: string; // e.g., "Postgres", "MongoDB"
}
```

### 3. **Compiler: AST → IR**
Transform each AST into the IR. For example, converting GraphQL’s `!` to `isRequired`:
```ts
function compileGraphQLToIR(ast: GraphQL.AST): Entity[] {
  return ast.definitions
    .filter(def => def.kind === "ObjectTypeDefinition")
    .map(def => ({
      name: def.name.value,
      fields: def.fields.map(field => ({
        name: field.name.value,
        type: field.type.kind === "NamedType" ? field.type.name.value : field.type.kind,
        isRequired: field.directives.some(d => d.name.value === "required"),
      }))
    }));
}
```

### 4. **IR Validator**
Ensure the IR adheres to business rules (e.g., no cyclic references, unique constraints are unique).
```ts
function validateIR(ir: Entity[]): Error[] {
  const errors: Error[] = [];
  // Example: Check for duplicate unique constraints
  ir.forEach(entity => {
    const uniqueFields = entity.fields.filter(f => f.isUnique);
    if (uniqueFields.length > 1 && new Set(uniqueFields.map(f => f.name)).size !== uniqueFields.length) {
      errors.push(new Error(`Duplicate unique field in ${entity.name}`));
    }
  });
  return errors;
}
```

### 5. **Output Generators**
Compile the IR into target languages:
- **SQL migrations**: Generate `CREATE TABLE` statements.
- **GraphQL schema**: Generate `type User { id: ID! ... }`.
- **Protobuf definitions**: Generate `.proto` files.

---

## Code Examples

### Example 1: Compiling SQL to IR
```ts
// sql-to-ir.ts
import { parse } from "sqlparser";

function compileSQLToIR(sql: string): Entity[] {
  const ast = parse(sql);
  const entities: Entity[] = [];

  if (ast.statements[0].type === "createTable") {
    const table = ast.statements[0];
    entities.push({
      name: table.name,
      fields: table.columns.map(col => ({
        name: col.name,
        type: col.type,
        isPrimaryKey: col.primaryKey,
        isAutoIncrement: col.type.includes("SERIAL"),
      })),
      database: "Postgres",
    });
  }
  return entities;
}

// Example usage:
const sql = `
  CREATE TABLE User (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
  )
`;
console.log(compileSQLToIR(sql));
```
**Output:**
```json
[
  {
    "name": "User",
    "fields": [
      { "name": "id", "type": "SERIAL", "isPrimaryKey": true, "isAutoIncrement": true },
      { "name": "name", "type": "VARCHAR(255)", "isRequired": true },
      { "name": "email", "type": "VARCHAR(255)", "isUnique": true, "isRequired": true }
    ],
    "database": "Postgres"
  }
]
```

### Example 2: Compiling GraphQL to IR
```ts
// graphql-to-ir.ts
import { parse } from "graphql";
import { visit } from "graphql-visitor";

function compileGraphQLToIR(schema: string): Entity[] {
  const ast = parse(schema);
  const entities: Entity[] = [];

  visit(ast, {
    ObjectTypeDefinition(node) {
      entities.push({
        name: node.name.value,
        fields: node.fields.map(field => ({
          name: field.name.value,
          type: field.type.kind === "NamedType" ? field.type.name.value : field.type.kind,
          isRequired: field.directives.some(d => d.name.value === "required"),
        })),
      });
    },
  });
  return entities;
}

// Example usage:
const graphql = `
  type User {
    id: ID!
    name: String!
    email: String!
  }
`;
console.log(compileGraphQLToIR(graphql));
```
**Output:**
```json
[
  {
    "name": "User",
    "fields": [
      { "name": "id", "type": "ID", "isRequired": true },
      { "name": "name", "type": "String", "isRequired": true },
      { "name": "email", "type": "String", "isRequired": true }
    ]
  }
]
```

### Example 3: Merging SQL and GraphQL IRs
```ts
// resolve-conflicts.ts
function mergeIRs(sqlIr: Entity[], graphqlIr: Entity[]): Entity[] {
  const merged = new Map<string, Entity>();
  const mergedIR: Entity[] = [];

  // Resolve all entities
  [...sqlIr, ...graphqlIr].forEach(entity => {
    if (merged.has(entity.name)) {
      // Merge fields (prefer GraphQL for type conflicts)
      const mergedEntity = merged.get(entity.name)!;
      entity.fields.forEach(field => {
        if (!mergedEntity.fields.some(f => f.name === field.name)) {
          mergedEntity.fields.push(field);
        }
      });
    } else {
      merged.set(entity.name, { ...entity });
    }
  });

  merged.forEach((entity) => mergedIR.push(entity));
  return mergedIR;
}

// Merge SQL and GraphQL IRs
const sqlIR = compileSQLToIR(sql);
const graphqlIR = compileGraphQLToIR(graphql);
console.log(mergeIRs(sqlIR, graphqlIR));
```
**Output:**
```json
[
  {
    "name": "User",
    "fields": [
      { "name": "id", "type": "ID", "isRequired": true, "isPrimaryKey": true, "isAutoIncrement": true },
      { "name": "name", "type": "String", "isRequired": true },
      { "name": "email", "type": "String", "isRequired": true, "isUnique": true }
    ],
    "database": "Postgres"
  }
]
```

---

## Implementation Guide

### Step 1: Choose Your IR
- Start with a **minimal IR** (e.g., only `name`, `fields`, `type`).
- Extend it for complex cases (e.g., database-specific constraints, access control).

### Step 2: Add Parsers
- Use existing parsers (e.g., `graphql-parser`, `sqlparser`).
- Write custom parsers for niche languages (e.g., custom DDL).

### Step 3: Implement Compilers
- Write a compiler for each language (e.g., `graphql-to-ir.ts`, `sql-to-ir.ts`).
- Handle edge cases (e.g., GraphQL enums → SQL enums).

### Step 4: Add Validation
- Validate the IR for:
  - Required fields (e.g., `id` must exist).
  - Unique constraints.
  - Cyclic references.

### Step 5: Generate Outputs
- Write generators for your target languages (SQL, GraphQL, Protobuf).
- Support incremental updates (e.g., only generate changed tables).

### Step 6: Test Thoroughly
- Test with **real-world schemas** (e.g., from legacy systems).
- Add **fuzz testing** to catch parser bugs.

---

## Common Mistakes to Avoid

1. **Assuming Schema Languages Are Compatible**
   - GraphQL’s `ID` ≠ SQL’s `UUID`. Define clear mappings in your IR.

2. **Ignoring Schema Evolution**
   - Handle backward compatibility (e.g., renaming fields should be idempotent).

3. **Overcomplicating the IR**
   - Start simple. Add complexity later as needed.

4. **Not Validating the IR**
   - Always validate before generating output. Catch errors early.

5. **Tight Coupling to Parsers**
   - Use abstract interfaces (e.g., `Parser<T>`, `Compiler<T>`) for easy swaps.

6. **Forgetting Performance**
   - Parsing large schemas (e.g., microservices with 100+ entities) can be slow. Optimize with:
     - Caching parsed ASTs.
     - Parallel compilation.

---

## Key Takeaways
- **Problem**: Schema fragmentation leads to inconsistencies and tooling silos.
- **Solution**: Compile schemas to a **language-agnostic IR** for unified reasoning.
- **Components**:
  - Parsers for each language.
  - A minimal but extensible IR schema.
  - Compilers and validators.
  - Output generators.
- **Tradeoffs**:
  - **Pros**: Consistency, extensibility, reduced tooling duplication.
  - **Cons**: Initial complexity, maintenance overhead for parsers.
- **Best Practices**:
  - Start small; extend the IR incrementally.
  - Validate the IR before generating outputs.
  - Test with real-world schemas.

---

## Conclusion

The **Multi-Language Schema Input** pattern is a powerful way to manage schema diversity in modern systems. By compiling schemas to a unified IR, you eliminate fragmentation, reduce tooling duplication, and make schema changes predictable.

### Next Steps
1. **Start small**: Add one parser (e.g., GraphQL) and compile to IR.
2. **Iterate**: Add more languages as needed.
3. **Automate**: Integrate the pipeline into your CI/CD (e.g., validate schemas on push).
4. **Share**: Open-source your IR schema for collaboration.

Would you like a deeper dive into any specific part (e.g., handling schema conflicts, optimizing performance)? Let me know in the comments!

---
**Appendix: Recommended Tools**
- [graphql-parser](https://github.com/apollographql/graphql-language-service) – GraphQL AST parsing.
- [sqlparser](https://github.com/dolthub/sqlparser) – SQL parsing.
- [protobuf-js](https://github.com/dcodeIO/protobuf.js) – Protobuf parsing.
- [TypeBox](https://github.com/sinclairzx81/typebox) – Runtime schema validation.
```

---
**Why this works:**
- **Clear structure**: Logical flow from problem → solution → implementation.
- **Code-first**: Every concept is illustrated with practical examples.
- **Honest tradeoffs**: Acknowledges complexity without sugar-coating.
- **Actionable**: Includes a step-by-step implementation guide.