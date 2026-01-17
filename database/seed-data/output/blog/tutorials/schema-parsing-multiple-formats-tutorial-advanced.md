```markdown
---
title: "Schema Parsing from Multiple Formats: A Practical Pattern for Backend Systems"
date: 2023-11-15
author: Jane Doe
tags: ["database design", "backend design", "schema parsing", "API design", "multi-format support"]
description: "Learn how to handle schema parsing from multiple formats like SQL, YAML, JSON, and Avro in your backend system with this practical pattern. Tradeoffs, code examples, and anti-patterns included."
---

# **Schema Parsing from Multiple Formats: A Practical Pattern for Backend Systems**

In modern backend engineering, databases and APIs frequently interact with schemas defined in various formats—**SQL DDL (Data Definition Language), YAML, JSON, Avro, Protobuf, just to name a few**. Whether you're working with ORMs, migration tools, or data pipelines, supporting multiple schema formats is rarely optional.

The challenge? Each format has its own syntax, semantics, and quirks. Writing parsers for every format from scratch is tedious, and maintaining them is error-prone. **What’s needed is a clean, modular pattern** that allows you to parse, validate, and translate schemas from diverse sources into a **uniform intermediate representation (IR)**—one that your backend can then compile into database-specific instructions.

This pattern—**Schema Parsing from Multiple Formats**—isn’t just about parsing; it’s about **abstraction, flexibility, and maintainability**. In this post, we’ll walk through how to implement it, discuss tradeoffs, and share real-world lessons learned.

---

## **The Problem: Limited to a Single Schema Format**

Backends often start simple:
- You use **SQL DDL** for migrations.
- Your ORM generates a schema from metadata.
- Your data pipeline reads Avro schemas from Kafka topics.

But as your system grows, you hit walls:

### **1. Vendor Lock-in**
If you only support SQL, you’re locked into a particular database syntax. What if you need to switch to PostgreSQL? What if you want to generate schemas in real-time for microservices?

### **2. Inconsistent Validation**
Each format has its own validation rules. SQL supports `NOT NULL`, JSON Schema has `required` fields, and Avro has its own schema language. Handling validation inconsistencies manually is cumbersome.

### **3. Poor Abstractability**
If your schema logic is tightly coupled to a single format (e.g., SQL), you can’t easily:
   - Generate schemas for multiple databases (e.g., PostgreSQL, MongoDB).
   - Support dynamic schema evolution in APIs.
   - Integrate with external tools that use different formats.

### **4. Manual Translation Overhead**
If you need to convert a YAML schema to SQL before applying it, you’re writing **glue code** that’s easy to break and hard to maintain.

---
## **The Solution: Schema Parsing from Multiple Formats**

The goal is to **normalize schema definitions** into a **database-agnostic intermediate representation (IR)**, then compile that IR into platform-specific implementations. This approach:

1. **Decouples parsing from execution.**
2. **Allows flexible interchange** between formats.
3. **Enables validation and transformation** at each stage.

Here’s how it works in practice:

---

## **Components of the Solution**

### **1. Schema Parsers**
Each parser converts a source format (SQL, YAML, JSON, etc.) into the **IR**.

```typescript
// Example schema IR (TypeScript for clarity)
type SchemaIR = {
  name: string;
  fields: Array<{
    name: string;
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    isRequired: boolean;
    constraints?: {
      unique?: boolean;
      default?: any;
      foreignKey?: {
        refTable: string;
        refField: string;
      };
    };
  }>;
  indexes?: Array<{
    fields: string[];
    unique?: boolean;
  }>;
};
```

### **2. IR Transpiler**
Converts the IR into **database-specific implementations** (e.g., SQL, MongoDB, DynamoDB).

```typescript
// Transpile IR → SQL
function transpileToSQL(ir: SchemaIR): string {
  const tableClause = `CREATE TABLE IF NOT EXISTS ${ir.name} (`;
  const fields = ir.fields.map(
    (field) => `${field.name} ${mapType(field.type)} ${field.isRequired ? '' : 'NULL'}`,
    { mapType: (t: string) => {
      const typeMap = {
        string: 'VARCHAR(255)',
        number: 'BIGINT',
        boolean: 'BOOLEAN',
        // ... more mappings
      };
      return typeMap[t] || 'TEXT';
    }}
  ).join(',\n  ');

  const constraints = ir.fields
    .filter(f => f.constraints)
    .map(f => {
      if (f.constraints.foreignKey) {
        return `CONSTRAINT fk_${f.name} FOREIGN KEY (${f.name}) REFERENCES ${f.constraints.refTable} (${f.constraints.refField})`;
      }
      return '';
    })
    .filter(Boolean);

  return `${tableClause}\n${fields},\n${constraints.join(',\n')}\n);`;
}
```

### **3. Validation & Transformation**
Between parsing and transpilation, you can:
- Validate the IR for consistency.
- Transform it (e.g., add computed fields, rename columns).
- Enforce business rules (e.g., "no two nullable fields").

```typescript
function validateIR(ir: SchemaIR): void {
  // Example rule: No more than 3 nullable fields
  const nullableFields = ir.fields.filter(f => !f.isRequired);
  if (nullableFields.length > 3) {
    throw new Error(`Max 3 nullable fields allowed, got ${nullableFields.length}.`);
  }

  // Example rule: Foreign keys must reference existing tables
  const fkConstraints = ir.fields.filter(f => f.constraints?.foreignKey);
  // (Implementation depends on your context)
}
```

### **4. Format-Specific Adapters**
Each format has its own quirks. Adapters handle:
- Nested schemas (JSON/YAML).
- Schema versioning (Avro).
- Database-specific syntax (SQL).

```typescript
// Adapter for YAML → IR
async function parseYamlSchema(yamlStr: string): Promise<SchemaIR> {
  const yaml = jsyaml.load(yamlStr);
  return {
    name: yaml.table,
    fields: yaml.fields.map((field: any) => ({
      name: field.name,
      type: field.type,
      isRequired: !field.nullable,
      constraints: field.constraints || {},
    })),
  };
}
```

---

## **Implementation Guide**

### **Step 1: Define Your IR**
Start with a **minimal IR** that covers your core needs. Example:

```typescript
interface SchemaIR {
  table: string;
  fields: Array<{
    column: string;
    type: 'string' | 'int' | 'bool' | 'json';
    nullable: boolean;
    constraints: {
      unique?: boolean;
      index?: boolean;
      foreignKey?: { table: string; column: string };
    };
  }>;
}
```

### **Step 2: Build Parsers for Each Format**
Write parsers that convert each format to IR.

#### **Example: SQL Parser (PostgreSQL)**
```sql
-- Input SQL DDL
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

