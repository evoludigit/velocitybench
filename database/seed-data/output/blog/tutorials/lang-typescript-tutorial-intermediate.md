```markdown
# Mastering TypeScript Language Patterns for Robust Backend Development

![TypeScript Logo](https://www.typescriptlang.org/favicon.ico)

As backend engineers, we're constantly juggling complexity while trying to maintain type safety, readability, and performance. TypeScript offers powerful language features that can help us build more maintainable systems—**but only if we use its patterns intentionally**.

Most teams adopt TypeScript primarily for its compile-time type checking, but many miss out on deeper language patterns that solve real-world backend problems: precise API return types, immutable data handling, and declarative configuration. This tutorial dives into concrete TypeScript patterns that will make your backend code more robust, predictable, and easier to maintain.

Let’s explore practical patterns—not just theoretical concepts—so you can apply them immediately in your projects.

---

## The Problem: Uncontrolled Complexity in Backend Code

Without deliberate TypeScript patterns, backend systems often suffer from:

1. **Type Ambiguity in APIs**
   When APIs return loosely-typed data (e.g., `any` or `unknown`), debugging and refactoring become painful. A failed API call might return a mix of success and error shapes, leaving you guessing the structure.

2. **Mutable State Risks**
   JavaScript’s dynamic nature makes it easy to inadvertently mutate sensitive objects (e.g., database models or config settings), leading to subtle bugs.

3. **Error Handling Overload**
   Many backend teams use `try/catch` blocks for everything, mixing runtime errors (e.g., DB connection failures) with valid business logic flows. This confusion harms maintainability.

4. **Boilerplate Configuration**
   Repeatedly defining similar interfaces for database schemas, HTTP responses, or ORM entities creates cognitive overhead.

5. **Testing Nightmares**
   Mocking APIs or services with loose types forces developers to manually assert contracts, increasing test flakiness.

---

## The Solution: Intentional TypeScript Patterns

TypeScript’s type system isn’t just about catching typos—it’s a toolkit for **explicitly modeling your application’s domain**. Here’s how:

1. **Precise API Return Types**: Replace vague `any` with discriminated unions or mapped types to enforce clear contracts.
2. **Immutable Data Handling**: Use `readonly`, `record`, and `as const` to prevent accidental mutations.
3. **Structured Error Handling**: Define custom error types with exhaustive error unions for cleaner logic.
4. **Configuration Patterns**: Generate reusable interfaces from runtime values (e.g., environment variables).
5. **Testing-Friendly Types**: Shape types for mocking/stubbing to reduce boilerplate.

Let’s dive into each of these with actionable examples.

---

## Core Pattern: **Discriminated Unions for API Responses**

### The Problem
A common backend pattern is returning API responses like:
```typescript
{ success: true, data: User[] } | { success: false, error: string }
```
But this is fragile. Over time, the `error` shape might expand (e.g., `{ code: number; message: string }`), breaking clients.

### The Solution: **Discriminated Unions**
Define a union type with a discriminator property to enforce consistent response shapes.

#### Example: HTTP API Response
```typescript
// 1. Define error types (closed set of possible errors)
type DatabaseError = { kind: "database"; reason: string };
type ValidationError = { kind: "validation"; field: string; message: string };

// 2. Union type with discriminator
type ApiResponse<T> =
  | { kind: "success"; data: T }
  | { kind: "error"; error: DatabaseError | ValidationError };

// 3. Usage in a service
async function fetchUser(id: string): Promise<ApiResponse<User>> {
  try {
    const user = await db.query("SELECT * FROM users WHERE id = ?", [id]);
    return { kind: "success", data: user };
  } catch (err) {
    if (err instanceof TypeORMError) {
      return { kind: "error", error: { kind: "database", reason: err.message } };
    }
    // Handle other errors...
  }
}

