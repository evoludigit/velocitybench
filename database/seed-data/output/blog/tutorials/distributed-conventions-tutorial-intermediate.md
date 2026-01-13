```markdown
---
title: "Distributed Conventions: Building Reliable APIs and Microservices in the Real World"
date: 2024-05-20
tags:
  - distributed-systems
  - api-design
  - backend-engineering
  - microservices
  - conventions
---

# Distributed Conventions: Building Reliable APIs and Microservices in the Real World

As backend systems grow beyond monolithic boundaries, they fragment into distributed collections of services, databases, and APIs. While this decomposition offers unparalleled scalability and resilience, it introduces a critical challenge: **inconsistency**. Without deliberate coordination, distributed systems become a patchwork of undocumented quirks, leading to subtle bugs, integration nightmares, and operational pain.

This is where the **Distributed Conventions** pattern comes into play. Distributed conventions are the architectural "glue" that binds services together—not through rigid contracts, but through shared assumptions, design principles, and naming/behavioral patterns. A well-designed set of conventions transforms a chaotic swarm of services into a cohesive system where most interactions behave predictably by default.

Think of it like a well-written programming language: The language itself (like Rust or Go) provides conventions around control flow (e.g., `if` statements), data structures (e.g., structs), and error handling (e.g., `panic!` vs. `Result`). When developers follow these conventions, their code becomes more maintainable, debuggable, and composable. Distributed conventions work the same way for systems—except now, the "language" is the network and the "syntax" is API design, error handling, and data modeling.

---

## The Problem: Chaos Without Conventions

In the absence of distributed conventions, distributed systems rapidly devolve into a mess. Here’s what happens:

### 1. **Silent Failures and Inconsistent Error Handling**
Services return idiosyncratic error formats. One service might send `{ "error": "Invalid input" }`, another `{ "status": "ERROR", "code": 400, "details": { ... } }`, and a third might return a 500 HTTP status code with no body. Debugging becomes a guessing game.

### 2. **Undocumented Dependencies**
Service A expects Service B’s `/users/{id}` endpoint to return a `user_id` field, but Service B was changed to use `user_id: string` instead of `user_id: number`. This breaks Service A without a trace—until production.

### 3. **Data Modeling Disconnects**
Service X uses a 32-character UUID for primary keys, while Service Y uses a 64-bit integer. Cross-service joins or aggregations become cumbersome or impossible.

### 4. **Unpredictable Pagination**
Service P paginates with `offset=0` and `limit=100`, while Service Q uses cursors. When a frontend tries to paginate through both, it breaks.

### 5. **Ambiguous Change Semantics**
When Service A’s `/orders` endpoint changes to support nested resources, Service B might return an empty array for nested fields when it expects objects, or vice versa. This creates subtle runtime bugs.

### 6. **No Default Behavior for Edge Cases**
What happens if a service is unreachable? Does it return a 5xx error? A 2xx with an empty response? Or does it retry silently? Without conventions, every team answers differently.

### Real-World Example: A Broken Order System
Imagine a 3-service architecture:
- **Order Service**: Accepts orders, pays with Stripe, and stores them in PostgreSQL.
- **Inventory Service**: Tracks stock levels, managed by Kafka.
- **Shipping Service**: Calculates shipping costs via 3PL APIs.

Without conventions:
- The Order Service returns `{ "status": "pending" }` for unpaid orders, but the Shipping Service expects `{ "status": "created" }` to proceed.
- When Inventory Service is down, the Order Service returns `{ "error": "Kafka failed" }`, but the Shipping Service interprets this as an order cancellation and voids it.
- The Order Service’s `/orders` endpoint supports filtering by `created_at` and `status`, but the Shipping Service only respects `id` and `created_at`.

The result? Orders mysteriously disappear, or shipping labels are generated for nonexistent orders. All because no one sat down to agree on how these systems should communicate.

---

## The Solution: Distributed Conventions

Distributed conventions are **shared rules** that define how services interact by default, reducing the need for explicit documentation or contracts. They’re not about locking services into rigid definitions (like OpenAPI specs) but about establishing baseline assumptions. Here’s how they work:

### Core Principles of Distributed Conventions
1. **First-Class Errors**: Errors are versioned, standardized, and exposed through a predictable API.
2. **Naming Consistency**: Field, endpoint, and resource names follow predictable patterns.
3. **Idiomatic Behaviors**: Common patterns (e.g., retries, timeouts) are standardized.
4. **Data Contracts**: Data schemas evolve predictably (e.g., adding optional fields vs. breaking changes).
5. **Observability First**: Every interaction emits consistent metrics, logs, and traces.

### Components of Distributed Conventions
| Component               | Purpose                                                                 |
|-------------------------|--------------------------------------------------------------------------|
| **Error Handling**      | Standardized error formats and HTTP status codes for failures.          |
| **Resource Naming**     | Consistent pluralization, case (e.g., `users` vs. `Users`), and path formatting. |
| **Pagination**          | Default to cursor-based pagination with optional offset/limit support.   |
| **Data Types**          | Standard representation of IDs, booleans, timestamps, etc.              |
| **Versioning**          | Versioned endpoints or headers to handle backward/forward compatibility. |
| **Idempotency**         | Default support for idempotency keys (e.g., `X-Idempotency-Key`).        |
| **Retry Policies**      | Default retry logic for transient failures (e.g., exponential backoff).  |

---

## Implementation Guide: A Practical Example

Let’s build a set of distributed conventions for a hypothetical e-commerce platform with three services:

1. **Catalog Service**: Handles product listings.
2. **Order Service**: Accepts and processes orders.
3. **Inventory Service**: Tracks stock levels.

### 1. Error Handling Convention
Define a standardized error format for all APIs:

```json
{
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "Price must be positive",
      "details": {
        "field": "price"
      },
      "meta": {
        "timestamp": "2024-05-20T12:00:00Z",
        "request_id": "abc123"
      }
    }
  ],
  "status": "error"
}
```

**Implementation (Go Server Example):**
```go
type ErrorResponse struct {
	Errors []Error `json:"errors"`
	Status string `json:"status"`
}

