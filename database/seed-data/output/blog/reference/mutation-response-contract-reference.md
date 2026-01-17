# **[Pattern] Mutation Response Contract Reference Guide**

---

## **Overview**
The **Mutation Response Contract** pattern ensures that stored procedures return structured, predictable responses when executing mutations (write operations). This pattern enforces a standardized format for success, error, and metadata payloads, improving reliability, debugging, and client application integration.

Unlike REST APIs, which often return flexible JSON structures, this pattern defines a **strict schema** for mutation responses. By adhering to this contract, backend systems guarantee consistent behavior across all mutation invocations.

Key benefits include:
- **Predictable error handling** (consistent error codes and messages).
- **Simplified client parsing** (uniform response structure).
- **Better observability** (metadata like timestamps, request IDs).
- **Enhanced maintainability** (explicit success/error schemas).

---

## **Key Concepts & Implementation Details**

### **1. Core Schema Components**
All mutation responses must include:
| Component          | Description                                                                 | Example Value                     |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------|
| **`@type`**        | Denotes the response type (either `"success"` or `"error"`).                 | `"success"` or `"error"`           |
| **`data`**         | Mutation result (structured per operation).                               | `{ id: 123, name: "Updated Item" }` |
| **`error`**        | Error details (present only in `@type: "error"` responses).                | `{ code: "400", message: "Bad Request" }` |
| **`metadata`**     | Non-critical context (e.g., request ID, timestamp).                      | `{ requestId: "abc-123", timestamp: "2024-05-20T12:00:00Z" }` |

---

### **2. Response Formatting Rules**
- **Success Response:**
  ```json
  {
    "@type": "success",
    "data": { ... },  // Operation-specific payload
    "metadata": { ... }
  }
  ```
  Example for a `createUser` mutation:
  ```json
  {
    "@type": "success",
    "data": {
      "user": {
        "id": "user_456",
        "email": "test@example.com",
        "createdAt": "2024-05-20T12:00:00Z"
      }
    },
    "metadata": {
      "requestId": "req_789",
      "timestamp": "2024-05-20T12:00:00Z"
    }
  }
  ```

- **Error Response:**
  ```json
  {
    "@type": "error",
    "error": {
      "code": "string",   // HTTP-like error code (e.g., "400", "404").
      "message": "string",// Human-readable explanation.
      "details": { ... }  // Optional: Additional context (e.g., validation errors).
    },
    "metadata": { ... }
  }
  ```
  Example for a `deleteUser` failure:
  ```json
  {
    "@type": "error",
    "error": {
      "code": "403",
      "message": "User not found",
      "details": {
        "requiredField": ["email"]
      }
    },
    "metadata": {
      "requestId": "req_abc"
    }
  }
  ```

---

### **3. Schema Validation**
- **Mandatory Fields:**
  - `@type` (always present).
  - Either `data` (success) **or** `error` (error).
- **Conditional Fields:**
  - `metadata` is optional but recommended for observability.
- **Error Codes:**
  Use standardized codes (e.g., `400` for client errors, `500` for server errors).
  Extend with custom codes (e.g., `400-1` for "Invalid email format").

---

## **Schema Reference**
Below is the **GraphQL-like schema** defining the mutation response contract. Replace placeholders (`{Type}`) with actual types.

| Field          | Type               | Description                                                                 | Example                     |
|----------------|--------------------|-----------------------------------------------------------------------------|-----------------------------|
| **`@type`**    | `String!`          | Required. Must be `"success"` or `"error"`.                               | `"success"`                 |
| **`data`**     | `{...}` (union)    | Success payload. Shape varies by mutation.                                 | `{ user: { id: "123" } }`   |
| **`error`**    | `{...}` (error obj)| Error details (only if `@type: "error"`).                                  | `{ code: "404", message: "Not found" }` |
| **`metadata`** | `{...}`            | Optional. Includes `requestId`, `timestamp`, etc.                         | `{ requestId: "abc-123" }`  |

### **Error Object Schema**
| Field      | Type     | Description                          | Example          |
|------------|----------|--------------------------------------|------------------|
| `code`     | `String!`| Error code (e.g., "400").             | `"400"`          |
| `message`  | `String!`| Human-readable error description.    | `"Invalid input"`|
| `details`  | `{...}`  | Optional nested error context.       | `{ field: ["error"] }` |

---

## **Query Examples**