// 4. Exhaustiveness check (TypeScript will warn if you miss a case)
function handleResponse<T>(response: ApiResponse<T>) {
  switch (response.kind) {
    case "success":
      return response.data;
    case "error":
      console.error("Error:", response.error);
      // No default needed (exhaustive union)
      break;
  }
}
```

### Why This Works
✅ **Exhaustive Validation**: TypeScript ensures all error cases are handled.
✅ **Evolvable**: Adding new error types forces updates to clients.
✅ **Tooling-Friendly**: Autocomplete works for `data` or `error` based on response shape.

---

## Pattern: **Immutable Data with `readonly` and `Record`**

### The Problem
Backend code often works with configuration objects (e.g., database settings, feature flags) that shouldn’t be modified after creation. Without safeguards, you might accidentally alter critical values:
```typescript
const config = { dbUrl: "postgres://..." };
config.dbUrl = "mongodb://..."; // Oops!
```

### The Solution: **Immutable Types**
Combine `readonly`, `as const`, and `Record` to prevent mutations.

#### Example: Database Configuration
```typescript
// 1. Define a closed set of config options
type DatabaseConfig = {
  readonly type: "postgres" | "mongo" | "mysql";
  readonly url: string;
  readonly poolSize?: number;
};

// 2. Create immutable config at runtime
const dbConfig = {
  type: "postgres",
  url: process.env.DB_URL,
  poolSize: parseInt(process.env.POOL_SIZE || "10"),
} satisfies DatabaseConfig; // Type assertion for safety

// 3. Prevent mutations
dbConfig.url = "invalid"; // TypeScript error!

// 4. Use in a function with guarded access
function connectDatabase(config: Readonly<DatabaseConfig>) {
  // ... (config.url is readonly, but we can still use it)
}
```

#### Advanced: **`as const` for Literal Types**
If your config is known at compile-time (e.g., from a config file):
```typescript
const dbSettings = {
  host: "localhost",
  port: 5432,
} as const;

// `dbSettings` is now `Readonly<{ readonly host: "localhost"; readonly port: 5432 }>`
```

### Key Benefits
✅ **No Silent Mutations**: Prevents bugs where config objects change unexpectedly.
✅ **Self-Documenting**: `readonly` signals "don’t touch me!"
✅ **Works with `Record`**: Combine with `Record<string, T>` for dynamic keys.

---

## Pattern: **Custom Error Types for Structured Handling**

### The Problem
Throwing plain `Error` objects forces runtime type checking:
```typescript
try {
  const user = await getUser(123);
} catch (err) {
  if ((err as ApiError).statusCode === 404) { // Ugly!
    // Handle 404...
  }
}
```

### The Solution: **Error Classes with Subtypes**
Create a hierarchy of error classes to model domain-specific failures.

#### Example: API Error System
```typescript
// 1. Base error class
class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// 2. Subclasses for different error types
class NotFoundError extends ApiError {
  constructor(message: string, public readonly resource: string) {
    super(404, message);
  }
}

class ValidationError extends ApiError {
  constructor(message: string, public readonly errors: Record<string, string[]>) {
    super(400, message);
  }
}

// 3. Usage
function getUser(id: number) {
  if (!id) throw new ValidationError("ID is required", { id: ["must be provided"] });

  const user = db.users.find(u => u.id === id);
  if (!user) throw new NotFoundError(`User ${id} not found`, "user");

  return user;
}

// 4. Type-safe handling
async function loadUser() {
  try {
    const user = await getUser(123);
    // ...
  } catch (err) {
    if (err instanceof NotFoundError) {
      console.log(`Fallback: Use default user`);
    } else if (err instanceof ValidationError) {
      // Handle validation errors
    } else {
      // Handle unexpected errors
    }
  }
}
```

### Why This Matters
✅ **Compile-Time Safety**: No runtime casts or `instanceof` checks.
✅ **Explicit Logic**: Each error type has its own handler.
✅ **Stack Traces**: Error classes preserve call stack info.

---

## Pattern: **Generating Interfaces from Runtime Data**

### The Problem
DB schemas, HTTP payloads, or config files often change frequently. Writing new interfaces for each schema is tedious:
```typescript
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}
```

### The Solution: **Type Inference from Runtime Values**
Use `typeof` or `zod`/`io-ts` to derive types from existing data.

#### Example 1: DB Schema to Type
```typescript
// 1. Start with a query result
const queryResult = {
  id: "123",
  name: "Alice",
  email: "alice@example.com",
  createdAt: "2024-01-01T00:00:00Z",
};