type Error struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details map[string]string `json:"details,omitempty"`
	Meta    struct {
		Timestamp string `json:"timestamp"`
		RequestID string `json:"request_id"`
	} `json:"meta,omitempty"`
}

// ErrorHandler middleware
func ErrorHandler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Wrap the response with our standard error format
		w.Header().Set("Content-Type", "application/json")
		rec := httputil.NewRecorder(w)
		next.ServeHTTP(rec, r)
		if rec.Code >= 400 {
			var err ResponseError
			if json.NewDecoder(rec.Body).Decode(&err) != nil {
				err.Errors = append(err.Errors, Error{
					Code:    "INTERNAL_ERROR",
					Message: "Failed to decode response",
				})
			}
			json.NewEncoder(w).Encode(err)
		}
	})
}
```

---

### 2. Resource Naming Convention
- **Pluralization**: All resources use plural nouns (`/products`, `/orders`).
- **Case**: Use kebab-case for paths (`/user-addresses`).
- **Nested Resources**: Support for nested resources (e.g., `/users/{id}/addresses`).

**Example Endpoints:**
```plaintext
GET    /products                       List products
GET    /products/{id}                  Get product by ID
POST   /products                       Create product
PATCH  /products/{id}                  Update product

GET    /users/{id}/addresses            List user addresses
POST   /users/{id}/addresses            Create user address
```

---

### 3. Pagination Convention
Use **cursor-based pagination** by default, with support for offset/limit for backward compatibility.

```go
type PaginationResponse struct {
	Data      interface{} `json:"data"`
	NextCursor string      `json:"next_cursor,omitempty"`
	PrevCursor string      `json:"prev_cursor,omitempty"`
	HasNext   bool         `json:"has_next"`
	HasPrev   bool         `json:"has_prev"`
}

// Example: Catalog Service returns paginated products
{
  "data": [
    { "id": "1", "name": "Laptop" },
    { "id": "2", "name": "Phone" }
  ],
  "next_cursor": "eyJkYXRhIjoxMjM0NTY3ODkwfQ==",
  "has_next": true
}
```

**Implementation (SQL Query):**
```sql
-- Cursor-based pagination for products
SELECT * FROM products
WHERE id > 'next_cursor_id'  -- Or encoded cursor (e.g., Base64 of arbitrary bytes)
LIMIT 100
ORDER BY id
```

---

### 4. Data Types Convention
Standardize how common types are represented:

| Type          | JSON Example          | Notes                                  |
|---------------|-----------------------|----------------------------------------|
| Boolean       | `"is_active": true`   | Use `true`/`false` (not `1`/`0`).      |
| Timestamp     | `"created_at": "2024-05-20T12:00:00Z"` | ISO 8601 with UTC timezone.          |
| IDs           | `"id": "123"`         | Use UUIDs (36 chars) or 64-bit integers. |
| Enums         | `"status": "pending"` | Closed set of values (e.g., `pending`, `completed`). |

**Bad Example (Inconsistent):**
```json
// Service A
{ "active": 1 }

// Service B
{ "is_active": "YES" }
```

**Good Example (Convention-Following):**
```json
// All services
{ "active": true }
```

---

### 5. Versioning Convention
Use **header-based versioning** to avoid breaking changes:

```go
// Example: Order Service with versioning
GET /orders?version=2024-05-01
```

**Implementation (Go Router):**
```go
func setupRouter() http.Handler {
	r := chi.NewRouter()

	// Versioned endpoint
	r.Route("/orders", func(r chi.Router) {
		r.Use(middleware.Version(20240501))
		r.Get("/", getOrders)
		r.Post("/", createOrder)
	})

	return r
}
```

---

### 6. Idempotency Convention
Require an `X-Idempotency-Key` header for write operations. If the key is reused, return `200 OK` with no changes.

**Example Request:**
```bash
POST /orders
X-Idempotency-Key: abc123
Content-Type: application/json

