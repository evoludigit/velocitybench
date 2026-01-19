# **[Pattern] Type Evolution Safety Reference Guide**

---

## **Overview**
The **Type Evolution Safety** pattern ensures backward and forward compatibility when modifying data structures, APIs, or schema definitions over time. Without this pattern, breaking changes to types (e.g., renaming fields, removing values, or modifying shapes) can cause cascading failures in systems relying on those types. This pattern provides mechanisms to safely evolve types while maintaining stability for existing consumers.

Use this pattern when:
- Refactoring APIs, database schemas, or serialization formats.
- Introducing breaking changes that must coexist with legacy systems.
- Requiring zero-downtime migrations for structural changes.

---

## **Key Principles**
1. **Backward Compatibility**: Existing consumers continue to work unchanged.
2. **Forward Compatibility**: New consumers can upgrade without breaking existing code.
3. **Gradual Adoption**: Minimal disruption by allowing parallel usage of old and new types.
4. **Validation**: Automatic or explicit checks to enforce usage rules.

---

## **Schema Reference**
Use the following conventions to define type evolution safely. This table outlines common strategies and their schema representations.

| **Strategy**                | **Old Schema**                     | **New Schema**                     | **Migration Mechanism**                          | **Use Case**                                  |
|-----------------------------|-------------------------------------|-------------------------------------|---------------------------------------------------|-----------------------------------------------|
| **Field Renaming**          | `{ "name": string }`                | `{ "oldName": string, "name": string }` | Shadow field with validation to deprecate `oldName`. | Phased renaming to avoid breaking calls.        |
| **Field Removal**           | `{ "deprecatedField": string }`     | `{}` (removed)                     | Ignore or emit warnings when `deprecatedField` is present. | Deprecate unused fields.                      |
| **Field Addition**          | `{ "requiredField": string }`       | `{ "requiredField": string, "optionalField": string }` | Mark `optionalField` as nullable.                  | Add non-breaking features.                    |
| **Union/Intersection Change**| `type A = { x: string } \| { y: int }` | `type A = { z: int }`               | Add a discriminator (`typeTag`) for compatibility. | Rewrite unions without breaking existing logic. |
| **Numeric Range Expansion**  | `{ "value": number (0-100) }`       | `{ "value": number (0-10000) }`     | Validate and clamp values during migration.       | Extend value ranges.                          |
| **Polymorphic Types**       | `type Shape = Circle \| Square`     | `type Shape = Circle \| Square \| Polygon` | Use a `kind` field to identify new types.          | Extend sealed hierarchies.                    |
| **Array Item Type Change**  | `{ "data": Array<string> }`         | `{ "data": Array<string \| number> }` | Validate or coerce types during serialization.    | Add supported types to existing arrays.       |

---

## **Implementation Details**
### **1. Field Renaming**
**Schema Evolution:**
```typescript
// Old Type
interface OldUser {
  username: string;
}

// New Type (with shadow field)
interface NewUser {
  username: string;       // Backward compatibility
  oldUsername?: string;   // Deprecated, will be removed later
}
```

**Validation Rules:**
- If `oldUsername` is present, emit a warning or deprecation notice.
- Client libraries should prefer `username` but accept both.

**Example Migration:**
```typescript
function migrateUser(user: OldUser | NewUser): NewUser {
  if ('oldUsername' in user) {
    console.warn('Deprecated field "oldUsername" detected.');
    return { ...user, username: user.username || user.oldUsername };
  }
  return user;
}
```

---

### **2. Field Removal**
**Schema Evolution:**
```typescript
// Old Type (with deprecated field)
interface LegacyConfig {
  timeout: number;
  deprecatedFlag?: boolean; // Will be removed
}
```

**Handling Legacy Data:**
- Skip validation for `deprecatedFlag` or emit warnings.
- Log deprecation notices during deserialization.

**Example:**
```typescript
function validateConfig(config: LegacyConfig): void {
  if (config.deprecatedFlag !== undefined) {
    console.warn('"deprecatedFlag" is no longer supported.');
  }
  if (config.timeout <= 0) {
    throw new Error('Invalid timeout value.');
  }
}
```

---

### **3. Field Addition**
**Schema Evolution:**
```typescript
// New Type (extends old type)
interface EnhancedUser {
  name: string;
  email?: string; // Optional
  role?: string;  // Optional
}
```

**Backward Compatibility:**
- New fields must be marked as optional (`?`).
- Existing code ignores new fields during serialization/deserialization.

---

### **4. Union/Intersection Changes**
**Schema Evolution:**
```typescript
// Old Union
type OldEvent = {
  type: 'login' | 'logout';
  userId: string;
};

// New Union (with discriminator)
type NewEvent =
  | { type: 'login'; userId: string; token: string }
  | { type: 'logout'; userId: string }
  | { type: 'refresh'; token: string };
```

**Migration:**
- Add a `typeTag` field to distinguish old/new variants:
  ```typescript
  type MigratedEvent =
    | { type: 'login'; userId: string; token?: string; _typeTag?: 'v1' }
    | { type: 'logout'; userId: string; _typeTag?: 'v1' };
  ```
- Use a runtime discriminator (e.g., `_typeTag`) to handle both formats.

