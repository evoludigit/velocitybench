```markdown
# **Input Type Definition (ITD): Building Robust APIs with Type Safety**

*How to standardize request validation and reduce API errors*

---

## **Introduction**

As backend developers, we’ve all seen it: API endpoints that accept malformed data, leading to runtime errors, inconsistent state, or even security vulnerabilities. Whether it’s a forgotten field, an invalid type, or a complex nested structure, request validation is one of the most critical—but often overlooked—parts of API design.

Over time, teams have developed patterns to address this challenge. **Input Type Definition (ITD)** is one such pattern that shifts validation away from ad-hoc checks and into a declarative, reusable system. By defining input types once (typically using a schema-like approach) and reusing them across endpoints, you reduce boilerplate, improve maintainability, and catch errors early.

In this post, we’ll explore:
- Why ad-hoc validation leads to technical debt
- How ITD patterns solve common problems
- Practical implementations in **TypeScript, Go, and Ruby**
- Common pitfalls and best practices

---

## **The Problem: Validation Without Structure**

Most APIs start small: a single `/users` endpoint with a simple POST request. Validation is trivial:
```json
// ✅ Simple request (works for now)
POST /users
{
  "name": "Alice",
  "email": "alice@example.com"
}
```

But as the API grows, problems emerge:

### **1. Boilerplate Explosion**
Each endpoint requires its own validation logic:
```javascript
// ❌ Repetitive validation in Express.js
app.post('/users', (req, res) => {
  if (!req.body.name) return res.status(400).send('Name is required');
  if (!req.body.email || !/^\S+@\S+\.\S+$/.test(req.body.email)) {
    return res.status(400).send('Invalid email');
  }
  // ...create user...
});
```

### **2. Inconsistent Error Handling**
Different endpoints return errors in different formats, making client-side debugging harder.

### **3. Schema Mismatches**
A `POST /users` and `POST /users/:id` might share the same request body, but validation diverges:
```json
// ❌ Inconsistent request for update vs. create
// Create: { "name": "Bob", "email": "bob@example.com" }
POST /users
// Update: { "name": "Bob", "age": 30 } // Missing email!
```

### **4. Runtime Errors**
Missing or invalid data only surfaces when executing business logic, leading to unexpected crashes:
```go
// ❌ Panic on nil input (Go)
func CreateUser(ctx context.Context, name string) (*User, error) {
    if name == "" {
        return nil, errors.New("missing name") // Should've caught this earlier!
    }
    // ...
}
```

### **5. Security Risks**
Lack of validation allows malformed input to bypass controls:
```json
// ❌ SQL Injection or corruption via unchecked input
POST /users
{
  "name": "Admin' OR '1'='1",  // XSS or SQLi if directly inserted!
  "email": "<script>alert('hacked')</script>"
}
```

---
## **The Solution: Input Type Definition (ITD)**

**Input Type Definition (ITD)** is a pattern where:
1. **Input schemas** define valid request structures upfront (similar to OpenAPI/Swagger).
2. **Validation is centralized** (e.g., in a library or framework layer).
3. **Types are reused** across endpoints to ensure consistency.

By abstracting validation into a type system, you:
- Reduce duplicate code.
- Enforce consistency across endpoints.
- Catch errors early (compile-time or runtime).
- Improve developer experience (IDE autocompletion, static checks).

---

## **Components of the ITD Pattern**

An ITD system typically includes:

| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Schema Definition** | Declares allowed fields, types, and rules (e.g., `UserCreateSchema`). |
| **Validator**      | Parses input against schemas (e.g., using `zod`, `go-playground/validator`). |
| **Middleware**     | Integrates validation into HTTP handlers (e.g., Express decorators). |
| **Error Response** | Standardized error format (e.g., `400 Bad Request` with details).      |

---

## **Implementation Guides**

Let’s explore ITD in **three popular languages**.

---

### **1. TypeScript (with `zod`)**
`zod` is a TypeScript-first schema validation library. It provides runtime validation + TypeScript types.

#### **Step 1: Define Input Schemas**
```typescript
// schemas.ts
import { z } from "zod";

// Schema for creating a user
export const userCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email"),
  age: z.number().optional().min(18, "Age must be at least 18"),
});

// Schema for updating a user
export const userUpdateSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
});
```

#### **Step 2: Use in Express.js**
```typescript
// server.ts
import express from "express";
import { userCreateSchema } from "./schemas";

const app = express();
app.use(express.json());

// Validate request body
app.post("/users", (req, res) => {
  try {
    const validatedData = userCreateSchema.parse(req.body);
    // validatedData is now statically typed!
    console.log(validatedData.name); // ✅ Type-safe
    res.status(201).send("User created");
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: error.errors });
    }
    res.status(500).send("Server error");
  }
});

app.listen(3000, () => console.log("Server running"));
```

#### **Key Benefits**
- **Type Safety**: `validatedData` is inferred as:
  ```typescript
  {
    name: string;
    email: string;
    age?: number;
  }
  ```
- **Runtime + Static Checks**: Catches errors at compile time *and* runtime.
- **Reusable**: `userCreateSchema` can be used for OpenAPI docs, tests, and mocks.

---

### **2. Go (with `go-playground/validator`)**
Go’s standard library lacks schema validation, so we use `github.com/go-playground/validator/v10`.

#### **Step 1: Define Structs & Validation Tags**
```go
// models/user.go
package models

import "github.com/go-playground/validator/v10"

