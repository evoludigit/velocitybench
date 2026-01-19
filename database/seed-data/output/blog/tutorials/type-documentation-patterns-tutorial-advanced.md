```markdown
# **Type Documentation: Writing APIs Where Data Speaks for Itself**

Backend systems thrive on clarity—not just in code, but in how data is structured, consumed, and evolved over time. Yet, even well-designed APIs and databases can become confusing as they grow, especially when teams collaborate across time zones, languages, or domains. **Type documentation** is a pattern that embeds metadata directly into your data definitions, ensuring that machine-readable contracts and human-readable clarity coexist seamlessly.

Think of type documentation as a "Rosetta Stone" for your data. Instead of forcing developers to parse vague comments or external documentation (which quickly becomes outdated), you define explicit, self-documenting data structures. This pattern reduces friction in:
- **Onboarding new developers** (clear expectations from day one),
- **Debugging and monitoring** (metadata embedded in logs, traces, and alerts),
- **API versioning and compatibility** (explicit type contracts avoid silent breakages).

By the end of this post, you’ll see how type documentation can be applied to databases, serialization/deserialization layers, and API schema design—with practical tradeoffs and anti-patterns to avoid.

---

## **The Problem: When "Self-Documenting" Becomes Self-Contradictory**

A common pitfall in backend development is assuming that "good code" or "well-structured APIs" naturally convey their purpose. But in reality, many systems suffer from:
- **Silent complexity.** A seemingly simple `POST /users` endpoint may return nested objects with optional fields, discriminated unions, or dynamic schemas—but without documentation, developers waste time guessing the contract.
- **Coupling between docs and code.** Maintainers update either the codebase or the OpenAPI/Swagger docs, but never both, leading to **drift** (where the docs don’t match runtime behavior).
- **Inconsistent naming conventions.** Teams use camelCase, underscores, or snake_case interchangeably, or naming conflicts arise when "global" IDs become "user_ids" in APIs.
- **Debugging nightmares.** Logs and traces show raw data, but without type hints, you can’t easily distinguish between a valid `User` object and an invalid `PartialUser` in production errors.

### **The Cost of Ambiguity**
Consider this `POST /orders` request handler:

```typescript
// What does this function actually do? What if `order` is missing `userId`?
async function createOrder(req: Express.Request, res: Express.Response) {
  const order = req.body;
  // ...
}
```

A single glance at the code doesn’t tell you:
- Is `order` a `UserOrder` or `AdminOrder`?
- Is `order.items` required or optional?
- Is `order.shippingAddress` a nested object or an array?

This ambiguity forces developers to:
1. Read comments (which may not exist or be out of date),
2. Consult internal wikis or Confluence pages,
3. Invent ad-hoc validation (e.g., `if (!order.items) throw new Error(...)`),
4. Waste time diagnosing issues in production.

Type documentation removes these guesswork layers by encoding metadata directly into your data structures.

---

## **The Solution: Embedding Metadata in Data Types**

Type documentation is the practice of **attaching metadata to your data models** (databases, APIs, serialization layers) so that:
- Machines (e.g., ORMs, validators) can enforce constraints,
- Humans (e.g., devs, tooling) can infer purpose and usage,
- Tooling (e.g., OpenAPI generators, IDEs) can auto-generate docs.

The key principle: **No more "just trust me."** Every field should answer:
- *What is it?* (type, constraints),
- *Why does it exist?* (description, examples),
- *How should it be used?* (required, example values, deprecated fields).

### **Where Type Documentation Applies**
| Component               | Example Use Case                          | Where Metadata Goes          |
|-------------------------|------------------------------------------|------------------------------|
| **Database models**     | Enforce constraints, generate migrations | Column comments, enums       |
| **API schemas**         | Self-documenting OpenAPI/Swagger         | `description`, `example`     |
| **Serialization**       | Avoid silent field renames in JSON       | Schema versioning, aliases   |
| **Validation layers**   | Catch malformed data early               | Custom validators, error msgs |
| **Async/rpc layers**    | Distinguish between `User` and `AnonUser`| Discriminators, tags         |

---

## **Components of Type Documentation**

### **1. Core Elements (Every Field Should Have These)**
Every field should include at least:
- **Type** (explicit, non-ambiguous),
- **Description** (brief purpose),
- **Examples** (concrete usage),
- **Constraints** (nullable, regex, min/max).

Example (JSON Schema):
```json
{
  "type": "object",
  "properties": {
    "userId": {
      "type": "string",
      "description": "Unique identifier for the user (UUIDv4).",
      "format": "uuid",
      "examples": ["550e8400-e29b-41d4-a716-446655440000"]
    },
    "isAdmin": {
      "type": "boolean",
      "description": "Whether the user has admin privileges (default: false).",
      "default": false
    }
  },
  "required": ["userId"]
}
```

### **2. Advanced Patterns**
| Pattern                | Use Case                          | Example                          |
|------------------------|-----------------------------------|----------------------------------|
| **Discriminated unions** | Handle polymorphic data          | `"type": "User" \| "Guest"`      |
| **Versioning**        | Manage backward-compatible changes | `"$schema": "v1"`                |
| **Aliases**           | Transparent field renames         | `"dbField": "created_at"`        |
| **Enums**             | Restrict to valid values          | `"enum": ["active", "inactive"]` |
| **Null handling**     | Clarify `null`, `undefined`, `""` | `"nullable": true`               |

### **3. Tooling Integration**
- **Database:** Use migrations to embed constraints (e.g., PostgreSQL `CHECK` constraints).
- **API:** Leverage OpenAPI/Swagger or JSON Schema validators.
- **Serialization:** Libraries like `class-validator` (NestJS) or `zod` (TypeScript) can auto-generate docs.

---

## **Code Examples**

### **Example 1: Self-Documenting Database Model (PostgreSQL)**
```sql
-- A table with embedded metadata via comments and constraints
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  -- { "type": "string", "description": "UUIDv4 generated by the system" }
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),
  -- { "type": ["string", "null"], "description": "User's full name (max 100 chars)." }
  name TEXT CHECK (LENGTH(name) <= 100),
  -- { "type": "boolean", "description": "Flag indicating if the account is active." }
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  -- { "enum": ["email", "phone"], "default": "email" }
  notification_method VARCHAR(10) CHECK (notification_method IN ('email', 'phone')) DEFAULT 'email'
);

