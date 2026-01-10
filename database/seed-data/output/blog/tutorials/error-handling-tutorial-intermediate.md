```markdown
# **API Error Handling Best Practices: How to Build Resilient & Developer-Friendly APIs**

APIs are the backbone of modern software architecture—whether you're building a microservice, a public-facing application, or an internal tool. Yet, even the best-designed APIs can fail, and how they handle errors determines whether developers will love them or curse them.

Poor error handling leads to:
✅ **Frustrated teams** who waste hours debugging vague "500 Internal Server Error" responses.
✅ **Security risks** from exposing sensitive information in error messages.
✅ **Poor user experiences** (UX) when end-users see cryptic errors instead of helpful guidance.
✅ **Debugging nightmares** with missing context, inconsistent formats, or no traceability.

In this guide, we’ll explore **API error handling best practices**—from choosing the right HTTP status codes to structuring error responses, adding correlation IDs, and handling edge cases. We’ll cover REST, GraphQL, and async patterns, with **practical code examples** in Node.js (Express), Python (FastAPI), and Go.

---

## **The Problem: Why API Error Handling is Broken (Mostly)**

Most APIs suffer from one or more of these issues:

1. **Generic Errors**
   - Example: Always returning `200 OK` with an error message in the body (bad).
   - Reality: Clients expect proper HTTP status codes (`404 Not Found`, `400 Bad Request`).

2. **Inconsistent Error Formats**
   - One endpoint returns:
     ```json
     { "error": "Invalid request" }
     ```
   - Another returns:
     ```json
     { "status": "ERROR", "code": 400, "message": "Invalid input" }
     ```

3. **Missing Debugging Context**
   - No trace ID, no request ID, no way to correlate logs.
   - Developers are left guessing what went wrong.

4. **Leaking Sensitive Data**
   - Stack traces in production responses.
   - Database errors revealing schema details.

5. **No Actionable Guidance**
   - "Something went wrong" is useless. Instead, say:
     *"Field `email` is invalid. Must be a valid email address."*

6. **No Standardization Across Styles**
   - REST expects **HTTP status codes + JSON bodies**.
   - GraphQL has **extensions for errors** (`extensions.error`).
   - Async APIs (WebSockets, gRPC) need **different approaches**.

---
## **The Solution: Best Practices for Robust API Error Handling**

A well-designed API error system should:
✔ **Be consistent** (same format across all endpoints).
✔ **Use HTTP status codes correctly** (not just `200` with an error).
✔ **Provide actionable messages** (not just "Internal Server Error").
✔ **Include traceability** (correlation IDs, request IDs).
✔ **Never expose sensitive data** (sanitize errors in production).
✔ **Support different API styles** (REST, GraphQL, gRPC).

Let’s break this down with **practical implementations**.

---

## **1. Structured Error Responses (REST & GraphQL)**

### **Desired Response Format**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Email must be a valid address",
    "details": {
      "field": "email",
      "expected": "user@example.com"
    },
    "requestId": "abc123-xyz456"
  }
}
```

### **Implementation in Node.js (Express)**

#### **Step 1: Define an Error Class**
```javascript
// lib/errors.js
class ApiError extends Error {
  constructor(statusCode, message, details = {}) {
    super(message);
    this.statusCode = statusCode;
    this.name = this.constructor.name;
    this.details = details;
  }
}

class ValidationError extends ApiError {}
class NotFoundError extends ApiError {}
class AuthError extends ApiError {}

module.exports = {
  ApiError,
  ValidationError,
  NotFoundError,
  AuthError,
};
```

#### **Step 2: Create a Middleware for Error Handling**
```javascript
// middleware/errorHandler.js
const { ApiError } = require('../lib/errors');

const errorHandler = (err, req, res, next) => {
  console.error(err.stack); // Log the full error (but don’t expose it!)

  // Default to 500 if no status code is set
  const statusCode = err.statusCode || 500;
  const errorCode = err.name;
  const message = err.message || 'Internal Server Error';

  res.status(statusCode).json({
    success: false,
    error: {
      code: errorCode,
      message,
      details: err.details,
      requestId: req.id // Assuming we set req.id earlier
    }
  });
};

module.exports = errorHandler;
```

