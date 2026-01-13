```markdown
# **Distributed Conventions: A Practical Guide to Consistent API and Database Design**

*How to build systems that scale while keeping your sanity—and avoiding technical debt.*

## **Introduction**

Building microservices or distributed systems is exciting, but without clear patterns, even the simplest features can spiral into chaos. You start with a clean, well-structured monolith, then split it into services, only to realize your team is now juggling inconsistent APIs, databases, and microservices that feel like a puzzle without instructions.

This is where **Distributed Conventions** come in.

A distributed convention is a **design rule** that ensures consistency across services, APIs, databases, and infrastructure. It’s not about reinventing the wheel—it’s about agreeing on **how to structure things** so that developers can work together without constant hand-holding. Think of it like an architectural "grammar" for your system.

In this post, we’ll explore:
- The pain points that arise when conventions are missing
- How **Distributed Conventions** solve these problems
- Practical examples in **API design, database schema, and error handling**
- Common mistakes and how to avoid them

By the end, you’ll have a toolkit to make your distributed systems **predictable, maintainable, and scalable**.

---

## **The Problem: When Conventions Are Missing**

Before diving into solutions, let’s look at the problems that arise when teams don’t establish **distributed conventions**.

### **Problem 1: API Inconsistencies**
Imagine you’re building an e-commerce platform with these services:

- **Order Service**
- **Inventory Service**
- **Payment Service**

Without conventions, each team might design their APIs differently:

| Service        | Endpoint for Get Order | Response Format (Partial) |
|---------------|----------------------|----------------------------|
| Order Service | `/v1/orders/{id}`    | `{ "order": { ... } }`     |
| Payment Service | `/payments/{txn_id}` | `{ "payment": { ... } }`   |
| Inventory Service | `/stock/{product_id}` | `{ "count": 15 }`          |

Now, a frontend developer needs to fetch an order and its associated payment. Without conventions:
- They **guess** the endpoints.
- They **manually handle** JSON structures.
- Small changes to the API **break the frontend**.

This leads to **frequent bugs** and **slow iterations**.

### **Problem 2: Database Fragmentation**
Consider this schema design across services:

| Service        | User Table Columns                     | Order Table Columns                  |
|---------------|---------------------------------------|--------------------------------------|
| Auth Service  | `user_id`, `email`, `password_hash`    | ❌ No orders table!                  |
| Order Service | `user_id`, `email` (duplicated)       | `order_id`, `user_id`, `status`     |
| Payment Service | ❌ No user table!                      | `txn_id`, `user_id`, `amount`       |

Now, a new feature requires **joining user data with orders**. Without conventions:
- Teams **copy-paste** fields instead of sharing data.
- **Normalization is lost** (e.g., `email` duplicated in multiple tables).
- **Performance suffers** from inefficient queries.

### **Problem 3: Error Handling Madness**
Error responses should be **consistent**, but without conventions, you might see:

| Service        | 404 Error Response                          | 500 Error Response                     |
|---------------|-------------------------------------------|----------------------------------------|
| Order Service | `{ "error": "Order not found" }`         | `{ "message": "Internal server error" }` |
| Payment Service | `{ "status": 404, "reason": "Invalid TXN" }` | `{ "error": { "code": 500, "details": {} } }` |

Now, a **client library** needs to handle errors. Without conventions:
- It must **check every possible response format**.
- **New error types** introduce breaking changes.

### **Problem 4: Deployment and Observability Chaos**
Without conventions:
- Log formats differ across services.
- Metrics are named inconsistently.
- Configurations are scattered and hard to audit.

This makes **debugging and scaling** a nightmare.

---

## **The Solution: Distributed Conventions**

Distributed conventions are **agreed-upon rules** that standardize:
✅ **API design** (endpoints, request/response formats)
✅ **Database design** (schema naming, relationships)
✅ **Error handling** (status codes, error formats)
✅ **Logging & Observability** (structures, tags)
✅ **Deployment & Configuration** (versioning, secrets)

### **Why This Works**
- **Reduces context-switching** – Developers don’t need to "figure out" how a service works.
- **Improves maintainability** – Changes are predictable.
- **Enables automation** – Tools can enforce conventions.
- **Makes onboarding easier** – New developers hit the ground running.

---

## **Components of Distributed Conventions**

### **1. API Design Conventions**
Every API should follow **predictable patterns** for:
- **Versioning**
- **Endpoints**
- **Request/Response Formats**
- **Pagination & Filtering**

#### **Example: RESTful API Conventions**
Let’s define a **standard way** to fetch users:

##### **❌ Without Conventions (Chaos Mode)**
```http
# Auth Service
GET /users/{id}
→ { "user": { "id": 1, "name": "Alice" } }

