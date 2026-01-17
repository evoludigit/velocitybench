```markdown
# **Procedure Signature Validation: Ensuring Safe and Reliable Stored Procedure Calls**

*How to catch and prevent runtime errors before they reach your application*

---

## **Introduction**

When building backend systems, we often interact directly with databases using stored procedures (SPs). Stored procedures offer advantages like performance optimization, encapsulation, and security—but they come with risks. One of the most frustrating (and common) issues is **signature mismatches**: when a stored procedure is called with incorrect parameters or expected return types, causing runtime failures.

This isn’t just a minor inconvenience—it can lead to cascading errors, security vulnerabilities, and downtime. Developers might spend hours debugging calls that could have been prevented with a simple check. Enter the **Procedure Signature Validation (PSV) pattern**, a straightforward yet powerful approach to catch these issues early, whether during development or deployment.

In this guide, we’ll explore:
- Why signature mismatches happen and their impact
- How the PSV pattern works in practice
- Code examples in **SQL, Python, and TypeScript** (with TypeORM and Prisma)
- Common missteps and how to avoid them
- Tradeoffs and when to use (or skip) this pattern

By the end, you’ll have a reusable validation technique that can save you (and your team) countless debugging hours.

---

## **The Problem: Signature Mismatches in Stored Procedures**

Stored procedures are meant to encapsulate database logic, but their behavior depends entirely on **two things**:
1. **The signature** (parameter names, types, count, and order)
2. **The return type** (if applicable)

A mismatch can happen in several ways:

### **1. Parameter Count Mismatch**
```sql
-- Procedure expects 2 params, but we send 3
CALL UpdateUser('123', 'admin') -- Missing 'email' param
```
**Result:** A runtime error (e.g., in PostgreSQL, you’d get an "argument count mismatch" error).

### **2. Incorrect Parameter Types**
```sql
-- Procedure expects 'boolean', but we send a string
CALL ActivateUser('yes') -- 'yes' is not a boolean
```
**Result:** Silent failures or database errors.

### **3. Outdated Procedure Signatures**
```sql
-- Procedure was modified to add a new optional param, but the client isn't updated
CALL CreateOrder('100') -- Now expects '100' and a 'customer_id'
```
**Result:** Half-initialized records or application crashes.

### **4. Return Type Ambiguity**
```sql
-- Procedure returns a tuple, but the app expects a single value
SELECT * FROM CallProcedure() -- Returns (user_id, status), but app expects only 'user_id'
```
**Result:** Unhandled data formats, causing app crashes.

### **Why This Is Dangerous**
- **Debugging Hell:** Errors only appear at runtime, making them harder to trace.
- **Security Risks:** Incorrect parameter handling can lead to SQL injection or data leaks.
- **Team Pain:** Developers spend time fixing "works on my machine" vs. "breaks in production" issues.
- **Deployment Nightmares:** Signature changes can break CI/CD pipelines if not validated.

---

## **The Solution: Procedure Signature Validation (PSV)**

The **Procedure Signature Validation** pattern ensures that stored procedures are called with the correct signatures by:

1. **Defining a contract** for each procedure (parameters + return type).
2. **Validating calls** against this contract before execution.
3. **Automating checks** in tests, debugging tools, or deployment pipelines.

This pattern doesn’t replace runtime validation—it complements it by catching issues **before** they reach the database.

---

## **Components of the PSV Pattern**

| Component          | Purpose                                                                 |
|--------------------|--------------------------------------------------------------------------|
| **Procedure Metadata** | A table/database layer that stores expected signatures (params, types, etc.). |
| **Validation Layer** | A service that checks calls against the metadata (e.g., in TypeORM hooks or middleware). |
| **Documentation**   | Clear docstrings or comments in the codebase explaining expected signatures. |
| **Test Coverage**   | Unit/integration tests that verify signature compliance.               |

---

## **Implementation Guide**

We’ll implement PSV in **three layers**:
1. **Database Layer:** Store procedure metadata.
2. **Application Layer:** Validate calls before execution.
3. **Testing Layer:** Ensure tests catch signature violations early.

---

### **1. Database Layer: Store Procedure Metadata**

First, create a table to track stored procedures’ expected signatures:

```sql
-- PostgreSQL example
CREATE TABLE procedure_signatures (
    procedure_name VARCHAR(128) PRIMARY KEY,
    database_schema VARCHAR(64),  -- e.g., 'public'
    parameter_count SMALLINT,
    parameters JSONB NOT NULL,    -- JSON array of {name: str, type: str, is_optional: bool}
    return_type VARCHAR(64),      -- e.g., 'int', 'jsonb', '(user_id int, status text)'
    last_updated TIMESTAMP DEFAULT NOW()
);
```

**Example Entry:**
```sql
-- For `CreateUser(user_name VARCHAR, email VARCHAR, age INT OPTIONAL)`
INSERT INTO procedure_signatures
    (procedure_name, database_schema, parameter_count, parameters, return_type)
