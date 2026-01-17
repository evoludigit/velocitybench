# **Debugging the Mutation Response Contract Pattern: A Troubleshooting Guide**

## **Introduction**
The **Mutation Response Contract** pattern ensures that stored procedures, APIs, or backend services return structured, schema-compliant responses. This pattern helps maintain consistency, improves debugging, and enables reliable frontend-backend communication. When this pattern fails, it often manifests as **response parsing errors, missing fields, or type mismatches**, breaking application logic.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the problem using this checklist:

| **Symptom**                     | **Possible Causes**                                  | **Frontend Impact**                     |
|---------------------------------|-----------------------------------------------------|-----------------------------------------|
| `Response data is empty or null` | Stored procedure returns `NULL`, `DEFAULT`, or no data | Missing data in UI, unexpected state    |
| `Field is missing from response` | Schema mismatch, optional field not included         | NPEs (NullPointerException), crashes      |
| `Type mismatch (e.g., string → int)` | Database return type differs from expected schema   | Type errors, incorrect UI rendering      |
| `Unexpected nested structure`   | Schema changed but frontend still expects old format | Parsing errors, broken component logic  |
| `Error codes not handled`       | Stored procedure returns error codes, but frontend ignores them | Poor error messaging, UX issues         |
| **At least 3 symptoms?** → Likely a **schema contract violation**. |

---

## **2. Common Issues & Fixes**

### **Issue 1: Response Parsing Fails (NPE, JSON Parsing Errors)**
**Symptoms:**
- `JSON.parseError` in frontend
- `NullPointerException` when accessing response fields

**Root Causes:**
- Stored procedure returns `NULL` for required fields.
- Frontend schema assumes a structure that doesn’t match the backend.

**Debugging Steps:**

#### **Backend Fix (Stored Procedure/Service)**
```sql
-- Example: Ensure all required fields are explicitly returned
CREATE PROCEDURE get_user(@user_id INT)
AS
BEGIN
    -- Instead of SELECT *, explicitly list columns
    SELECT
        user_id,
        username VARCHAR(50) NOT NULL, -- Ensure NOT NULL if required
        email VARCHAR(255) DEFAULT NULL,
        created_at DATETIME DEFAULT GETDATE()
    FROM users
    WHERE user_id = @user_id;
END
```
**Key Fix:**
- **Never use `SELECT *`**—always define the exact schema.
- **Set `DEFAULT` values** for optional fields to avoid `NULL`.

#### **Frontend Fix (TypeScript/JavaScript)**
```typescript
// Define a strict interface matching the backend
interface UserResponse {
  userId: number;      // Exact type, not dynamic
  username: string;    // Required
  email?: string;      // Optional (with ?)
  createdAt: Date;     // Ensures type safety
}

// Parse response with validation
const response = await api.getUser(userId);
if (!response) throw new Error("No response received");
const user: UserResponse = {
  userId: response.userId,
  username: response.username || "Anonymous", // Fallback
  email: response.email?.trim() || undefined, // Safe handling
  createdAt: new Date(response.createdAt),
};
```

---

### **Issue 2: Missing Required Fields**
**Symptoms:**
- `field is undefined` in JavaScript/TypeScript
- Database record exists, but frontend receives partial data

**Root Causes:**
- Frontend schema expects a field that the **stored procedure omits**.
- Backend returns `NULL` for optional fields, but frontend treats them as required.

**Debugging Steps:**

#### **Backend Check (SQL/Stored Proc)**
```sql
-- Verify returned columns
EXEC get_user(1);

-- Expected output should match your frontend interface
-- If missing, update the SP:
ALTER PROCEDURE get_user(@user_id INT)
AS
BEGIN
    SELECT
        user_id,
        username,  -- Must include even if optional
        email,
        status    -- Was missing in original query
    FROM users
    WHERE user_id = @user_id;
END
```

#### **Frontend Validation**
```typescript
// Add runtime validation
const validateUserResponse = (data: any): UserResponse => {
  if (!data?.userId || !data.username) {
    throw new Error("Invalid response: missing required fields");
  }
  return {
    userId: data.userId,
    username: data.username,
    email: data.email || undefined,
    createdAt: new Date(data.createdAt),
  };
};

// Usage
const user = validateUserResponse(response);
```

---

### **Issue 3: Type Mismatches (e.g., `string` vs `int`)**
**Symptoms:**
- `Cannot convert string to number` in frontend
- Database returns `VARCHAR` but frontend expects `INT`

**Root Causes:**
- Database column type differs from frontend assumption.
- Stored procedure returns `NULL` or `0` for numeric fields.

**Debugging Steps:**

#### **Backend Fix (Type Consistency)**
```sql
-- Ensure backend returns correct types
ALTER TABLE users
ALTER COLUMN status INT NOT NULL DEFAULT 1; -- Was VARCHAR?

-- Update stored procedure
ALTER PROCEDURE get_user(@user_id INT)
AS
BEGIN
    SELECT
        user_id INT,
        username VARCHAR(50),
        status INT  -- Explicitly typed
    FROM users
    WHERE user_id = @user_id;
END
```

#### **Frontend Type Handling**
```typescript
// Convert dynamic responses to expected types
const parseUserData = (raw: any): UserResponse => ({
  userId: Number(raw.userId),  // Force number
  username: String(raw.username), // Force string
  status: raw.status ? Number(raw.status) : 0, // Default
});

// Usage
const user = parseUserData(response);
```

