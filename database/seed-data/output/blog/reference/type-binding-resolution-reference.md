# **[Pattern] Type Binding Resolution – Reference Guide**

The **Type Binding Resolution** pattern defines a mechanism for dynamically connecting data structures (e.g., JSON, XML, Protocol Buffers) to strongly-typed programming constructs. This pattern enables runtime validation, serialization, and transformation of loosely coupled data into concrete object models, ensuring type safety without requiring manual mapping code.

Type Binding Resolution is commonly used in:
- **API Gateway/Service Mesh** configurations (e.g., OpenAPI/OpenAPI to gRPC)
- **Configuration Profiles** (e.g., Kubernetes Custom Resources to Go structs)
- **Data Processing Pipelines** (e.g., Kafka messages to domain models)
- **Schema Evolution** (e.g., migrating between JSON and Avro)

---

## **1. Overview**
Type Binding Resolution bridges the gap between **runtime data** (e.g., JSON payloads) and **compiled type systems** (e.g., Python classes, Java interfaces). The pattern avoids repetitive "glue code" by:
- **Decoupling** the data model from implementation.
- **Automating** type validation and conversion.
- **Supporting** runtime extensibility (e.g., adding new fields without recompilation).

The pattern typically involves:
1. **Schema Definition** – A metadata description of allowed fields and types.
2. **Binding Etiquette** – Rules to convert runtime data into typed objects.
3. **Resolution Engine** – A service that matches schemas to code types, validating and transforming data.

---

## **2. Schema Reference**
The following table outlines key components of a Type Binding Resolution schema. This example uses a hybrid JSON/YAML format, but adaptations exist for XML, Protobuf, and others.

| **Field**               | **Type**          | **Description**                                                                 | **Constraints**                          | **Example**                          |
|-------------------------|-------------------|-------------------------------------------------------------------------------|------------------------------------------|--------------------------------------|
| `@schema`               | `string`          | Unique identifier for the binding schema.                                     | Required                                | `"v1/user-profile"`                  |
| `@target`               | `object`          | The Go/Python/Java/TS class or type name where data binds.                     | Required                                | `"com.example.UserProfile"`           |
| `properties`            | `map<string, Prop>`| Dictionary of data fields and validation rules.                                | Required                                | `{ "name": { "type": "string" }, ... }` |
| `required`              | `list<string>`    | Fields that must be present.                                                 | Optional                                | `["name", "email"]`                  |
| `@bindings`             | `map<string, Bind>`| Custom transformation rules (e.g., date parsing).                            | Optional                                | `{ "createdAt": { "parser": "iso8601" } }` |
| `@extends`              | `string`          | Inherited schema (e.g., base class).                                          | Optional                                | `"v1/user-base"`                     |
| `@version`              | `string`          | Schema version for backward compatibility.                                     | Optional                                | `"1.2"`                              |

### **Property Schema (`Prop`)**
| **Field**       | **Type**          | **Description**                                                                 |
|-----------------|-------------------|-------------------------------------------------------------------------------|
| `type`          | `string`          | Primitive type (`"string"`, `"number"`, `"boolean"`, `"array"`, `"object"`)  |
| `format`        | `string`          | Special type hints (`"date-time"`, `"uuid"`, `"email"`)                      |
| `default`       | any               | Fallback value if field is missing.                                           |
| `enum`          | `list<string>`    | Allowed values (e.g., `["active", "inactive"]`).                             |
| `nillable`      | `boolean`         | Allows `null` values.                                                          |

### **Binding Rule (`Bind`)**
| **Field**       | **Type**          | **Description**                                                                 |
|-----------------|-------------------|-------------------------------------------------------------------------------|
| `parser`        | `string`          | Custom parser function (e.g., `"iso8601"`).                                   |
| `mapper`        | `string`          | External function to transform data (e.g., `"toUpperCase"`).                   |
| `dependencies`  | `list<string>`    | Required fields for validation.                                                |

---
## **3. Query Examples**
The following examples demonstrate how Type Binding Resolution resolves data into typed objects.

### **Example 1: Basic JSON-to-Go Binding**
**Schema (`schema.json`):**
```json
{
  "@schema": "v1/user",
  "@target": "github.com/user/pkg.User",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "email": { "type": "string", "format": "email" },
    "status": { "type": "string", "enum": ["active", "banned"] }
  },
  "required": ["email"]
}
```