// 2. Infer the type
type User = typeof queryResult;

// 3. Use generically
function processUser(user: User) {
  console.log(user.name.toUpperCase());
}
```

#### Example 2: With `zod` (Recommended for APIs)
```typescript
import { z } from "zod";

// 1. Define schema (runtime + compile-time)
const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
});

// 2. Infer type
type User = z.infer<typeof UserSchema>;

// 3. Parse input
const user = UserSchema.parse({
  id: "123",
  name: "Bob",
  email: "bob@example.com",
});

// Works with runtime checks
if (!UserSchema.safeParse(user).success) {
  throw new Error("Invalid user data");
}
```

### Tradeoffs
| Approach       | Pros                          | Cons                          |
|----------------|-------------------------------|-------------------------------|
| `typeof`       | Zero dependency, simple       | Manual updates for changes     |
| `zod`/`io-ts`  | Runtime validation + types    | Adds runtime overhead          |

---

## Implementation Guide: **Putting It All Together**

### Step 1: Project Setup
Add these dependencies to your `package.json`:
```json
"dependencies": {
  "zod": "^3.22.4", // For validation and type inference
  "io-ts": "^2.2.20" // Alternative to zod (heavy on runtime checks)
}
```

### Step 2: Define Core Types
Create a `types/api.ts` file:
```typescript
// Domain types
export type User = {
  id: string;
  name: string;
  email: string;
};

// API response type (discriminated union)
export type ApiResponse<T> =
  | { kind: "success"; data: T }
  | { kind: "error"; error: ApiError };

export type ApiError =
  | { code: "NOT_FOUND"; message: string; resource: string }
  | { code: "VALIDATION"; errors: Record<string, string[]> };
```

### Step 3: Create a Service with Type Safety
```typescript
// services/user.service.ts
import { db } from "../db";
import { User, ApiResponse } from "../types/api";

export async function getUser(id: string): Promise<ApiResponse<User>> {
  const user = await db.query("SELECT * FROM users WHERE id = ?", [id]);

  if (!user) {
    return {
      kind: "error",
      error: { code: "NOT_FOUND", message: "User not found", resource: "user" },
    };
  }

  return { kind: "success", data: user };
}
```

### Step 4: Implement a Controller
```typescript
// controllers/user.controller.ts
import { Request, Response } from "express";
import { getUser } from "../services/user.service";

export function handleGetUser(req: Request, res: Response) {
  const { id } = req.params;

  getUser(id)
    .then(response => {
      if (response.kind === "error") {
        return res.status(400).json(response);
      }
      res.json(response.data);
    })
    .catch(err => {
      res.status(500).json({
        kind: "error",
        error: { code: "INTERNAL_ERROR", message: err.message },
      });
    });
}
```

### Step 5: Add Unit Tests
```typescript
// tests/user.service.test.ts
import { getUser } from "../services/user.service";

describe("getUser", () => {
  it("returns success if user exists", async () => {
    // Mock DB
    jest.spyOn(db, "query").mockResolvedValueOnce({ id: "123", name: "Alice" });

    const result = await getUser("123");
    expect(result.kind).toBe("success");
  });

  it("returns NOT_FOUND error", async () => {
    jest.spyOn(db, "query").mockResolvedValueOnce(undefined);
    const result = await getUser("999");
    expect(result.error).toEqual(
      expect.objectContaining({ code: "NOT_FOUND" })
    );
  });
});
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Overusing `any` or `unknown`
**Anti-pattern**:
```typescript
function processData(data: any) { /* ... */ }
// or
async function fetchData(): Promise<unknown> { /* ... */ }
```
**Problem**: TypeScript loses its power—you’re back to runtime checks.