-- A discriminated union for roles (stored as JSONB with metadata)
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  -- { "type": "object", "properties": {
  --   "type": { "type": "string", "enum": ["User", "Admin", "Guest"] },
  --   "permissions": { "type": "array", "items": { "type": "string" } }
  -- } }
  metadata JSONB NOT NULL
);
```

### **Example 2: OpenAPI Schema with Full Type Documentation**
```yaml
# openapi.yaml
paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        201:
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  schemas:
    UserCreate:
      type: object
      description: Input for creating a new user.
      properties:
        email:
          type: string
          format: email
          description: |
            User's email address.
            Must be unique and validated.
          example: "user@example.com"
        password:
          type: string
          format: password
          description: |
            Plaintext password (hashed internally).
            Must be at least 8 characters.
          minLength: 8
          writeOnly: true  # Hidden in docs
        metadata:
          type: object
          description: |
            Arbitrary key-value pairs (e.g., preferences).
            No validation or constraints.
          additionalProperties: true
          nullable: true
```

### **Example 3: TypeScript with Zod for Runtime Validation**
```typescript
// zod-schema.ts
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid("Must be a valid UUID"),
  name: z.string().min(1, "Name is required").max(100),
  isAdmin: z.boolean().default(false),
  // Discriminated union for roles
  role: z.discriminatedUnion("type", [
    z.object({
      type: z.literal("user"),
      permissions: z.array(z.literal("read", "write")).default(["read"])
    }),
    z.object({
      type: z.literal("admin"),
      permissions: z.array(z.literal("read", "write", "delete")).default(["read", "write", "delete"])
    })
  ])
});

// Auto-generate OpenAPI docs from Zod
const openapiSchema = JSON.stringify(UserSchema._def, null, 2);
```

### **Example 4: Database-to-API Aliasing (Handling Schema Drift)**
```typescript
// sql-to-api.ts
interface DBUser {
  user_id: string;  // DB column
  first_name: string;
  last_name: string;
}

interface APIUser {
  id: string;       // API field
  name: string;     // Merged first + last
  displayName: string | null; // Optional alias
}