VALUES (
    'CreateUser',
    'public',
    3,
    '[{"name": "user_name", "type": "VARCHAR", "is_optional": false},
      {"name": "email", "type": "VARCHAR", "is_optional": false},
      {"name": "age", "type": "INT", "is_optional": true}]',
    'INT'  -- Returns the new user's ID
);
```

---

### **2. Application Layer: Validate Calls Before Execution**

#### **Option A: TypeORM (Node.js/Python)**
TypeORM supports dynamic queries and hooks. We’ll create a **beforeInsert/beforeUpdate validator**:

```typescript
// src/data-source.ts
import { DataSource } from 'typeorm';
import { validateProcedureSignature } from './signature-validator';

const AppDataSource = new DataSource({
    type: 'postgres',
    host: 'localhost',
    port: 5432,
    database: 'mydb',
    entities: [...],
    migrations: [...],
    subscriptions: [...],
});

AppDataSource.initialize().then(() => {
    // Hook into procedure calls
    AppDataSource.queryRunner.onQueryEvent = (event) => {
        const query = event.query;
        if (query.text.startsWith('CALL')) {
            validateProcedureSignature(query.text)
                .then(() => console.log('Signature valid.'))
                .catch(err => console.error('Signature mismatch:', err));
        }
    };
});
```

**Validator Logic:**
```typescript
// src/signature-validator.ts
import { readProcedureSignature } from './metadata-fetcher';

export async function validateProcedureSignature(procedureCall: string) {
    // Example: CALL public.CreateUser('Alice', 'alice@example.com', 30)
    const match = procedureCall.match(/CALL (\w+)\.(\w+)\((.*)\)/);
    if (!match) throw new Error('Not a procedure call.');

    const [, schema, procedureName, paramsStr] = match;

    // 1. Fetch expected signature
    const signature = await readProcedureSignature(procedureName, schema);
    if (!signature) throw new Error(`Procedure ${procedureName} not found.`);

    // 2. Parse provided params
    const providedParams = paramsStr.split(',').map(p => p.trim());

    // 3. Validate count
    if (providedParams.length !== signature.parameter_count) {
        throw new Error(
            `Expected ${signature.parameter_count} params, got ${providedParams.length}.`
        );
    }

    // 4. Validate types (simplified—use a type parser in production)
    const typeRegex = /(\w+)(?:\((.*)\))?/;
    signature.parameters.forEach((param, i) => {
        const paramType = typeRegex.exec(param.type)!;
        const providedValue = providedParams[i].trim();

        // Basic check (e.g., no 'yes' for boolean)
        if (paramType[1] === 'BOOLEAN' && providedValue !== 'true' && providedValue !== 'false') {
            throw new Error(`Param ${param.name} must be boolean.`);
        }
    });
}
```

#### **Option B: Prisma (TypeScript)**
Prisma’s `$queryRaw` allows dynamic SQL execution. Add validation before calls:

```typescript
import { PrismaClient } from '@prisma/client';
import { validateProcedureSignature } from './signature-validator';

const prisma = new PrismaClient();

export async function safeCallProcedure(procedure: string, ...args: any[]) {
    const query = `CALL ${procedure}(${args.map(arg => `'${arg}'`).join(', ')})`;
    await validateProcedureSignature(query);
    return await prisma.$queryRaw(query);
}