---

### **5. Polymorphic Types**
**Schema Evolution:**
```typescript
// Old Type
type Shape = Circle | Square;

// New Type (with kind)
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'square'; side: number }
  | { kind: 'polygon'; sides: number[] };
```

**Backward Compatibility:**
- Add a `kind` field to identify legacy shapes:
  ```typescript
  type LegacyShape = Circle | Square | { kind: 'legacy-circle'; radius: number };
  ```
- Use a library like [`json-schema-to-typescript`](https://github.com/ThomasAribart/json-schema-to-typescript) to auto-generateTypeScript types.

---

## **Query Examples**
### **1. Validating New vs. Old Types**
```typescript
// Example: Migrate OldUser to NewUser
function safeDeserialize(userData: string): NewUser {
  const parsed = JSON.parse(userData);
  if ('oldUsername' in parsed) {
    return { ...parsed, name: parsed.oldUsername }; // Rename field
  } else {
    return parsed; // Assume backward-compatible JSON
  }
}
```

### **2. Schema Validation with `zod`**
```typescript
import { z } from 'zod';

const OldSchema = z.object({
  username: z.string(),
});

const NewSchema = z.object({
  username: z.string(),
  oldUsername: z.string().optional(),
}).refine(
  (data) => !(data.oldUsername && !data.username),
  'Username is missing.'
);

const result = NewSchema.safeParse({ username: 'alice', oldUsername: 'legacy_alice' });
console.log(result.error?.message); // Warnings but validates.
```

### **3. Database Migration (Prisma)**
```prisma
// Add a new field with a fallback
model User {
  id     Int     @id @default(autoincrement())
  name   String
  email  String?
  oldEmail String?  // For migration
}

function migrateUsers() {
  // Update legacy records
  await prisma.user.updateMany({
    where: { oldEmail: { not: null } },
    data: { email: { set: prisma.user.oldEmail } },
  });
}
```

---

## **Tools & Libraries**
| **Tool**               | **Purpose**                                      | **Example Use Case**                          |
|------------------------|--------------------------------------------------|-----------------------------------------------|
| [`json-schema-faker`](https://github.com/json-schema-faker) | Generate test data for evolving schemas.       | Test backward-compatible API changes.          |
| [`zod`](https://github.com/colinhacks/zod) | Runtime schema validation.                      | Validate incoming JSON with deprecated fields.|
| [`prisma`](https://www.prisma.io/) | Database migrations.                              | Add optional fields before removing old ones.   |
| [`ts-morph`](https://github.com/dsherret/ts-morph) | TypeScript schema manipulation.                 | Auto-generate backward-compatible types.      |

---

## **Related Patterns**
1. **[Schema Registry]** – Centralized versioning for evolving schemas (e.g., Avro, Protobuf).
2. **[Feature Flags]** – Gradually roll out new fields via config (e.g., LaunchDarkly).
3. **[Backward-Compatible APIs]** – Use versioned endpoints (e.g., `/v1/users`, `/v2/users`).
4. **[Lazy Initialization]** – Delay loading non-critical fields until needed.
5. **[Immutable Data Structures]** – Prevent accidental mutations during evolution.

---
## **Best Practices**
1. **Document Breaking Changes** – Clearly note deprecation timelines in release notes.
2. **Use Tooling** – Automate schema validation (e.g., `zod`, `ajv`).
3. **Test Gradually** – Deploy new types in staging before production.
4. **Monitor Usage** – Track deprecated fields with logging (e.g., Sentry, OpenTelemetry).
5. **Set a Deprecation Timeline** – Example:
   - **Phase 1 (6 months)**: Old field + warning.
   - **Phase 2 (3 months)**: Warning + enforcement.
   - **Phase 3 (1 month)**: Remove field.

---
## **Example Workflow**
1. **Refactor Type**:
   ```typescript
   // Before
   interface User { id: string; name: string; }

   // After (with evolution)
   interface User {
     id: string;
     name: string;
     oldName?: string; // Deprecated
   }
   ```
2. **Update Validation**:
   ```typescript
   function isDeprecatedUser(user: User): boolean {
     return 'oldName' in user && !user.name;
   }
   ```
3. **Roll Out**:
   - Deploy to 10% of traffic with warnings.
   - Log usage of `oldName`.
   - After 6 months, remove `oldName`.

---
## **Common Pitfalls**
| **Pitfall**                     | **Solution**                                  |
|----------------------------------|-----------------------------------------------|
| Forcing old types on new code.   | Use optional fields and runtime checks.       |
| Ignoring deprecation warnings.   | Auto-reject invalid usage after cutoff date.  |
| Breaking async consumers.        | Buffer changes in message queues (e.g., Kafka).|
| Memory leaks from unused fields. | Garbage-collect deprecated data periodically. |

---
## **Further Reading**
- [JSON Schema Draft 7: Backward Compatibility](https://json-schema.org/understanding-json-schema/reference/backwards-compatibility.html)
- [Protobuf Backward/Forward Compatibility](https://developers.google.com/protocol-buffers/docs/proto3#upward_compatibility)
- [Avro Schema Evolution](https://avro.apache.org/docs/current/evoschema.html)