export function transformUser(dbUser: DBUser): APIUser {
  return {
    id: dbUser.user_id,
    name: `${dbUser.first_name} ${dbUser.last_name}`,
    displayName: dbUser.first_name ? `${dbUser.first_name}'s Profile` : null
  };
}
```

---

## **Implementation Guide**

### **Step 1: Audit Your Current Schema**
Start by documenting **existing** types. Tools like:
- [SQLDelight](https://cashapp.github.io/sqldelight/) (for mobile/DB sync),
- [Prisma](https://www.prisma.io/) (for ORM schemas),
- [OpenAPI Generator](https://openapi-generator.tech/) (for API docs)
can extract metadata from your codebase.

### **Step 2: Enforce Consistency**
- **Naming:** Use a convention (e.g., `snake_case` for DB, `camelCase` for API).
- **Versioning:** Add `$schemaVersion` fields to track changes.
- **Deprecation:** Mark obsolete fields with `deprecated: true`.

### **Step 3: Integrate with Tooling**
| Tool          | How to Use                          | Example                          |
|---------------|-------------------------------------|----------------------------------|
| **Zod (TS)**  | Validate and infer JSON Schema       | `z.object({ ... }).parse(data)`   |
| **Prisma**    | Auto-generate type-safe queries     | `prisma.user.create()`           |
| **OpenAPI**   | Auto-document APIs                  | `@ApiProperty({ description: '...' })` |
| **Postman**   | Import OpenAPI for interactive docs | `postman collection export`      |

### **Step 4: Automate Testing**
Write tests that verify:
- The schema matches runtime behavior,
- Deprecated fields are ignored,
- Optional fields are handled correctly.

```typescript
// test-schema.ts
import { UserSchema } from "./zod-schema";

test("validates required fields", () => {
  const error = UserSchema.parse({}).catch(e => e);
  expect(error.message).toContain("email is required");
});

test("rejects invalid UUID", () => {
  const error = UserSchema.parse({ id: "not-a-uuid", email: "test@example.com" }).catch(e => e);
  expect(error.message).toContain("Must be a valid UUID");
});
```

---

## **Common Mistakes to Avoid**

### **1. Overloading Fields with Multiple Types**
❌ **Bad:**
```json
{
  "status": { "type": ["string", "number"] }  // What does "5" mean?
}
```
✅ **Better:**
```json
{
  "status": {
    "type": "object",
    "properties": {
      "code": { "type": "number" },
      "message": { "type": "string" }
    },
    "description": "Status with code (e.g., 200) and human-readable message."
  }
}
```

### **2. Ignoring Nullability**
❌ **Bad:**
```typescript
interface User {
  name: string;  // Could be `null`, `undefined`, or empty string?
}
```
✅ **Better:**
```typescript
interface User {
  name: string | null;  // Explicitly handle null cases
}
```

### **3. Documentation Drift**
❌ **Bad:**
```yaml
# openapi.yaml
properties:
  password:
    type: string
    description: "User's password (plaintext)."
```
But in reality, passwords are hashed in the DB → **docs and code mismatch.**

✅ **Better:**
```yaml
properties:
  password:
    type: string
    format: password
    description: "Plaintext password (hashed before storage)."
    writeOnly: true  # Never returned
```

### **4. Overcomplicating Discriminated Unions**
❌ **Bad:**
```typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; sides: number[] };
```
✅ **Better (if possible):**
```typescript
interface Shape {
  kind: "circle" | "rectangle" | "triangle";
  // Common fields (e.g., color) can be in a base interface
  color?: string;
}
```

### **5. Not Versioning Schemas**
❌ **Bad:**
```json
{ "type": "object", "properties": { "user": {} } }
```
After changes:
```json
{ "type": "object", "properties": { "user_id": {} } }
```
→ **Breaking change** if consumers expect `user`.

✅ **Better:**
```json
{ "$schema": "v1", "properties": { "user": {} } }
```
Later:
```json
{ "$schema": "v2", "properties": { "user_id": {} } }
```

---

## **Key Takeaways**
- **Type documentation** = **metadata embedded in data** (not just in comments or docs).
- **Self-documenting systems** reduce ambiguity in APIs, databases, and logging.
- **Tradeoff:** Slightly more upfront work (schema definitions) saves time long-term.
- **Key patterns:**
  - Use discriminated unions for polymorphic data,
  - Version schemas to avoid breaking changes,
  - Alias fields when DB/API structures differ,
  - Enforce constraints at the database level.
- **Tools to leverage:** Zod (TS), OpenAPI, Prisma, SQLDelight.

---

## **Conclusion: Build for the Machines—and the Humans**

Type documentation isn’t about making your system "perfect"—it’s about **reducing friction** for everyone who interacts with it. Developers no longer need to guess whether a field is required or how to format a date. Operators can parse logs without poring over internal wikis. And when you inevitably add a new feature (e.g., "soft deletes"), the metadata travels with it, ensuring clarity from day one.

Start small:
1. Pick **one API endpoint** and fully document its schema.
2. Add **type validation** to catch issues early.
3. Gradually expand to databases and internal services.

The payoff? Fewer late-night debugging sessions, fewer "but the docs said it would work" incidents, and APIs that evolve with your team—not against it.

---
**What’s your biggest pain point with API/database documentation? Share your struggles (or solutions) in the comments—I’d love to hear how you’ve tackled similar challenges!**
```