#### **Step 3: Use It in Routes**
```javascript
// routes/users.js
const express = require('express');
const { ValidationError, NotFoundError } = require('../lib/errors');
const router = express.Router();

router.post('/', async (req, res, next) => {
  try {
    const { email } = req.body;

    if (!email) {
      throw new ValidationError(400, 'Email is required');
    }

    if (!validateEmail(email)) {
      throw new ValidationError(
        400,
        'Invalid email',
        { expected: 'user@example.com' }
      );
    }

    // ... rest of the logic
    res.status(201).json({ success: true, data: user });

  } catch (err) {
    next(err); // Pass to error handler
  }
});

module.exports = router;
```

#### **Step 4: Add Request IDs for Debugging**
```javascript
// middleware/requestId.js
const { v4: uuidv4 } = require('uuid');

const requestIdMiddleware = (req, res, next) => {
  req.id = uuidv4(); // Attach a unique ID to each request
  next();
};

module.exports = requestIdMiddleware;
```

**Apply middleware in `app.js`:**
```javascript
app.use(requestIdMiddleware);
app.use(errorHandler);
```

---

### **GraphQL Error Handling (Apollo Server)**

GraphQL errors are structured differently but should follow similar principles.

#### **Step 1: Define Error Format**
```graphql
type Query {
  getUser(id: ID!): User @error(
    message: "User not found"
    code: "USER_NOT_FOUND"
  )
}
```

#### **Step 2: Custom Error Handling in Resolvers**
```javascript
// resolvers/query.js
const { AuthenticationError } = require('apollo-server');

const resolvers = {
  Query: {
    getUser: async (_, { id }, { dataSources }) => {
      const user = await dataSources.users.get(id);

      if (!user) {
        throw new AuthenticationError(
          "User not found (code: USER_NOT_FOUND)",
          {
            extensions: {
              code: 'USER_NOT_FOUND',
              requestId: req.id
            }
          }
        );
      }
      return user;
    }
  }
};
```

#### **Step 3: Global Error Handling**
```javascript
// server.js
const { ApolloServer } = require('apollo-server');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  formatError: (err) => {
    // Don’t expose stack traces in production
    if (process.env.NODE_ENV === 'production') {
      delete err.extensions.stacktrace;
    }
    return err;
  }
});
```

---

## **2. HTTP Status Codes: When to Use What**

| Status Code | Use Case |
|-------------|----------|
| **200 OK** | Success (but include data in body) |
| **201 Created** | Resource successfully created |
| **400 Bad Request** | Client-side validation failure |
| **401 Unauthorized** | Authentication failed |
| **403 Forbidden** | Auth succeeded but no permission |
| **404 Not Found** | Resource doesn’t exist |
| **409 Conflict** | Request conflicts (e.g., duplicate entry) |
| **500 Internal Server Error** | Server-side failure (never expose details) |

**Bad Example:**
```javascript
// ❌ Wrong: Always 200
app.get('/api/users/:id', (req, res) => {
  if (!user) return res.status(200).json({ error: "Not found" });
  res.status(200).json(user);
});
```

**Good Example:**
```javascript
// ✅ Correct: Use proper status codes
app.get('/api/users/:id', (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) throw new NotFoundError("User not found");
    res.status(200).json(user);
  } catch (err) {
    next(err);
  }
});
```

---

## **3. Handling Async Errors (WebSockets, gRPC, Stream APIs)**

### **WebSockets (Socket.IO)**
```javascript
// sockets.js
socket.on('process-data', async (data, callback) => {
  try {
    const result = await processData(data);

    socket.emit('result', {
      success: true,
      data: result
    });

  } catch (err) {
    socket.emit('error', {
      success: false,
      error: {
        code: err.code,
        message: err.message,
        requestId: req.id
      }
    });
  }
});
```