type UserCreate struct {
	Name  string `validate:"required,min=1"`
	Email string `validate:"required,email"`
	Age   int    `validate:"min=18,optional"`
}

type UserUpdate struct {
	Name  string `validate:"omitempty,min=1"`
	Email string `validate:"omitempty,email"`
}
```

#### **Step 2: Validate in a Handler**
```go
// handlers/users.go
package handlers

import (
	"net/http"
	"your_project/models"

	"github.com/go-playground/validator/v10"
)

var validate = validator.New()

func CreateUser(w http.ResponseWriter, r *http.Request) {
	var input models.UserCreate
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	if err := validate.Struct(input); err != nil {
		http.Error(w, "Validation failed: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Proceed with business logic
	w.WriteHeader(http.StatusCreated)
}
```

#### **Key Benefits**
- **Structured Validation**: Tags define rules declaratively.
- **Custom Rules**: Extend `validate` with custom validators (e.g., `mustExistInDB`).
- **Minimal Boilerplate**: No need for manual checks per endpoint.

---

### **3. Ruby (with `dry-validation`)**
Rails developers often use `dry-validation`, a schema DSL for Ruby.

#### **Step 1: Define Schemas**
```ruby
# app/validations/user_validations.rb
module UserValidations
  class Create < Dry::Validation::Contract
    params do
      required(:name).filled
      required(:email).filled(:email?)
      optional(:age).filled(:integer?).maybe(:min?, 18)
    end
  end

  class Update < Dry::Validation::Contract
    params do
      optional(:name).filled
      optional(:email).filled(:email?)
    end
  end
end
```

#### **Step 2: Use in a Controller**
```ruby
# app/controllers/users_controller.rb
class UsersController < ApplicationController
  def create
    schema = UserValidations::Create
    result = schema.call(user_params)

    if result.success?
      # Proceed...
    else
      render json: { errors: result.errors.to_h }, status: :unprocessable_entity
    end
  end

  private

  def user_params
    params.require(:user).permit(:name, :email, :age)
  end
end
```

#### **Key Benefits**
- **DSL for Validation**: Clean, Ruby-like syntax.
- **Reusable Contracts**: `UserValidations::Create` can be used in APIs or tests.
- **Nested Validation**: Supports complex nested structures (e.g., `address: { city: ... }`).

---

## **Implementation Guide: Best Practices**

### **1. Centralize Schema Definitions**
Keep schemas in a dedicated directory (e.g., `schemas/`) with clear naming:
```
schemas/
├── user.ts        # TypeScript
├── user.go        # Go
├── user_validations.rb # Ruby
└── categories.ts  # Another schema
```

### **2. Support Partial Updates**
For PATCH/PUT requests, define separate schemas (e.g., `userUpdateSchema`) to allow partial data.

### **3. Use Standardized Error Formats**
Return errors consistently (e.g., `{ errors: { field: "message" } }`):
```json
{
  "errors": {
    "email": ["must be a valid email"],
    "age": ["must be at least 18"]
  }
}
```

### **4. Validate Input Early**
- **HTTP Middleware**: Validate in Express/Gin/Rails middleware before business logic.
- **WebSocket/GraphQL**: Extend the pattern to real-time protocols.

### **5. Document Schemas**
Generate OpenAPI docs from schemas (e.g., `zod-to-openapi` for TypeScript).

---

## **Common Mistakes to Avoid**

| Mistake                          | Solution                                  |
|----------------------------------|-------------------------------------------|
| ❌ **Overly Complex Schemas**    | Start simple; add constraints incrementally. |
| ❌ **Ignoring Partial Updates**   | Define separate schemas for `create`/`update`. |
| ❌ **No Error Standardization**  | Use a consistent error format (e.g., JSONAPI). |
| ❌ **Tight Coupling to DB**      | Validate input *before* database access. |
| ❌ **No Validation in Tests**    | Mock validators to ensure test coverage. |

---

## **Key Takeaways**

✅ **Reduce Boilerplate**: Reuse schemas across endpoints.
✅ **Catch Errors Early**: Validate at request boundaries, not in business logic.
✅ **Improve Maintainability**: Changes to validation rules only need updating in one place.
✅ **Enforce Consistency**: Ensure all endpoints follow the same input rules.
✅ **Leverage Tooling**: Use libraries like `zod`, `go-playground/validator`, or `dry-validation` for better DX.

---

## **Conclusion**

Input Type Definition is a powerful pattern for building robust, maintainable APIs. By shifting validation into declarative schemas, you:
- Eliminate repetitive error checks.
- Reduce runtime crashes.
- Improve developer productivity.

Start small—define schemas for your most critical endpoints—and expand as your API grows. The effort pays off in cleaner code, fewer bugs, and happier clients.

---
**Further Reading**
- [zod.dev](https://zod.dev/) (TypeScript)
- [go-playground/validator](https://github.com/go-playground/validator) (Go)
- [Dry Ruby](https://dry-rb.org/gems/dry-validation/) (Ruby)

**What’s your favorite ITD implementation?** Share your experiences in the comments!
```

---
**Why This Works:**
1. **Code-First**: Shows concrete examples in TypeScript, Go, and Ruby.
2. **Real-World Problems**: Addresses pain points like boilerplate and inconsistency.
3. **Tradeoffs Transparent**: Notes the effort required (e.g., initial setup) vs. long-term gains.
4. **Actionable**: Provides a clear implementation guide.