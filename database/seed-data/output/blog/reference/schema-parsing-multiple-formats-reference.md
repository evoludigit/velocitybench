# **[Pattern] Reference Guide: Schema Parsing from Multiple Formats**

---

## **1. Overview**
This pattern standardizes the translation of multiple schema formats (e.g., JSON Schema, Avro, Protobuf, GraphQL) into an **intermediate representation (IR)** for database-agnostic compilation. By centralizing parsing logic, the system accommodates diverse schema definitions while ensuring consistency in query planning, validation, and optimization.

The **compilation pipeline** uses a modular design with a parser registry, allowing new formats to be added without modifying core logic. Each parser validates input syntax, maps structured fields to the IR, and resolves cross-references (e.g., nested types, dependencies). The generated IR serves as a unified interface for downstream components, including query engines, schema validators, and runtime adapters.

---
---

## **2. Schema Reference**
The following table defines the intermediate representation (IR) schema and supported input formats.

| **IR Field**               | **Description**                                                                                     | **Data Type**       | **Input Format Support**                     |
|----------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-----------------------------------------------|
| `schema_id`                | Unique identifier for the schema (e.g., UUID).                                                     | `string`            | All                                           |
| `name`                     | Human-readable schema name.                                                                      | `string`            | All                                           |
| `version`                  | Schema version (semantic or compatibility tag).                                                   | `string`            | All                                           |
| `fields`                   | List of schema fields with type, constraints, and references.                                     | `[SchemaField]`     | All                                           |
| `dependencies`             | List of referenced schemas (if external).                                                         | `[string]`          | Avro, Protobuf, GraphQL                      |
| `metadata`                 | Custom key-value tags (e.g., `author`, `last_updated`).                                          | `object`            | JSON Schema, Avro                              |
| `generated_at`             | Timestamp of IR generation.                                                                         | `datetime`          | All (automated)                               |

### **SchemaField Structure**
Each field in `schema.fields` follows this schema:

| **Field**       | **Description**                                                                                     | **Data Type**       | **Example Values**                          |
|-----------------|-----------------------------------------------------------------------------------------------------|---------------------|---------------------------------------------|
| `name`          | Field identifier (lowercase, snake_case).                                                         | `string`            | `user_id`, `email`                          |
| `type`          | Primitive or complex type (e.g., `INT`, `STRING`, `ARRAY<FLOAT>`, `ENUM{RED, BLUE}`).               | `string`            | `INT32`, `VARCHAR(255)`, `USER_DEFINED`       |
| `required`      | Boolean flag for mandatory fields.                                                                  | `boolean`           | `true`, `false`                              |
| `default_value` | Fallback value if field is nullable.                                                               | `any`               | `null`, `"default@example.com"`              |
| `constraints`   | Validation rules (e.g., `min_length`, `unique`, `regex`).                                           | `object`            | `{ "min_length": 3, "regex": "/^[A-Za-z]+$/" }`|
| `nested_schema`| Reference to a sub-schema (if field is a complex type).                                           | `string` (schema_id)| `"users_profile"`                             |
| `external_ref`  | Cross-document reference (e.g., foreign keys).                                                    | `string`            | `#orders:order_id`                          |

---
---

## **3. Query Examples**
This section demonstrates how to parse and translate schemas using common input formats.

### **3.1 JSON Schema Example**
**Input (`schema.json`):**
```json
{
  "id": "users",
  "title": "User Schema",
  "type": "object",
  "properties": {
    "id": { "type": "integer", "required": true },
    "name": {
      "type": "string",
      "minLength": 2,
      "pattern": "^[A-Za-z]+$"
    },
    "emails": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "email"
      }
    }
  },
  "dependencies": ["auth"]
}
```

**IR Output:**
```json
{
  "schema_id": "uuid123",
  "name": "users",
  "version": "1.0",
  "fields": [
    {
      "name": "id",
      "type": "INT32",
      "required": true,
      "default_value": null,
      "constraints": {}
    },
    {
      "name": "name",
      "type": "VARCHAR(255)",
      "required": true,
      "constraints": {
        "min_length": 2,
        "regex": "^[A-Za-z]+$"
      }
    },
    {
      "name": "emails",
      "type": "ARRAY<STRING>",
      "required": false,
      "constraints": {
        "items_type": "STRING",
        "format": "email"
      }
    }
  ],
  "dependencies": ["auth"]
}
```

---
### **3.2 Avro Schema Example**
**Input (`users.avsc`):**
```json
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "userId", "type": ["null", "long"], "default": null},
    {"name": "preferences", "type": {"type": "map", "values": "string"}),
    {"name": "accounts", "type": {"type": "array", "items": "UserAccount"}}
  ]
}
```

**IR Output:**
```json
{
  "schema_id": "avro_user",
  "name": "users",
  "fields": [
    {
      "name": "user_id",
      "type": "INT64",
      "required": false,
      "default_value": null
    },
    {
      "name": "preferences",
      "type": "MAP<STRING>",
      "required": false
    },
    {
      "name": "accounts",
      "type": "ARRAY<USER_DEFINED>",
      "required": false,
      "nested_schema": "user_accounts"
    }
  ]
}
```

---
### **3.3 Protobuf Schema Example**
**Input (`users.proto`):**
```protobuf
syntax = "proto3";
message User {
  string id = 1 [(json_name) = "userId"];
  repeated string roles = 2 [(json_name) = "userRoles"];
  UserProfile profile = 3;
}
message UserProfile {
  string fullName = 1;
}
```

