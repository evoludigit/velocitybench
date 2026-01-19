# **Debugging "WHERE Clause Compilation to SQL" Pattern: A Troubleshooting Guide**
*For Backend Engineers Handling GraphQL Filter Inputs*

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your system exhibits these symptoms:

### **Security & Injection Issues**
- [ ] Unexpected SQL errors (e.g., `syntax error at or near "..."`)
- [ ] Database queries returning excessive or nonsensical data
- [ ] Logs show raw user input being directly embedded in SQL
- [ ] Unexpected database locks or performance degradation under filter queries

### **Logic & Query Issues**
- [ ] Filters not working as expected (e.g., `WHERE age > 30` returns users younger than 30)
- [ ] Boolean logic fails (e.g., `AND` behaves like `OR`)
- [ ] Comparison operators (`>`, `<`, `LIKE`) don’t match GraphQL input
- [ ] Null checks (`IS NULL` vs. `=`) break expected behavior

### **Database-Specific Issues**
- [ ] Operators like `BETWEEN` or `IN` don’t compile correctly
- [ ] Case sensitivity issues in string comparisons (e.g., PostgreSQL vs. MySQL)
- [ ] Date/time parsing fails (e.g., ISO format vs. Unix timestamp)
- [ ] Aggregations (`COUNT`, `SUM`) misbehave with filters

---

## **2. Common Issues & Fixes**
### **Issue 1: SQL Injection Vulnerabilities**
**Symptoms:** Unexpected query behavior, crashes, or misuse of database privileges.
**Root Cause:** Direct string interpolation of untrusted GraphQL inputs.

#### **Fix: Parameterized Queries (Best Practice)**
**Before (Vulnerable):**
```javascript
// ❌ UNSAFE: Direct string insertion
const query = `SELECT * FROM users WHERE name = '${req.query.name}'`;
```

**After (Safe):**
```javascript
// ✅ SAFE: Parameterized query (using Knex.js example)
const query = knex('users').where('name', req.query.name);
```

**Advanced (Dynamic Build):**
```javascript
// ✅ Dynamic WHERE clause (with validation)
const whereConditions = [];
if (req.query.age) whereConditions.push('age = ?', req.query.age);
if (req.query.status) whereConditions.push('status = ?', req.query.status);

const query = knex('users').where(whereConditions);
```

**Key Tools:**
- **ORMs/Libraries:** Knex.js, Sequelize, TypeORM, Prisma
- **Database Drivers:** `pg`, `mssql`, `mysql2` (all support parameterized queries)

---

### **Issue 2: Incorrect Filter Logic**
**Symptoms:** `AND` acts as `OR` or `LIKE` behaves unpredictably.

#### **Fix: Map GraphQL Operators to SQL Correctly**
GraphQL often uses `eq`, `gt`, `contains`, etc., while SQL uses `=`, `>`, `LIKE`.

**Before (Incorrect):**
```javascript
// ❌ GraphQL input: { status: { contains: "active" } } → SQL: status LIKE "active"
```

**After (Correct):**
```javascript
// ✅ Handle "contains" as SQL LIKE
if (input.status?.contains) {
  where.push(`status ILIKE ?`, `%${input.status.contains}%`);
}
```

**Full Example (Knex.js):**
```javascript
function buildWhere(input) {
  const where = [];

  if (input.age) {
    where.push('age', input.age);
  }

  if (input.status) {
    if (input.status.contains) {
      where.push(`status ILIKE ?`, `%${input.status.contains}%`);
    } else {
      where.push('status', input.status);
    }
  }

  return where;
}

const query = knex('users').where(buildWhere(req.query));
```

**Edge Cases:**
- **Null Handling:** Use `IS NULL` vs. `= NULL` (e.g., `input.id ? 'id = ?' : 'id IS NULL'`).
- **Boolean Fields:** Convert `true/false` to `1/0` if the DB doesn’t support booleans.

---

### **Issue 3: Database-Specific Compilation Errors**
**Symptoms:** `UNEXPECTED_TOKEN` or `SYNTAX ERROR` in SQL logs.

#### **Common Culprits & Fixes**
| **Database**       | **Problem**                          | **Fix** |
|--------------------|--------------------------------------|---------|
| **PostgreSQL**     | `BETWEEN` with `NULL` values         | Use `IS BETWEEN` or exclude `NULL` inputs. |
| **MySQL**          | `LIKE` with `NULL`                   | Replace with `IS NULL` checks. |
| **SQLite**         | `DATE` functions (e.g., `DATE()`)     | Use `strftime()` or avoid raw dates. |
| **Oracle**         | `TO_DATE` parsing                   | Ensure date formats match DB conventions. |

**Example: Handling Dates Across Databases**
```javascript
// ✅ Cross-database date handling
if (input.createdAt) {
  // PostgreSQL/MySQL: `>=` with ISO string
  // SQLite: `strftime('%Y-%m-%d', created_at) >= ?`
  where.push('created_at', input.createdAt);
} else {
  // Default: no date filter
}
```

**Debugging Tip:**
- **Log Raw SQL:** Enable SQL logging in your ORM (e.g., `knex.debug(true)`).
- **Test in DB Client:** Manually run the generated SQL in your database to isolate issues.

---

### **Issue 4: Aggregations with Filters**
**Symptoms:** `COUNT` or `SUM` ignore filters, or return wrong results.