### **Example 1: Successful Mutation (`createUser`)**
**Input:**
```sql
CALL createUser(
  email = 'test@example.com',
  password = 'SecurePass123'
);
```
**Output:**
```json
{
  "@type": "success",
  "data": {
    "user": {
      "id": "user_456",
      "email": "test@example.com",
      "createdAt": "2024-05-20T12:00:00Z"
    }
  },
  "metadata": {
    "requestId": "req_789",
    "timestamp": "2024-05-20T12:00:00Z"
  }
}
```

---

### **Example 2: Failed Mutation (`updateUser`)**
**Input:**
```sql
CALL updateUser(
  userId = 'user_456',
  email = 'invalid-email'
);
```
**Output:**
```json
{
  "@type": "error",
  "error": {
    "code": "400",
    "message": "Invalid email format",
    "details": {
      "field": ["email"]
    }
  },
  "metadata": {
    "requestId": "req_abc"
  }
}
```

---

### **Example 3: Custom Mutation (`transferFunds`)**
**Input:**
```sql
CALL transferFunds(
  fromAccount = 'acc_123',
  toAccount = 'acc_456',
  amount = 100.00
);
```
**Output (Success):**
```json
{
  "@type": "success",
  "data": {
    "transaction": {
      "id": "txn_987",
      "amount": 100.00,
      "status": "completed"
    }
  },
  "metadata": {
    "requestId": "req_def",
    "timestamp": "2024-05-20T12:05:00Z"
  }
}
```

**Output (Error - Insufficient Funds):**
```json
{
  "@type": "error",
  "error": {
    "code": "400-1",  /* Custom code for "insufficient funds" */
    "message": "Transfer amount exceeds account balance",
    "details": {
      "account": "acc_123",
      "balance": 50.00
    }
  },
  "metadata": {
    "requestId": "req_ghi"
  }
}
```

---

## **Related Patterns**

### **1. [Input Validation Pattern](link)**
   - Ensures mutations receive valid data **before** execution.
   - Complements the response contract by preventing malformed inputs.
   - *Use Case:* Reject `createUser` if `email` is missing.

### **2. [Idempotency Keys](link)**
   - Prevents duplicate mutations (e.g., retries).
   - Clients provide a unique `idempotencyKey`; servers validate and deduplicate.
   - *Example:* `updateUser` with `idempotencyKey = "user_123-456"`.

### **3. [Event Sourcing](link)**
   - Logs mutations as immutable events (e.g., `UserCreated`).
   - Pair with this pattern to provide **audit trails** alongside responses.
   - *Use Case:* Track `createUser` via events while returning a structured response.

### **4. [Transactional Mutations](link)**
   - Ensures atomicity (all-or-nothing execution).
   - Example: `transferFunds` debits `fromAccount` **and** credits `toAccount` in a single transaction.
   - *Conflict:* If this pattern fails mid-execution, return a rollback error (e.g., `@type: "error"`, `code: "409"`).

### **5. [Rate Limiting](link)**
   - Throttles mutations per client (e.g., 100 requests/minute).
   - Return a `429 Too Many Requests` error if limits are exceeded.
   - *Example:*
     ```json
     {
       "@type": "error",
       "error": {
         "code": "429",
         "message": "Rate limit exceeded. Try again in 60 seconds."
       }
     }
     ```

---
## **Best Practices**
1. **Explicit Error Codes:**
   Use HTTP-like codes (e.g., `400`, `404`) with **custom extensions** (e.g., `400-1` for "duplicate email").
2. **Include Metadata:**
   Always add `requestId` and `timestamp` for debugging.
3. **Document Mutation Schemas:**
   Publish a **data dictionary** for `data.*` fields (e.g., `createUser.data.user` properties).
4. **Handle Edge Cases:**
   - Return `409 Conflict` for duplicate records.
   - Use `500 Internal Server Error` for unexpected failures.
5. **Client-Side Parsing:**
   Clients should expect **only** `{ "@type": "success" | "error" }` at the root.

---
## **Common Pitfalls**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|-------------------------------------------------------------------------|
| Missing `@type` field.            | Automatically append `@type` in all stored procedures.                 |
| Inconsistent `data` structure.    | Define a strict schema per mutation (e.g., GraphQL-like interfaces).    |
| Missing `metadata`.               | Add a default `metadata` block with `requestId` and `timestamp`.        |
| Overly broad error messages.      | Include `details` for actionable insights (e.g., missing validation rules). |

---
## **Tools & Libraries**
- **Validation:** Use [JSON Schema](https://json-schema.org/) to validate responses.
- **Logging:** Correlate `requestId` with backend logs (e.g., ELK stack).
- **Testing:** Mock responses for client-side integration tests (e.g., Postman, Jest).

---
**Last Updated:** `2024-05-20`
**Contact:** `engineering@yourcompany.com` for schema updates.