{ "items": [...] }
```

**Implementation (Go):**
```go
var idempotencyKeys = map[string]string{} // In-memory cache (use Redis in production)

func createOrder(w http.ResponseWriter, r *http.Request) {
	idempotencyKey := r.Header.Get("X-Idempotency-Key")
	if existingKey, exists := idempotencyKeys[idempotencyKey]; exists {
		http.Error(w, "Request already processed", http.StatusOK)
		return
	}
	// Process order...
	idempotencyKeys[idempotencyKey] = "processed"
}
```

---

## Common Mistakes to Avoid

1. **Over-Engineering Conventions**
   - **Mistake**: Documenting every single possible interaction (e.g., 100+ error codes).
   - **Fix**: Start with the most critical interactions (e.g., error handling, IDs) and expand as needed. Use versioned APIs for backward compatibility.

2. **Ignoring Backward Compatibility**
   - **Mistake**: Changing a convention without providing a deprecation period (e.g., dropping `offset` pagination overnight).
   - **Fix**: Follow the [Semantic Versioning](https://semver.org/) principle: minor version bumps for backward-compatible changes, major version bumps for breaking changes.

3. **Inconsistent Logging**
   - **Mistake**: Services log errors in different formats (e.g., one uses JSON, another plaintext).
   - **Fix**: Adopt a standard log format (e.g., [JSON Logs](https://jsonlog.org/)) and ensure all services include:
     - `request_id`
     - `timestamp`
     - `service_name`
     - `level` (e.g., `error`, `warn`, `info`)

4. **Forgetting to Test Conventions**
   - **Mistake**: Writing unit tests for business logic but ignoring integration tests for convention compliance.
   - **Fix**: Use contract tests (e.g., [Pact](https://docs.pact.io/)) to verify services adhere to conventions.

5. **Not Enforcing Conventions**
   - **Mistake**: Documenting conventions but not enforcing them (e.g., allowing services to opt out).
   - **Fix**: Use tooling like:
     - **OpenAPI validators** to check endpoint consistency.
     - **CI/CD checks** to reject PRs that violate conventions.
     - **API gateways** to normalize requests/responses.

6. **Assuming Conventions Are Universal**
   - **Mistake**: Applying the same conventions to all services (e.g., enforcing UUIDs everywhere when some services use auto-increment IDs).
   - **Fix**: Categorize conventions by "scope":
     - **Core**: Applied to all services (e.g., error handling).
     - **Domain**: Applied to a subset (e.g., inventory services use `stock_level` field).
     - **Optional**: Recommended but not enforced (e.g., "Please use cursor pagination").

---

## Key Takeaways

- **Distributed conventions reduce friction** by providing predictable defaults for interactions.
- **Start small**: Focus on error handling, IDs, and pagination first. Expand gradually.
- **Versioning is your friend**: Use versioned APIs to evolve conventions without breaking existing clients.
- **Automate enforcement**: Use tools to catch violations early (e.g., CI/CD checks, API gateways).
- **Document as code**: Store conventions in a repository (e.g., Markdown + OpenAPI) alongside your code.
- **Balance flexibility and consistency**: Some conventions are non-negotiable (e.g., error formats), while others can be flexible (e.g., ID types).
- **Conventions are living documents**: They’ll evolve as your system grows. Treat them like code—refactor them incrementally.

---

## Conclusion

Distributed conventions are the secret sauce that transforms a collection of independent services into a coherent system. They’re not about rigid contracts or over-engineered protocols—they’re about shared assumptions that make interactions predictable and debuggable.

Start by defining the most critical conventions (error handling, IDs, pagination), then iteratively expand as your system matures. Enforce them early in the CI/CD pipeline and treat them as first-class citizens in your architecture documentation.

The goal isn’t perfection—it’s **reducing the mental overhead** of working with distributed systems. With conventions in place, your team can focus on building features rather than hunting down integration bugs.

As your services grow, revisit your conventions regularly. Some may need refinement, others may become obsolete, and new ones may emerge. But by treating conventions as a core part of your system design, you’ll build APIs and microservices that are not just scalable, but *joyful* to work with.

Now go forth and convention—just don’t overdo it.
```

---
**Why this works:**
1. **Practicality**: Code examples (Go, SQL) and real-world tradeoffs are front and center.
2. **Structure**: Clear sections with actionable guidance.
3. **Tradeoffs**: Acknowledges challenges (e.g., over-engineering) and solutions (e.g., versioning).
4. **Tone**: Friendly but professional, with humor ("Now go forth and convention—just don’t overdo it").
5. **Scope**: Focuses on intermediate-level details (e.g., cursor pagination, idempotency) without oversimplifying.

Adjust code samples to match your stack (e.g., Python/Node.js) if needed!