### **gRPC (Go Example)**
```go
// server.go
func (s *UserServiceServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
  user, err := s.store.GetUser(req.Id)
  if err != nil {
    if errors.Is(err, sql.ErrNoRows) {
      return nil, status.Errorf(codes.NotFound, "user not found")
    }
    return nil, status.Errorf(codes.Internal, "internal server error")
  }
  return &pb.GetUserResponse{User: user}, nil
}
```

---

## **4. Security: Never Expose Sensitive Data**

**Bad Example (Production!):**
```json
{
  "error": "SQL syntax error",
  "stack": "Error: Column 'name' does not exist..."
}
```

**Good Example (Sanitized):**
```json
{
  "error": {
    "code": "INVALID_SCHEMA",
    "message": "Invalid database column. Contact support."
  }
}
```

**How to Sanitize in Node.js:**
```javascript
// middleware/sanitizeErrors.js
const sanitizeError = (err) => {
  const sanitized = { ...err };
  delete sanitized.stack;
  if (process.env.NODE_ENV === 'production') {
    delete sanitized.details;
  }
  return sanitized;
};
```

---

## **Implementation Guide: Step-by-Step Checklist**

1. **Define a Custom Error Class** (e.g., `ApiError`, `ValidationError`).
2. **Create a Structured Error Response Format** (consistent across all endpoints).
3. **Add Request/Trace IDs** (for debugging correlation).
4. **Use Proper HTTP Status Codes** (no `200` for errors).
5. **Implement Global Error Handling Middleware** (catch all unhandled errors).
6. **Sanitize Errors in Production** (hide stack traces, sensitive details).
7. **Test Edge Cases** (invalid inputs, missing fields, auth failures).
8. **Document Error Formats** (Swagger/OpenAPI should describe error responses).

---

## **Common Mistakes to Avoid**

❌ **Using `200 OK` for errors** → Clients expect proper HTTP statuses.
❌ **Exposing stack traces in production** → Security risk!
❌ **Inconsistent error formats** → Confuses clients.
❌ **No traceability (no request IDs)** → Hard to debug.
❌ **Catching all errors silently** → Some errors (like OOM) should crash the server.
❌ **Ignoring validation errors** → Clients need actionable guidance.
❌ **Not testing error paths** → Always test failure cases!

---

## **Key Takeaways**

✅ **Consistency is key** – Use the same error format across all endpoints.
✅ **HTTP status codes matter** – `400` ≠ `500` ≠ `200`.
✅ **Actionable messages > vague errors** – Tell users **how** to fix the issue.
✅ **Add correlation IDs** – Debugging is easier with trace IDs.
✅ **Never expose sensitive data** – Sanitize in production.
✅ **Test errors thoroughly** – Validation, auth, DB failures.
✅ **Support different API styles** – REST, GraphQL, gRPC, WebSockets each have nuances.

---

## **Conclusion: Build APIs Developers Will Love**

Good error handling is **not an afterthought**—it’s a core part of API design. When done right:
✔ **Developers spend less time debugging.**
✔ **Users get helpful feedback.**
✔ **Security risks are minimized.**
✔ **Logs are more actionable.**

Start with **structured error responses**, **proper HTTP status codes**, and **consistent formats**. Then refine with **trace IDs**, **security hardening**, and **comprehensive testing**.

Now go build better APIs—one well-handled error at a time! 🚀

---
### **Further Reading**
- [REST API Design Best Practices (Kinsta)](https://kinsta.com/blog/rest-api-best-practices/)
- [GraphQL Error Handling (Apollo Docs)](https://www.apollographql.com/docs/apollo-server/errors/)
- [gRPC Error Handling Guide](https://grpc.io/docs/guides/error/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) (Error handling section)

---
**What’s your biggest API error-handling pain point?** Share in the comments—I’d love to hear your battle stories! 🔥
```

---
This post is **practical, code-heavy, and honest about tradeoffs** while covering all major API styles. It’s ready to publish on a tech blog, Medium, or Dev.to.