#### **Fix: Apply Filters Before Aggregation**
```javascript
// ❌ Wrong: Filters applied after aggregation (incorrect)
const count = await knex('users').where(where).count('id');

// ✅ Correct: Filter first, then aggregate
const filteredUsers = await knex('users').where(where);
const count = await filteredUsers.count('id');
```

**Alternative (Single Query):**
```javascript
// ✅ Single-query solution (better performance)
const count = await knex('users').where(where).count('id');
```

---

## **3. Debugging Tools & Techniques**
### **A. Logging & Validation**
1. **Enable SQL Logging:**
   - **Knex.js:** `knex.debug(true)`
   - **Sequelize:** `logging: console.log`
   - **Prisma:** `log: ['query']`

2. **Log Inputs vs. Outputs:**
   ```javascript
   console.log('Input:', req.query);
   console.log('Generated SQL:', query.toSQL());
   ```

3. **Validate GraphQL Inputs:**
   - Use **Zod** or **Joi** to schema-validate inputs before SQL compilation:
     ```javascript
     const userFilterSchema = z.object({
       id: z.number().optional(),
       name: z.string().min(2).optional(),
       age: z.number().int().positive().optional(),
     });
     const validatedInput = userFilterSchema.parse(req.query);
     ```

### **B. Unit Testing**
- **Mock Database Queries:** Use libraries like `sinon` or `jest.mock` to test SQL generation.
- **Example:**
  ```javascript
  test('builds correct WHERE clause for name contains', () => {
    const where = buildWhere({ name: { contains: 'John' } });
    expect(where).toEqual(['name ILIKE ?', '%John%']);
  });
  ```

### **C. Database-Specific Queries**
- **PostgreSQL:** Use `EXPLAIN ANALYZE` to check query plans.
- **MySQL:** Use `EXPLAIN` to identify bottlenecks.
- **SQLite:** Enable FTS (Full-Text Search) for `LIKE` optimizations.

### **D. Static Analysis**
- **ESLint Plugins:** Use `eslint-plugin-security` to detect raw SQL in code.
- **TypeScript:** Enforce type safety to catch invalid inputs early.

---

## **4. Prevention Strategies**
### **A. Defense in Depth**
1. **Always Use ORMs:**
   - Never build raw SQL manually. Use `knex`, `sequelize`, or `typeorm`.
2. **Input Sanitization:**
   - Reject or sanitize inputs that could break SQL (e.g., `DROP TABLE`).
3. **Least Privilege:**
   - Database users should have `SELECT` only (avoid `ALL PRIVILEGES`).

### **B. Code Patterns**
1. **Modular WHERE Builders:**
   ```javascript
   // reusable WHERE builders
   const ageCondition = (age) => (age ? ['age', age] : null);
   const nameCondition = (name) => (name ? ['name ILIKE ?', `%${name}%`] : null);

   const conditions = [ageCondition(input.age), nameCondition(input.name)].filter(Boolean);
   ```
2. **Default Values for Edge Cases:**
   ```javascript
   const statusFilter = input.status
     ? input.status === 'all' ? null : ['status', input.status]
     : null;
   ```
3. **Deprecate Unsafe Inputs:**
   - Replace `LIKE '%user%'` with `contains` in GraphQL schema:
     ```graphql
     input UserFilter {
       name: String!  # Safe: exact match
       # nameContains: String  # Deprecated: use "name" with "contains" qualifier
     }
     ```

### **C. Testing & CI**
1. **Automated SQL Sanitization Tests:**
   - Test that `input = "' OR 1=1 --"` doesn’t break queries.
2. **Schema Validation in GraphQL:**
   - Enforce that filters only accept allowed operators:
     ```graphql
     input NumericFilter {
       eq: Float
       gt: Float
       lt: Float
       # ❌ Reject: `in: [1, 2, 3]` if not supported
     }
     ```
3. **Database Migration Checks:**
   - Verify SQL compilation in staging before production.

### **D. Monitoring**
- **Alert on Long Queries:**
  - Monitor slow queries with filters (e.g., `EXPLAIN ANALYZE` warnings).
- **Log Query Failures:**
  - Set up alerts for unexpected `SQLSyntaxError` or `400 Bad Request`.

---

## **5. Quick Fix Cheat Sheet**
| **Problem**               | **Quick Fix**                          |
|---------------------------|----------------------------------------|
| SQL Injection             | Use parameterized queries.             |
| `AND` → `OR` logic        | Double-check condition logic.          |
| `LIKE` not working        | Use `ILIKE` for case-insensitive.      |
| `NULL` handling           | Use `IS NULL` vs. `= NULL`.            |
| Date parsing fails        | Standardize to ISO strings.            |
| Aggregations wrong        | Filter before aggregating.             |
| PostgreSQL `BETWEEN NULL` | Exclude `NULL` inputs.                 |
| MySQL `LIKE` with `NULL`  | Replace with `IS NULL` checks.         |

---

## **6. Final Checklist Before Deployment**
- [ ] All filter inputs are validated with schema rules.
- [ ] SQL is parameterized (no string interpolation).
- [ ] Test edge cases (empty inputs, `NULL`, special chars).
- [ ] Enable SQL logging in production (temporarily).
- [ ] Monitor for unexpected query patterns in logs.

---

### **Summary**
- **Security:** Parameterize queries and validate inputs.
- **Logic:** Map GraphQL operators (`gt`, `contains`) to SQL correctly.
- **Database:** Account for dialect-specific syntax.
- **Testing:** Log SQL, unit test builders, and validate schemas.