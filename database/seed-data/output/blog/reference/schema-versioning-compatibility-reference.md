**[Pattern] Schema Versioning and Compatibility – Reference Guide**
*FraiseQL Core Pattern*

---

### **Overview**
FraiseQL enforces strict **schema versioning and backward/forward compatibility** to ensure seamless migrations between client/server versions while preventing breaking changes. This pattern automates validation to detect unsafe schema modifications, including deprecated fields, renamed types, and incompatible type changes. Schemas evolve via explicit versioning (e.g., `v1.0` → `v2.0`), with the compiler enforcing compatibility rules at runtime. This guide outlines the technical implementation and requirements for this pattern.

---

### **Key Concepts**
| **Term**               | **Definition**                                                                 |
|--------------------------|---------------------------------------------------------------------------------|
| **Schema Version**       | A timestamped snapshot (e.g., `v20240515.1`) of a FraiseQL schema, stored in metadata. |
| **Backward Compatibility** | New versions must support legacy clients (e.g., allow missing optional fields). |
| **Forward Compatibility**   | Legacy clients must work with new versions (e.g., ignore unknown fields).       |
| **Breaking Change**      | A schema modification that invalidates existing queries (e.g., dropping a field). |
| **Migration Rule**       | Compiler-enforced constraints to validate compatibility (e.g., "no new required fields"). |

---

### **Schema Reference**
Schema versions are defined in a **`schema_version`** manifest file (JSON/YAML) with these fields:

| **Field**               | **Type**   | **Description**                                                                 |
|--------------------------|------------|-------------------------------------------------------------------------------|
| `version`                | `string`   | Semantic version (e.g., `v1.2.0`).                                             |
| `timestamp`              | `ISO-8601` | When the schema was published.                                                 |
| `dependencies`           | `object`   | External modules this schema relies on (e.g., `{ "fraction": "v1.1" }`).      |
| `rules`                  | `object`   | Migration constraints (see [Rules Table](#rules-table)).                     |
| **Schema Definitions**   |            |                                                                               |
| `types`                  | `array`    | List of types (e.g., `enum`, `struct`) with versioned schemas.                |
| `enums`                  | `object`   | Enum values and their compatibility status (`deprecated`, `removed`).          |
| `structs`                | `object`   | Struct fields with optional `version` and `deprecated` flags.                |

---
#### **Rules Table**
Compiler rules ensure compatibility. Violations raise errors during build:

| **Rule**                  | **Description**                                                                 | **Example Violation**                     |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| `no-required-fields`      | New versions cannot add required fields in structs.                           | Adding `age: number { required: true }`.   |
| `no-type-change`          | Field types cannot be changed (e.g., `string` → `number`).                    | Changing `name: string` → `name: int`.     |
| `deprecate-before-remove`| Fields/enums must be deprecated for ≥1 version before removal.               | Dropping `username` without a deprecation phase. |
| `enum-backward-compat`    | New enum values must be prefixed (e.g., `v2_pending`).                        | Adding `active` to an enum without `v2_`.  |

---

### **Implementation Steps**
#### **1. Define a Schema Version**
Modify `schema_version.json` to declare a new version:
```json
{
  "version": "v1.1.0",
  "timestamp": "2024-05-15T12:00:00Z",
  "rules": {
    "no-required-fields": true,
    "deprecate-before-remove": { "phase": "1" }
  },
  "dependencies": { "math": "v2.3" }
}
```

#### **2. Update Schema Definitions**
Add/modify types in `schema.graphql` (or equivalent):
```graphql
# Add a new optional field (compatible)
type User {
  id: ID!
  email: String!      # Required (unchanged)
  phone: String       # New optional field (compatible)
  legacyName: String  # Deprecated (phase=1)
}
```

#### **3. Validate Compatibility**
Run the FraiseQL compiler with `--check-compatibility`:
```bash
fraise compile --schema=schema.graphql --version=./schema_version.json --check-compatibility
```
- **Pass**: If all rules are satisfied.
- **Fail**: If violations exist (e.g., `User.phone` cannot become required).

---

### **Query Examples**
#### **Backward-Compatible Query**
**Schema (v1.0):**
```graphql
type Product { id: ID! name: String }
```
**Query (v1.0 client):**
```graphql
query { product(id: "1") { name } }
```

**Schema (v2.0):**
```graphql
type Product { id: ID! name: String price: Float }  # price is optional
```
**Query (v1.0 client still works):**
```graphql
query { product(id: "1") { name } }  # price is ignored
```

#### **Forward-Compatible Query**
**Schema (v1.0):**
```graphql
type Order { items: [Item!]! }
type Item { name: String quantity: Int }
```
**Query (v1.0 client):**
```graphql
query { order { items { name } } }
```

**Schema (v2.0):**
```graphql
type Order {
  items: [Item!]!
  total: Float @deprecated(phase: 1)  # Deprecated field
}
type Item {
  name: String
  quantity: Int
  sku: String  # New optional field
}
```
**Query (v2.0 server ignores `total`):**
```graphql
query { order { items { name sku } } }  # sku is optional
```

---

### **Handling Breaking Changes**
1. **Deprecate First**:
   Add `@deprecated(phase: N)` to fields/types for `N` versions before removal.
   ```graphql
   type Vertex { deprecatedField: Int @deprecated(phase: 2) }
   ```

2. **Schema Aliasing** (for non-breaking renames):
   Use `alias` to shadow old names:
   ```graphql
   type Vertex {
     oldName: String @alias(deprecated: true)
     newName: String
   }
   ```

3. **Versioned Imports**:
   Pin dependencies to specific versions in `schema_version.json`:
   ```json
   "dependencies": { "core": "v1.2.0" }
   ```

---

### **Related Patterns**
| **Pattern**                  | **Description**                                                                 |
|-------------------------------|---------------------------------------------------------------------------------|
| **[Aliasing](link)**          | Shadow deprecated fields/types without breaking queries.                          |
| **[Modular Schema](link)**   | Split schemas into reusable modules with explicit versioning.                   |
| **[Query Optimization](link)** | Leverage schema versioning to cache incompatible query results.                |
| **[Deprecation Policy](link)**| Standardize deprecation timelines and communication channels.                   |

---

### **Troubleshooting**
| **Issue**                     | **Solution**                                                                     |
|-------------------------------|---------------------------------------------------------------------------------|
| `Rule violation: no-type-change` | Use `alias` for renamed fields or wait for the deprecation phase to end.         |
| `Dependency mismatch`         | Update `schema_version.json` to match the latest compatible version.              |
| `Deprecated field in query`   | Replace with the new field or omit the query if the field is removed.            |

---
**See Also**:
- [FraiseQL Compiler Flags](#fraise-compile--check-compatibility)
- [Migration Checklist](link) (for large-scale updates).