**IR Output:**
```json
{
  "schema_id": "protobuf_user",
  "name": "users",
  "fields": [
    {
      "name": "user_id",
      "type": "STRING",
      "required": true,
      "constraints": {"json_name": "userId"}
    },
    {
      "name": "user_roles",
      "type": "ARRAY<STRING>",
      "required": false,
      "constraints": {"json_name": "userRoles"}
    },
    {
      "name": "profile",
      "type": "USER_DEFINED",
      "required": false,
      "nested_schema": "user_profile"
    }
  ]
}
```

---
---

## **4. Implementation Details**
### **4.1 Parser Registry**
The system maintains a registry of parsers, each implementing the `SchemaParser` interface:

```typescript
interface SchemaParser {
  parse(input: string | Buffer): Promise<IRSchema>;
  supports(format: string): boolean;
  validate(input: string | Buffer): boolean;
}
```

**Example Registry (TypeScript):**
```typescript
const parsers: Record<string, SchemaParser> = {
  "JSON_SCHEMA": new JsonSchemaParser(),
  "AVRO": new AvroSchemaParser(),
  "PROTOBUF": new ProtobufSchemaParser(),
  "GRAPHQL": new GraphQLSchemaParser()
};
```

---
### **4.2 Core Parsing Logic**
1. **Input Validation**: Check syntax (e.g., JSON Schema draft version).
2. **Field Mapping**: Translate format-specific types to IR (e.g., `proto3.string` → `STRING`).
3. **Dependency Resolution**: Recursively parse nested schemas (e.g., `UserAccount` in Avro).
4. **Error Handling**: Log warnings (e.g., deprecated fields) and fail fast on critical errors.

```typescript
async function parseSchema(input: Buffer, format: string): Promise<IRSchema> {
  const parser = parsers[format];
  if (!parser.supports(format)) throw new Error("Unsupported format");

  const rawSchema = await parser.parse(input);
  const validated = parser.validate(input); // Pre-flight check

  return {
    ...rawSchema,
    schema_id: generateUUID(),
    generated_at: new Date().toISOString()
  };
}
```

---
### **4.3 Handling Complex Types**
| **Format-Specific Type** | **IR Equivalent**               | **Notes**                                  |
|--------------------------|----------------------------------|--------------------------------------------|
| JSON Schema `array`      | `ARRAY<TYPE>`                    | Resolve `items` to nested schema.          |
| Avro `map<STRING>`       | `MAP<STRING>`                    | Emitted verbatim (key-value pairs).        |
| Protobuf `repeated`      | `ARRAY<TYPE>`                    | Maps to IR array with type inference.      |
| GraphQL `ObjectType`     | `USER_DEFINED`                   | References a separate schema.              |

---
### **4.4 Performance Considerations**
- **Caching**: Store parsed IRs to avoid reprocessing identical schemas.
- **Parallelization**: Use workers for large schemas (e.g., GraphQL with 100+ types).
- **Lazy Parsing**: Delay resolving dependencies until needed (e.g., during query execution).

---
---

## **5. Query Examples (Advanced)**
### **5.1 Cross-Format Schema Queries**
**Scenario**: Query a combined schema where `users` references `auth.roles`.

```sql
-- IR-based query (pseudo-SQL)
SELECT users.name, auth.roles.admin
FROM users
JOIN auth USING (user_id)
WHERE users.name LIKE '%admin%'
```

**IR Representation**:
```json
{
  "query": {
    "from": ["users", "auth"],
    "join": { "users.user_id": "auth.user_id" },
    "filter": { "name": { "like": "%admin%" } },
    "select": ["users.name", "auth.roles.admin"]
  }
}
```

---
### **5.2 Schema Evolution**
**Input (JSON Schema v6 → v7)**:
```json
// Old (v6)
"properties": { "age": { "type": "integer", "minimum": 0 } }

// New (v7)
"properties": {
  "age": {
    "type": "integer",
    "minimum": 0,
    "description": "User age in years"
  }
}
```

**IR Handling**:
- Preserve backward compatibility.
- Add `metadata.description` for v7-only fields.

---
---

## **6. Related Patterns**
| **Pattern**                     | **Relationship**                                                                                     | **When to Use**                                      |
|----------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **Schema Registry**              | Stores parsed IRs for reuse across services.                                                         | Persistent schema versioning.                        |
| **Query Compilation**            | Uses IR to generate optimized query plans (e.g., for SQL, Cypher).                                  | Database-agnostic execution.                           |
| **Adaptive Schema Validation**   | Validates queries against IR at runtime (e.g., GraphQL schemas).                                   | Dynamic APIs with evolving schemas.                   |
| **Polyglot Persistence**         | Maps IR to multiple database schemas (e.g., PostgreSQL, MongoDB).                                    | Multi-database deployments.                           |
| **Schema Evolution Strategies**  | Handles breaking changes (e.g., field renames) via IR transformations.                              | Legacy system migrations.                             |

---
---
## **7. Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                      |
|------------------------------------|--------------------------------------------|---------------------------------------------------|
| Missing nested schema reference    | `nested_schema` field not resolved.        | Preload all dependencies via `parseDependencies()`. |
| Type mismatch in Avro/Protobuf     | Primitive types misaligned (e.g., `int32` vs `int64`). | Use IR `INT32`/`INT64` consistently.              |
| GraphQL union/interfaces unresolved| Complex types not fully parsed.           | Enable recursive resolution in `GraphQLSchemaParser`. |
| Performance bottleneck             | Large schemas cause memory spikes.         | Stream parsing or chunk processing.               |

---
---
## **8. References**
- [JSON Schema Spec (Draft 7)](https://json-schema.org/specification.html)
- [Avro Schema Format](https://avro.apache.org/docs/current/spec.html)
- [Protocol Buffers Schema](https://developers.google.com/protocol-buffers/docs/reference/java-generated)
- [GraphQL Schema Language](https://spec.graphql.org/October2021/)

---
---
**Last Updated**: `[Insert Date]`
**Version**: `1.2`