// Usage:
safeCallProcedure('CreateUser', 'Alice', 'alice@example.com', 30)
    .then(result => console.log('Success:', result))
    .catch(console.error);
```

---

### **3. Testing Layer: Catch Violations Early**

Add a **pre-commit hook** or **unit test** to validate procedures:

```typescript
// tests/signature-validation.test.ts
import { validateProcedureSignature } from '../src/signature-validator';

describe('Procedure Signature Validation', () => {
    it('should reject mismatched parameter counts', async () => {
        await expect(
            validateProcedureSignature('CALL CreateUser(\'Alice\')')
        ).rejects.toThrow('Expected 3 params');
    });

    it('should reject boolean params', async () => {
        await expect(
            validateProcedureSignature('CALL ActivateUser(\'yes\')')
        ).rejects.toThrow('must be boolean');
    });
});
```

---

## **Common Mistakes to Avoid**

### **1. Overlooking Optional Parameters**
**Bad:**
```sql
-- Procedure: CREATE_USER(name VARCHAR, email VARCHAR, age INT OPTIONAL)
CALL CREATE_USER('Bob') -- Missing email!
```
**Fix:** Use `IS NULL` checks or default values:
```sql
CREATE PROCEDURE CREATE_USER(
    p_name VARCHAR,
    p_email VARCHAR,
    p_age INT DEFAULT NULL
)
```

### **2. Ignoring Return Type Validation**
**Bad:**
```typescript
const result = await prisma.$executeRaw(
    'CALL GetUser(1)'
);
// Assumes result is always { id: number, name: string }
```
**Fix:** Parse return types explicitly:
```typescript
const user = await prisma.$executeRaw<{ id: number; name: string }>(
    'CALL GetUser(1)'
);
```

### **3. Not Updating Metadata When Procedures Change**
**Bad:** Forgetting to run migrations when a procedure is altered.
**Fix:** Automate metadata updates with schema migrations:
```typescript
// Example: Update metadata after altering a procedure
await prisma.$executeRaw`
    UPDATE procedure_signatures
    SET parameters = '[{"name": "name", "type": "VARCHAR", "is_optional": false}]'
    WHERE procedure_name = 'UpdateUser'
`;
```

### **4. Trusting "Works Locally" Without Validation**
**Bad:** Deploying code that passes locally but fails in production due to unchecked signatures.
**Fix:** Run validation in CI/CD pipelines:
```yaml
# GitHub Actions example
- name: Validate procedure signatures
  run: npm run test:signature-validation
```

### **5. Overcomplicating Validation**
**Bad:** Writing complex regex for type checking.
**Fix:** Use libraries like `pg-format` for SQL parsing or type-safe query builders.

---

## **Key Takeaways**

✅ **Catch signature mismatches early** with automatic validation.
✅ **Document procedures clearly** to avoid "works on my machine" issues.
✅ **Use metadata tables** to store expected signatures for reuse.
✅ **Test procedures rigorously** to ensure CI/CD safety.
✅ **Balance automation with simplicity**—don’t over-engineer validation.

❌ **Don’t rely solely on runtime checks** (they’re too late).
❌ **Ignore optional parameters**—they can break calls silently.
❌ **Skip return type validation**—unhandled data formats cause crashes.

---

## **Conclusion**

The **Procedure Signature Validation** pattern is a small but mighty tool in your backend toolkit. By validating calls against a contract before they reach the database, you:
- **Reduce debugging time** by catching errors early.
- **Improve security** by preventing malicious or incorrect invocations.
- **Enhance team collaboration** by making signatures explicit.

While no pattern is perfect, PSV provides a strong defense against one of the most frustrating kinds of runtime errors. Implement it in your next project, and you’ll thank yourself (and your future self) when signature mismatches become a thing of the past.

---
**Next Steps:**
1. Try implementing PSV in your current project.
2. Share your experience—what worked (or didn’t)?
3. Explore combining PSV with **API versioning** for even stronger contract enforcement.

Happy coding!
```