**Fix**: Use discriminated unions or `zod` for explicit shapes.

---

### ❌ Mistake 2: Ignoring Exhaustiveness in Unions
**Anti-pattern**:
```typescript
type ApiResponse<T> = { ... } | { ... };
function handle(response: ApiResponse<User>) {
  if (response.status === "success") { // Missing other cases!
    // ...
  }
}
```
**Problem**: Future changes might introduce unhandled cases.

**Fix**: Use `exhaustive switch` (TypeScript 5.0+) or `never` unions:
```typescript
function handle(response: ApiResponse<User>) {
  switch (response.kind) {
    case "success":
      // ...
      break;
    default:
      const _exhaustiveCheck: never = response; // Fails if new cases are added
  }
}
```

---

### ❌ Mistake 3: Mutating Config Objects
**Anti-pattern**:
```typescript
const config = { db: { url: "postgres://..." } };
config.db.url = "mysql://..."; // Silent bug!
```
**Fix**: Mark config as `readonly` or use `Object.freeze`:
```typescript
const config = { db: { url: "postgres://..." } } as const;
Object.freeze(config); // Prevents mutation entirely
```

---

### ❌ Mistake 4: Not Leveraging `satisfies`
**Anti-pattern**:
```typescript
const user = {
  id: "123",
  name: "Alice",
} satisfies { id: string; name: string; email: string }; // No warning!
```
**Problem**: `user` doesn’t match the required type.

**Fix**: Use `satisfies` to enforce type compliance:
```typescript
const user = {
  id: "123",
  name: "Alice",
  email: "alice@example.com",
} satisfies { id: string; name: string; email: string }; // OK
```

---

### ❌ Mistake 5: Overcomplicating Error Handling
**Anti-pattern**:
```typescript
try { ... } catch (err) {
  if (err instanceof Error) {
    if (err.message.includes("not found")) { // Magic strings!
      // ...
    }
  }
}
```
**Fix**: Use custom error classes as shown in the [Error Types](#pattern-custom-error-types) section.

---

## Key Takeaways

### ✅ **For APIs**
- Use **discriminated unions** to enforce response shapes.
- Prefer **custom error types** over vague `Error` objects.
- Validate inputs/outputs with **`zod`/`io-ts`** for robustness.

### ✅ **For Data**
- Mark configs/models as **`readonly`** to prevent mutations.
- Use **`as const`** for literal types in static configs.
- Generate types from **runtime data** to stay in sync.

### ✅ **For Testing**
- Mock APIs with **explicit types** to avoid runtime surprises.
- Use **exhaustive unions** to catch unhandled cases.

### ✅ **Tradeoffs to Consider**
| Pattern               | When to Use                          | Avoid When...                     |
|-----------------------|--------------------------------------|-----------------------------------|
| Discriminated Unions  | API responses, error handling        | Schema is highly dynamic          |
| `readonly`            | Configs, DB models                    | You need runtime mutations         |
| Custom Errors         | Domain-specific failures              | Errors are generic (use `Error`)   |
| `zod`/`io-ts`         | Input validation                      | Performance is critical (use `typeof`) |

---

## Conclusion: TypeScript as a Backend Superpower

TypeScript isn’t just about catching typos—it’s a **toolkit for modeling your application’s behavior at compile time**. By adopting these patterns, you’ll:

✅ **Reduce runtime bugs** through static guarantees.
✅ **Improve maintainability** with explicit types and immutability.
✅ **Enhance collaboration** (other devs understand the contract).
✅ **Ship faster** with fewer edge-case surprises.

The key is to **start small**: pick one pattern (e.g., discriminated unions for API responses) and iteratively improve your codebase. Over time, these small investments compound into a more robust backend.

### Next Steps
1. **Experiment**: Pick one pattern (e.g., error types) and refactor a module.
2. **Share**: Introduce the pattern to your team with a PR.
3. **Iterate**: Use TypeScript’s feedback to improve your types.

TypeScript isn