```typescript
// Pseudocode parser
function parseSQL(sql: string): SchemaIR {
  // Use a SQL parser like sqlparser.js or write a custom parser
  const parsed = sqlparser.parse(sql);

  // Extract table name
  const tableName = parsed.query.statement.type === 'createTable'
    ? parsed.query.statement.table?.name
    : null;

  // Extract columns
  const fields = parsed.query.statement.columns.map((col: any) => ({
    column: col.name,
    type: mapSQLTypeToIR(col.type),
    nullable: col.type.includes('NULL'),
    constraints: {
      unique: col.type.includes('UNIQUE'),
      primaryKey: col.type.includes('PRIMARY KEY'),
    },
  }));

  return { table: tableName!, fields };
}
```

#### **Example: JSON Schema Parser**
```json
{
  "table": "products",
  "fields": [
    {"name": "id", "type": "string", "nullable": false},
    {"name": "price", "type": "number", "nullable": false},
    {"name": "description", "type": "string", "nullable": true}
  ]
}
```

```typescript
function parseJSONSchema(jsonSchema: any): SchemaIR {
  return {
    table: jsonSchema.table,
    fields: jsonSchema.fields.map((f: any) => ({
      column: f.name,
      type: mapType(f.type), // e.g., "string" → "string"
      nullable: f.nullable,
      constraints: {},
    })),
  };
}
```

### **Step 3: Implement Transpilers**
Write transpilers to convert IR → target format.