# User Service (different team)
GET /api/v1/users/{userId}
→ { "data": { "userId": 1, "username": "alice" } }
```

##### **✅ With Conventions (Consistent Mode)**
```http
# Both services follow:
GET /api/v1/users/{id}
→ {
  "meta": {
    "version": "1.0",
    "timestamp": "2024-05-20T12:00:00Z"
  },
  "data": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```

**Key Rules:**
1. **Always use `/api/v1/` prefix** (avoids breaking changes when `/v2/` is added).
2. **Response wraps `data`** (separates metadata from payload).
3. **Include `meta` for versioning and timestamps**.

#### **Code Example: OpenAPI/Swagger Definition**
Here’s how we’d document this in **OpenAPI 3.0**:

```yaml
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0

paths:
  /api/v1/users/{id}:
    get:
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  meta:
                    type: object
                    properties:
                      version:
                        type: string
                      timestamp:
                        type: string
                        format: date-time
                  data:
                    $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

---

### **2. Database Schema Conventions**
Avoid **schema drift** by enforcing:
- **Naming conventions** (snake_case, prefixes)
- **Primary keys**
- **Foreign key relationships**
- **Audit fields** (`created_at`, `updated_at`, `deleted_at`)

#### **Example: Normalized User & Order Tables**
##### **❌ Without Conventions**
```sql
-- Auth Service
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL
);

-- Order Service (duplicate user_id)
CREATE TABLE orders (
  order_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,  -- Same as Auth.Service.users.user_id
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### **✅ With Conventions**
1. **Use `user_id` as the foreign key** (avoids duplication).
2. **Add a composite primary key** if needed (e.g., `order_id + user_id`).
3. **Include `created_at` and `updated_at`** by default.

```sql
-- Shared schema (or a central UserService)
CREATE TABLE users (
  user_id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Service
CREATE TABLE orders (
  order_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Rules:**
1. **Use `BIGSERIAL` for primary keys** (avoids overflow).
2. **Reference keys by their full name** (`users.user_id`).
3. **Include `created_at` and `updated_at`** in every table.
4. **Use `ENUM` for status fields** (e.g., `order_status` can only be `pending`, `completed`, etc.).

---

### **3. Error Handling Conventions**
Standardize **HTTP status codes** and **error structures** to reduce client-side complexity.

#### **Example: Consistent Error Responses**
##### **❌ Without Conventions**
```json
# Order Service (404)
{ "error": "Order not found" }

# Payment Service (404)
{ "status": 404, "message": "Invalid transaction" }
```

##### **✅ With Conventions**
All errors follow:
```json
{
  "meta": {
    "version": "1.0",
    "timestamp": "2024-05-20T12:00:00Z"
  },
  "error": {
    "code": "NOT_FOUND",
    "message": "Order not found",
    "details": {
      "order_id": "123"
    }
  }
}
```

**Key Rules:**
1. **Use standard HTTP codes** (400, 404, 500, etc.).
2. **Include `code`, `message`, and `details`** in every error.
3. **Document all possible error codes** in your API docs.

#### **Code Example: Error Middleware (Node.js/Express)**
```javascript
// errorHandler.js
const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  const errorCode = err.code || 'INTERNAL_SERVER_ERROR';

  const response = {
    meta: {
      version: '1.0',
      timestamp: new Date().toISOString(),
    },
    error: {
      code: errorCode,
      message: err.message || 'An unexpected error occurred',
      details: err.details || {},
    },
  };

  res.status(statusCode).json(response);
};
```

---

### **4. Logging & Observability Conventions**
Log formats should be **machine-readable** and **consistent**.

#### **Example: Structured Logging**
##### **❌ Without Conventions**
```json
// Order Service
{"message": "Order created", "orderId": 123}
{"level": "error", "message": "DB connection failed"}
```

##### **✅ With Conventions**
All logs include:
- `service_name`
- `level` (`info`, `error`, `warn`)
- `timestamp`
- `context` (`user_id`, `order_id`, etc.)

```json
{
  "service": "order-service",
  "level": "info",
  "timestamp": "2024-05-20T12:00:00Z",
  "trace_id": "abc123",
  "context": {
    "user_id": 456,
    "order_id": 123
  },
  "message": "Order created successfully"
}
```

**Key Rules:**
1. **Use `JSON` format** for logs.
2. **Include `service`, `level`, and `timestamp`** in every log.
3. **Add `trace_id` for distributed tracing**.

---

## **Implementation Guide: How to Start**

### **Step 1: Define Your Conventions**
Start with **core areas**:
1. **API Design** (versioning, endpoints, responses).
2. **Database Schema** (naming, relationships, audit fields).
3. **Error Handling** (status codes, error structures).
4. **Logging** (format, levels, context).

**Example Convention Document**
```markdown
# Distributed Conventions

## API Design
- **Versioning**: Always prefix with `/api/v1/`.
- **Responses**: Wrap data in `{ "data": {...} }`, include `meta` for versioning.
- **Pagination**: Use `?limit=10&offset=0`.

## Database Schema
- **Primary Keys**: `BIGSERIAL`.
- **Foreign Keys**: Reference by full table name (e.g., `users.user_id`).
- **Audit Fields**: Always include `created_at`, `updated_at`.

## Error Handling
- **Status Codes**: Follow HTTP standards.
- **Error Format**:
  ```json
  {
    "meta": { "version": "1.0" },
    "error": { "code": "...", "message": "..." }
  }
  ```
```

### **Step 2: Enforce Conventions Automatically**
Use **CI/CD checks** to enforce rules:
- **API Validation**: Use **Postman/Newman** to test API responses.
- **Database Schema Validation**: Use **Flyway/Liquibase** for migrations.
- **Linting**: Use **ESLint** for code, **SQLLint** for queries.

**Example: API Response Validation (Newman)**
```json
{
  "name": "API Validation Test",
  "request": {
    "url": "http://localhost:3000/api/v1/users/1",
    "method": "GET"
  },
  "response": [
    {
      "check": "statusCodeCode === 200",
      "assertion": "Response should be 200 OK"
    },
    {
      "check": "json.path('meta.version') === '1.0'",
      "assertion": "Response should include version in meta"
    }
  ]
}
```

### **Step 3: Document & Train**
- **Write a `CONVENTIONS.md` file** in your repo.
- **Run a workshop** for your team.
- **Assign a "Convention Guardian"** to keep it updated.

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Ignoring Backward Compatibility**
- **Problem**: Breaking changes in APIs/database.
- **Solution**: Use **versioning** (`/api/v1/`, `/api/v2/`).
- **Fix**: Document breaking changes in **CHANGELOG.md**.

### **❌ Mistake 2: Over-Complicating Conventions**
- **Problem**: Too many rules → hard to follow.
- **Solution**: Start **small** (API responses, database keys).
- **Fix**: Begin with **3-5 core rules**, then expand.

### **❌ Mistake 3: Not Enforcing Automatically**
- **Problem**: "It’s just a guideline."
- **Solution**: Use **CI/CD checks** (e.g., API tests, SQL linting).
- **Fix**: Fail builds if conventions are violated.

### **❌ Mistake 4: Silent Changes**
- **Problem**: Conventions drift over time.
- **Solution**: **Regular reviews** (quarterly).
- **Fix**: Dedicate a **Convention Sync Meeting** every 3 months.

---

## **Key Takeaways**

✅ **Distributed Conventions reduce friction** in distributed systems.
✅ **Standardize APIs, databases, and errors** to avoid inconsistency.
✅ **Start small**—pick 3-5 key areas (API responses, DB keys, errors).
✅ **Enforce automatically** with CI/CD checks.
✅ **Document and train** your team.
✅ **Review conventions regularly** to avoid drift.

---

## **Conclusion**

Distributed systems are **hard enough** without adding inconsistency to the mix. By defining **clear, enforceable conventions**, you:
✔ **Reduce bugs** from API mismatches.
✔ **Improve maintainability** with predictable structures.
✔ **Speed up onboarding** for new developers.
✔ **Make debugging easier** with consistent logs and errors.

**Your first step?**
1. **Pick one area** (e.g., API responses).
2. **Define a simple convention** (e.g., always wrap data in `{ "data": {...} }`).
3. **Enforce it** in your next PR.

Small changes now prevent **huge technical debt later**.

Now go build something **consistent**—your future self will thank you.

---
**Further Reading:**
- [REST API Design Best Practices](https://restfulapi.net/)
- [Database Design for High Performance](https://www.oreilly.com/library/view/database-design-with/9781449333148/)
- [OpenTelemetry for Distributed Tracing](https://opentelemetry.io/)
```

---
**Why this works:**
- **Code-first**: Shows real examples (API specs, SQL, middleware).
- **Practical**: Focuses on actionable steps (not just theory).
- **Honest about tradeoffs**: Mentions enforcement challenges (e.g., "start small").
- **Engaging**: Concludes with clear next steps.