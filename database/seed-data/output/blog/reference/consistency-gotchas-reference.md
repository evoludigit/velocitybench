# **[Pattern] Reference Guide: Consistency Gotchas**

## **Overview**
**Consistency Gotchas** refers to unintended behavioral inconsistencies in patterns, APIs, or systems that mislead users, break expectations, or cause logical errors. These arise from subtle differences in syntax, semantics, error handling, edge cases, or implicit behaviors across similar operations. Addressing consistency gotchas improves developer experience, reduces debugging time, and maintains predictable system behavior. This guide outlines common sources of inconsistency, how to identify them, and best practices for resolution.

---

## **Key Concepts & Implementation Details**
| Concept               | Definition                                                                                                                                                                                                 | Impact                                                                                                                                                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Semantic Inconsistency** | Operations with similar naming but differing behaviors (e.g., `update()` vs `apply()`).                                                                                                                           | Leads to logical errors, confusion, and inefficient code.                                                                                                                                                                 |
| **Edge-Case Inconsistency** | Different handling of boundary conditions (e.g., empty inputs, nulls) across methods or APIs.                                                                                                                       | Unexpected crashes or incorrect outputs in edge scenarios.                                                                                                                                                               |
| **Error Handling Differences** | Varying error messages, codes, or recovery mechanisms for identical failures.                                                                                                                                       | Debugging difficulty and inconsistent system states.                                                                                                                                                                       |
| **Order-Dependent Behavior** | Outcomes that change based on the sequence of operations (e.g., race conditions, transactional dependencies).                                                                                                         | Unpredictable system states and race-related bugs.                                                                                                                                                                       |
| **Implicit vs. Explicit**    | Inconsistent reliance on default values, hidden assumptions, or implicit side effects.                                                                                                                               | Silent failures or performance surprises.                                                                                                                                                                                 |
| **Language-Specific Quirks** | Differences in behavior between languages (e.g., Python’s `None` vs Java’s `null`).                                                                                                                               | Cross-language integration issues.                                                                                                                                                                                   |

---

## **Schema Reference**
Below are common patterns where inconsistencies often occur, along with their pitfalls:

| **Pattern**               | **Inconsistency Source**                     | **Example**                                                                                                                                                                                                                     | **Mitigation Strategy**                                                                                                                                                                                                                   |
|---------------------------|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **CRUD Operations**       | Different return types (e.g., `create()` returns ID, `update()` returns `true`).                                                                                                                                         | `user.create()` → `{ id: 123 }`, but `user.update(id, {})` → `true`.                                                                                                                                                                       | Standardize return types (e.g., always return resource data).                                                                                                                                                                   |
| **Error Handling**        | API errors use HTTP 400 for bad requests but 500 for timeouts.                                                                                                                                                           | `/payments/status` → `400 Bad Request` vs `/reports` → `500 Internal Error` for identical failures.                                                                                                                                   | Use consistent HTTP status codes (e.g., `429 Too Many Requests` for timeouts).                                                                                                                                                                |
| **Input Validation**      | Some APIs fail on `null`, others on empty strings.                                                                                                                                                                     | `validateEmail(null)` → `Invalid null`, but `validateEmail("")` → `Must provide email`.                                                                                                                                                   | Define explicit rules (e.g., treat `null` and `""` equivalently).                                                                                                                                                                    |
| **Pagination**            | `page=1` returns 10 items; `page=2` returns 5 items.                                                                                                                                                                       | Inconsistent response sizes break client-side logic.                                                                                                                                                                                 | Enforce fixed sizes or document variability.                                                                                                                                                                                     |
| **Transactions**          | `save()` commits on success but `commit()` may retry indefinitely.                                                                                                                                                       | `db.save(user)` → immediate commit; `db.commit()` → retries on failure.                                                                                                                                                                     | Document retry policies explicitly.                                                                                                                                                                                          |
| **Async Behavior**        | `async.getUser()` resolves with `null` if not found vs `async.fetchUser()` raises an error.                                                                                                                           | Inconsistent handling of missing data.                                                                                                                                                                                       | Standardize error propagation (e.g., always reject with `404`).                                                                                                                                                                  |
| **Side Effects**          | `deleteUser()` removes data but logs a warning; `hardDeleteUser()` does not.                                                                                                                                             | Unexpected logging in non-critical operations.                                                                                                                                                                                 | Document all side effects (e.g., via `@deprecated` or `@side-effect`).                                                                                                                                                               |

---

## **Query Examples**
### **1. Detecting CRUD Inconsistencies**
**Scenario**: A REST API where `POST /users` returns `{ id: 1 }`, but `PUT /users/1` returns `true`.

```http
# Inconsistent return types
POST /users → { "id": 123, "name": "Alice" }
PUT /users/1 → { "success": true }
```
**Fix**: Standardize to return resource data:
```http
PUT /users/1 → { "id": 1, "name": "Alice" }
```

---
### **2. Edge-Case Validation**
**Scenario**: Two endpoints treat empty strings differently:
```javascript
// API 1: Empty string is invalid
validateEmail("") → throws "Email cannot be empty";

// API 2: Empty string is allowed but marked as pending
submitForm({ email: "" }) → { status: "pending" };
```
**Fix**: Align validation rules:
```javascript
// Consistent: Empty strings are rejected
validateEmail("") → throws "Email is required";
```

---
### **3. Error Handling Consistency**
**Scenario**: A microservice returns:
```http
# Timeout handled as 500
GET /slow-operation → 500 Internal Error

# Bad request handled as 400
GET /slow-operation?invalid_param=true → 400 Bad Request
```
**Fix**: Classify timeouts as `429 Too Many Requests`:
```http
GET /slow-operation → 429 Retry-After: 30
```