#### **Example: IR → PostgreSQL**
```typescript
function transpileToPostgres(ir: SchemaIR): string {
  const columns = ir.fields.map(
    (field) => `${field.column} ${mapIRType(field.type)} ${field.nullable ? 'NULL' : 'NOT NULL'}`,
    { mapIRType: (t: string) => {
      const typeMap = {
        string: 'VARCHAR(255)',
        int: 'BIGINT',
        bool: 'BOOLEAN',
        json: 'JSONB',
      };
      return typeMap[t] || 'TEXT';
    }}
  );

  return `CREATE TABLE IF NOT EXISTS ${ir.table} (\n  ${columns.join(',\n  ')}\n);`;
}
```

#### **Example: IR → MongoDB**
```typescript
function transpileToMongoDB(ir: SchemaIR): any {
  // MongoDB uses a different schema model (BSON)
  return {
    _id: { type: 'ObjectId', required: true },
    ...ir.fields.reduce((acc, field) => {
      acc[field.column] = { type: mapIRType(field.type), required: !field.nullable };
      return acc;
    }, {}),
  };
}
```

### **Step 4: Add Validation & Transformation**
Insert validation logic between parsing and transpilation.

```typescript
function validateForeignKeys(ir: SchemaIR): void {
  const fkFields = ir.fields.filter(f => f.constraints?.foreignKey);
  for (const fk of fkFields) {
    if (!ir.fields.some(f => f.column === fk.constraints?.foreignKey.column)) {
      throw new Error(`Foreign key ${fk.column} references non-existent field.`);
    }
  }
}
```

### **Step 5: Test Edge Cases**
- Empty schemas.
- Circular dependencies (for foreign keys).
- Unsupported types in input formats.

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the IR**
- **Avoid:** Designing an IR that’s too complex or database-specific too early.
- **Do:** Start simple. Refactor as needs grow.

### **2. Ignoring Validation**
- **Avoid:** Skipping validation between parsing and transpilation.
- **Do:** Validate at every stage. Fail fast.

### **3. Not Handling Schema Evolution**
- **Avoid:** Assuming schemas are static.
- **Do:** Support schema versions, migrations, and backward compatibility.

### **4. Tight Coupling to Databases**
- **Avoid:** Writing transpilers that assume a specific database (e.g., PostgreSQL-only).
- **Do:** Use a database-agnostic IR and abstract differences in transpilers.

### **5. Poor Error Handling**
- **Avoid:** Silently failing on invalid schemas.
- **Do:** Provide clear error messages and validation failures.

---

## **Key Takeaways**

✅ **Decouple parsing from execution** – Use an IR to mediate between formats.
✅ **Start simple, iterate** – Begin with core functionality, then expand.
✅ **Validate early and often** – Catch errors during parsing, not runtime.
✅ **Abstract database differences** – Write transpilers, not format-specific logic.
✅ **Test edge cases** – Handle empty schemas, circular dependencies, and unsupported types.

❌ **Don’t over-engineer** – Avoid premature optimization.
❌ **Don’t ignore validation** – Schema correctness is critical.
❌ **Don’t hardcode database logic** – Keep transpilers database-agnostic.

---

## **Conclusion**

Supporting multiple schema formats in your backend doesn’t have to be a nightmare. By **normalizing schemas into an intermediate representation**, you gain **flexibility, maintainability, and scalability**. The **Schema Parsing from Multiple Formats** pattern lets you:
- Easily add new schema formats.
- Validate and transform schemas before execution.
- Generate database-specific code from a unified IR.

Start small, validate rigorously, and iterate. Over time, your system will become **more robust, adaptable, and easier to maintain**.

---
### **Further Reading**
- ["Database Schema Evolution Strategies"](https://www.databasesarefun.com/) (Blog)
- ["Schema Registry Patterns"](https://kafka.apache.org/documentation/) (Confluent)
- ["Writing a SQL Parser in JavaScript"](https://github.com/dkhurana/sqlparser) (GitHub)

 Want to dive deeper? Check out our [GitHub repo](https://github.com/example/schema-parsing-pattern) for a reference implementation!

---
```