**Input JSON:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "status": "active"
}
```

**Go Code (Bound Object):**
```go
type User struct {
    ID     string `json:"id" binding:"required,uuid"`
    Email  string `json:"email" binding:"required,email"`
    Status string `json:"status" binding:"oneof=active banned"`
}
```

**Resolution:**
```go
data, err := binding.ResolveJSON(inputJSON, "v1/user")
if err != nil { /* handle */ }
user := data.(*User)
```

---

### **Example 2: Nested Objects with Custom Parsing**
**Schema:**
```json
{
  "@schema": "v1/order",
  "properties": {
    "customer": {
      "type": "object",
      "@schema": "v1/user-base",
      "@bindings": { "name": { "mapper": "trim" } }
    },
    "items": {
      "type": "array",
      "items": { "type": "object", "@schema": "v1/product" }
    },
    "createdAt": { "type": "string", "format": "date-time", "@bindings": { "parser": "iso8601" } }
  }
}
```

**Input JSON:**
```json
{
  "customer": {
    "name": "   Alice   ",
    "email": "alice@example.com"
  },
  "items": [{"id": 1, "price": 19.99}],
  "createdAt": "2023-10-01T12:00:00Z"
}
```

**Resolved Go Struct:**
```go
type Order struct {
    Customer Customer `json:"customer"`
    Items    []Product `json:"items"`
    CreatedAt time.Time `json:"createdAt"`
}
```

---

### **Example 3: Error Handling**
**Schema:**
```json
{
  "@schema": "v1/invoice",
  "properties": {
    "total": { "type": "number", "minimum": 0 },
    "currency": { "type": "string", "enum": ["USD", "EUR"] }
  }
}
```

**Invalid Input:**
```json
{ "total": "-50", "currency": "XYZ" }
```

**Error Response:**
```json
{
  "errors": [
    { "field": "total", "message": "must be >= 0" },
    { "field": "currency", "message": "must be one of [USD, EUR]" }
  ]
}
```

---

## **4. Implementation Approaches**
The pattern can be implemented via:

### **A. Code Generation**
- **Tool:** [OpenAPI Generator](https://openapi-generator.tech/) / [protobuf Go Plugins](https://github.com/golang/protobuf)
- **Process:** Compile schemas into language-specific bindings (e.g., `User.go` from JSON schema).

### **B. Runtime Resolution (Dynamic)**
- **Framework:** [JSON Schema with Go](https://github.com/go-playground/validator) / [JSONata](https://jsonata.org/)
- **Example:**
  ```go
  package main
  import (
      "github.com/go-playground/validator/v10"
      "github.com/yourorg/binding"
  )
  func main() {
      schema := binding.MustLoad("schema.json")
      validator := validator.New()
      err := binding.ValidateWith(validator, inputJSON, schema)
      if err != nil { /* handle */ }
  }
  ```

### **C. Hybrid (Schema + Annotations)**
- **Example:** Use Go struct tags with `@binding` directives:
  ```go
  type User struct {
      Email string `json:"email" binding:"required,email"`
  }
  ```
  Resolver reads tags at runtime to validate against the schema.

---

## **5. Performance Considerations**
| **Factor**               | **Recommendation**                                                                 |
|--------------------------|-----------------------------------------------------------------------------------|
| **Schema Complexity**    | Flatten deeply nested schemas to reduce parsing overhead.                         |
| **Caching**              | Cache resolved types for frequent schemas (e.g., HTTP responses).                |
| **Validation Order**     | Validate required fields first to fail fast.                                     |
| **Schema Evolution**     | Use `@version` to handle backward-compatible changes (e.g., add optional fields). |

---

## **6. Related Patterns**
| **Pattern**                     | **Relationship**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Schema Registry](https://www.confluent.io/blog/schema-registry-apache-avro-backwards-compatibility/)** | Type Binding Resolution relies on schemas stored/retrieved here.              | Cross-language compatibility (e.g., Kafka).       |
| **[Data Transformation](https://micronaut-projects.github.io/micronaut-guide/latest/guide/#transformingData)** | Post-resolution transformation of bound data.                                  | Cleaning/mapping data before processing.          |
| **[OpenAPI/Swagger](https://swagger.io/specification/)**                     | Defines schemas for REST APIs; Type Binding resolves these into code.           | API documentation + client/server sync.          |
| **[Protocol Buffers](https://developers.google.com/protocol-buffers)**          | Structured binary formats with strong typing; Type Binding can serialize/deserialize. | High-performance systems (e.g., microservices).   |
| **[Kubernetes Custom Resources](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/)** | CRDs use JSON schemas; Type Binding resolves them into Go structs.            | Kubernetes operators.                              |

---

## **7. Best Practices**
1. **Schema Reusability**
   Use `@extends` to avoid duplicating common fields (e.g., `UserBase` schema).

2. **Immutable Schemas**
   Version schemas (`@version`) to enable safe upgrades (e.g., add optional fields).

3. **Validation First**
   Resolve types *before* processing to catch errors early (e.g., in API gateways).

4. **Document Schemas**
   Include `@description` fields for human-readable specs (e.g., `@description: "User's preferred timezone"`).

5. **Benchmark Resolvers**
   Compare tools like:
   - **JSON Schema Validator** (pure validation)
   - **JSONata** (transformation + validation)
   - **Codegen** (compile-time binding for max performance).

---
## **8. Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                  |
|-------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Type Mismatch**             | Schema expects `number` but gets `string`.                                 | Use `@bindings.parser` (e.g., `"parseFloat"`) |
| **Missing Required Field**    | Field marked `required` is absent.                                           | Check client input or schema `required` list. |
| **Circular References**       | Nested objects reference each other (e.g., `User.hasRole.Role.user`).        | Flatten schemas or use graph traversal.      |
| **Slow Resolution**           | Large schemas or complex mappings.                                           | Cache resolved types or generate static code. |

---
## **9. Example Tools/Libraries**
| **Language** | **Library**                                                                 | **Features**                                      |
|--------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| Go           | [go-playground/validator](https://github.com/go-playground/validator)       | Struct tag validation + custom bindings.          |
| Python       | [jsonschema](https://pypi.org/project/jsonschema/) + [pydantic](https://pydantic.dev/) | Compile-time type checking.                       |
| JavaScript   | [Ajv](https://ajv.js.org/) + [Zod](https://github.com/colinhacks/zod)      | Validation + inference.                           |
| Rust         | [serde_json](https://serde.rs/derive.json/) + [schema.rs](https://github.com/EmilHernvall/schema) | Macro-derived type binding.                     |

---
## **10. Migration Path**
1. **Audit Existing Code**
   Identify manual mappings (e.g., `json.Unmarshal` + `if-else` logic).
2. **Adopt a Schema Format**
   Choose JSON Schema, OpenAPI, or Protobuf based on your ecosystem.
3. **Incremental Replacement**
   Replace one mapping at a time; use both old and new code temporarily.
4. **Test Schema Evolution**
   Verify backward compatibility with `@version` flags.

---
**See Also:**
- [JSON Schema Specification](https://json-schema.org/)
- [OpenAPI Specification](https://spec.openapis.org/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers/docs/proto)