---
### **4. Async Behavior**
**Scenario**: Two async methods handle missing data differently:
```javascript
// Resolves to null
async.findUser("nonexistent") → Promise.resolve(null);

// Rejects with error
async.fetchUser("nonexistent") → Promise.reject("User not found");
```
**Fix**: Standardize to reject for missing data:
```javascript
async.fetchUser("nonexistent") → Promise.reject({ status: 404 });
```

---

## **Related Patterns**
To mitigate **Consistency Gotchas**, leverage these complementary patterns:

| **Pattern**               | **Description**                                                                                                                                                                                                                     | **How It Helps**                                                                                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Schema Validation**     | Define strict input/output schemas (e.g., JSON Schema, OpenAPI).                                                                                                                                                                 | Enforces consistency by validating all operations against a shared contract.                                                                                                                                                       |
| **Documentation As Code** | Embed spec files in code (e.g., Swagger/OpenAPI) and auto-generate docs.                                                                                                                                                       | Reduces ambiguity by providing real-time references.                                                                                                                                                                         |
| **Contract Testing**      | Automate tests to verify consistency across services.                                                                                                                                                                         | Catches inconsistencies early via property-based testing.                                                                                                                                                                     |
| **Idiomatic APIs**        | Follow language/framework conventions (e.g., Python’s `None` vs `null` handling).                                                                                                                                              | Reduces cognitive load for developers.                                                                                                                                                                                 |
| **Feature Flags**         | Gradually roll out changes with toggleable behavior.                                                                                                                                                                     | Isolates inconsistencies during transitions.                                                                                                                                                                                 |
| **Observability**         | Implement logging/metrics to track operation behavior.                                                                                                                                                                   | Detects inconsistencies in production via anomaly detection.                                                                                                                                                                   |
| **Backward Compatibility** | Design updates to maintain prior behavior (e.g., deprecation warnings).                                                                                                                                                     | Prevents breaking changes that introduce gotchas.                                                                                                                                                                           |

---

## **Anti-Patterns to Avoid**
1. **Ad-Hoc Error Codes**: Avoid custom error codes without documentation (e.g., `ERR_123`). Use standardized codes (e.g., `HTTP 4xx`).
2. **Silent Failures**: Never swallow errors without explicit user feedback.
3. **Unversioned APIs**: Version APIs (e.g., `/v1/users`) to isolate breaking changes.
4. **Overloading Methods**: Avoid single methods handling multiple unrelated cases (e.g., `process()` for create/update/delete).
5. **Inconsistent Logging**: Standardize log formats (e.g., `{ timestamp, level, message, context }`).

---
## **Tools & Libraries**
| Tool/Library          | Purpose                                                                                                                                                                                                                   | Example Use Case                                                                                                                                                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Postman/Newman**    | Automated API testing for consistency checks.                                                                                                                                                                   | Validate that `POST /users` and `PUT /users` return consistent fields.                                                                                                                                                              |
| **JSON Schema**       | Enforce input/output contracts.                                                                                                                                                                                   | Reject requests where `age` is missing or negative.                                                                                                                                                                         |
| **OpenAPI/Swagger**   | Document APIs with interactive examples.                                                                                                                                                                       | Show expected responses for `200 OK` vs `400 Bad Request`.                                                                                                                                                                     |
| **Pact**              | Contract testing between services.                                                                                                                                                                               | Ensure `Service A` and `Service B` handle `null` inputs identically.                                                                                                                                                                 |
| **Sentry**            | Centralized error tracking.                                                                                                                                                                                   | Group similar inconsistencies (e.g., `null` vs empty string errors).                                                                                                                                                               |
| **Grafana**           | Monitor API latency/errors for behavioral drifts.                                                                                                                                                                   | Detect when `GET /users` starts returning partial data.                                                                                                                                                                       |

---
## **Best Practices Checklist**
1. **Design Phase**:
   - [ ] Audit existing APIs for inconsistencies using schema validators.
   - [ ] Document edge cases (e.g., "Empty strings are rejected").
   - [ ] Choose error codes from standardized sets (e.g., HTTP statuses).

2. **Implementation Phase**:
   - [ ] Use consistent return types (e.g., always return resource data).
   - [ ] Log all operations with standardized formats.
   - [ ] Implement retry logic explicitly (avoid silent retries).

3. **Testing Phase**:
   - [ ] Add contract tests for cross-service consistency.
   - [ ] Test edge cases (e.g., nulls, empty inputs, race conditions).
   - [ ] Validate async behavior (e.g., promise resolutions/rejections).

4. **Deployment Phase**:
   - [ ] Use feature flags for gradual behavior changes.
   - [ ] Monitor for anomalies post-deploy (e.g., error spikes).
   - [ ] Communicate API breaking changes via changelogs.

---
## **Example Workflow: Fixing a Consistency Gotcha**
**Problem**: A frontend app fails when `GET /users` returns fewer items than expected due to inconsistent pagination:
```javascript
// Backend: Page 1 → 10 items; Page 2 → 5 items (inconsistent)
fetch('/users?page=1')
  .then(console.log); // 10 items
fetch('/users?page=2')
  .then(console.log); // 5 items (breaks UI)
```

**Steps to Resolve**:
1. **Identify**: Audit `/users` endpoint with Postman to confirm pagination inconsistency.
2. **Standardize**: Update backend to return fixed sizes (e.g., always 10 items, add `totalPages` header).
3. **Test**: Verify frontend pagination logic with new responses.
4. **Document**: Update OpenAPI spec to reflect `pagination.size=10`.
5. **Monitor**: Set up Grafana alerts for pagination-related errors.

**Result**:
```http
# Fixed: Consistent pagination
GET /users?page=1 → { users: [10], totalPages: 2 }
GET /users?page=2 → { users: [0], totalPages: 2 }
```