---

### **Issue 4: Unexpected Nested Structures**
**Symptoms:**
- `TypeError: Cannot read property 'nested' of undefined`
- Backend schema changed, but frontend still expects old format.

**Root Causes:**
- API evolution without frontend updates.
- Stored procedure now returns `NULL` where it once returned an object.

**Debugging Steps:**

#### **Backend Audit (Check SQL Output)**
```sql
-- Run stored procedure with EXPLAIN (SQL Server)
EXEC sp_help @procname = 'get_user';
-- Check if 'address' was once returned but now dropped
```

#### **Frontend Fallback Handling**
```typescript
interface UserResponse {
  userId: number;
  username: string;
  address?: {  // Now optional
    street?: string;
    city?: string;
  };
}

const user: UserResponse = {
  ...response,
  address: response.address ? {
    street: response.address.street,
    city: response.address.city,
  } : undefined,
};
```

---

## **3. Debugging Tools & Techniques**

### **A. Backend Debugging**
1. **Log Raw SQL Output**
   - Use `PRINT` in SQL Server or `SELECT` a test row:
     ```sql
     PRINT 'Testing user 1:';
     SELECT * FROM users WHERE user_id = 1;
     ```
   - Compare with expected schema.

2. **Use a SQL Debugger (DBeaver, SSMS, pgAdmin)**
   - Execute stored procedures manually to see real outputs.

3. **Enable Query Profiler**
   - Capture actual queries executed (e.g., SQL Server Profiler).

4. **Mock Stored Procedures**
   ```sql
   -- Replace real SP with a test version
   CREATE PROCEDURE get_user_mock()
   AS
   BEGIN
       SELECT * FROM (VALUES
           (1, 'TestUser', 'test@example.com', '2023-01-01', 1)
       ) AS t(user_id, username, email, created_at, status);
   END
   ```

---

### **B. Frontend Debugging**
1. **Log Raw API Responses**
   ```javascript
   const response = await fetch('/api/user/1');
   console.log('Raw response:', await response.json());
   ```
   - Compare with defined schema.

2. **Use TypeScript’s `NonNullable` and `unknown`**
   ```typescript
   const data: unknown = await fetchData();
   if (typeof data !== 'object' || data === null) throw new Error("Invalid");
   const parsed: UserResponse = data as UserResponse;
   ```

3. **Unit Test Schema Parsing**
   ```typescript
   // Mock tests for different response formats
   test("handles missing email", () => {
     const invalid = { userId: 1, username: "John" };
     expect(() => validateUserResponse(invalid)).toThrow();
   });
   ```

4. **Postman/Insomnia for API Testing**
   - Manually call the API to inspect responses.

---

## **4. Prevention Strategies**

### **A. Schema Management**
1. **Document the Mutation Response Contract**
   - Store schema in a `README.md` or Confluence wiki.
   - Example:
     ```markdown
     ## User Response Schema
     ```json
     {
       "userId": "integer",
       "username": "string (required)",
       "email": "string (optional)",
       "status": "integer (1=active, 0=inactive)"
     }
     ```

2. **Use OpenAPI/Swagger for APIs**
   - Define contracts in `openapi.yaml` for machine-readable schemas.

3. **Versioned APIs**
   - Use URL paths like `/v1/users` to isolate breaking changes.

### **B. Automated Validation**
1. **Backend: Input Validation**
   ```csharp
   // C# example with FluentValidation
   public class GetUserRequestValidator : AbstractValidator<GetUserRequest>
   {
       public GetUserRequestValidator()
       {
           RuleFor(x => x.UserId).GreaterThan(0);
       }
   }
   ```

2. **Frontend: Runtime Checks**
   ```typescript
   const isValidUser = (data: any): boolean =>
     data &&
     typeof data.userId === 'number' &&
     typeof data.username === 'string';
   ```

3. **CI/CD Pipeline Checks**
   - Run schema validation in tests before deployment.

### **C. Backward Compatibility**
1. **Deprecation Strategy**
   - Add `deprecated` flags before removing fields:
     ```sql
     SELECT user_id, username, email, status, address AS legacy_address
     FROM users;
     ```

2. **Graceful Fallbacks**
   - Provide defaults in stored procedures:
     ```sql
     SELECT
         user_id,
         ISNULL(email, 'guest@example.com') AS email
     FROM users;
     ```

3. **Logging Schema Breaks**
   - Log when responses deviate from the contract:
     ```java
     if (!response.matchesSchema()) {
         logger.warn("Schema mismatch for user_id {}: {}", userId, response);
     }
     ```

---

## **5. Summary Checklist for Quick Resolution**
| **Step** | **Action** |
|----------|------------|
| 1 | **Log raw response** (frontend & backend) |
| 2 | **Compare with schema** (is `NULL` expected?) |
| 3 | **Check stored procedure output** (does it match?) |
| 4 | **Test with mocked data** (simulate different cases) |
| 5 | **Update frontend schema** (if backend changed) |
| 6 | **Add validation** (runtime checks) |
| 7 | **Document changes** (update contract docs) |

---

## **Final Notes**
- **Start with the frontend error** (it’s the visible symptom).
- **Verify the backend response** (is it `NULL`, `undefined`, or malformed?).
- **Update schemas incrementally**—never break contracts without deprecation.
- **Automate validation** to catch issues early.

By following this guide, you can **quickly identify and fix Mutation Response Contract issues** while preventing future regressions.