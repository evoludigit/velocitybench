```markdown
# **[Database-First Mutations: Running GraphQL via Stored Procedures](https://example.com/blog/mutation-stored-procedures)**

### *Execute business logic in the database while keeping your GraphQL API lean and maintainable.*

---

## **Introduction**

As backend developers, we’re constantly balancing the tradeoffs between **application logic** and **database complexity**. GraphQL APIs thrive on flexibility—allowing clients to request exactly what they need—yet mutations often end up duplicating business logic across your application and database layers. You might write a mutation in your resolver like this:

```javascript
// resolver.js
const createUser = async (_, { input }) => {
  // Validate input
  // Check constraints
  // Transform data
  // Call ORM to persist

  return await db.user.create({ data: input });
};
```

But what if that logic could be **trusted to the database instead**? What if your business rules—like validation, transactional logic, and data transformations—lived in the database itself, where they’re **version-controlled, optimized, and secure by design**?

Enter the **"Mutation Execution via Stored Procedures"** pattern: a way to offload GraphQL mutations to the database, where they’re executed as stored procedures. This approach isn’t new—it’s been used for decades in traditional ETL and transactional systems—but it’s gaining traction in modern GraphQL architectures for good reason.

In this post, we’ll explore:
✅ **Why mutations end up duplicated** between app and database
✅ **How stored procedures can centralize logic**
✅ **Real-world examples** in PostgreSQL, SQL Server, and MySQL
✅ **Implementation best practices** and pitfalls to avoid
✅ **When (and when *not*) to use this pattern**

Let’s dive in.

---

## **The Problem: Mutations Duplicated Across the Stack**

### **1. Logic Stuck in the Application Layer**
Most GraphQL APIs follow this workflow:
1. **Client sends mutation request** → Resolver receives input.
2. **Resolver validates, transforms, and calls an ORM** (e.g., Prisma, TypeORM).
3. **ORM persists changes** → Database echoes back data.

But here’s the problem: **business logic is split** between:
- **Application layer** (validation, auth, workflows)
- **Database layer** (constraints, triggers, stored procs)

This duplication leads to:
🔸 **Inconsistencies**: Different versions of logic in code vs. DB.
🔸 **Performance bottlenecks**: Complex logic runs in app instead of optimized DB queries.
🔸 **Maintenance hell**: Changes must be applied in *two* places.

### **2. The GraphQL Resolver Overload**
Consider a `transferFunds` mutation:

```graphql
mutation TransferFunds($input: TransferInput!) {
  transferFunds(input: $input) {
    success
    error
  }
}
```

A naive resolver might look like this:

```javascript
// resolver.js
const transferFunds = async (_, { input }) => {
  const { fromAccount, toAccount, amount } = input;

  // 1. Validate inputs
  if (fromAccount.balance < amount) throw new Error("Insufficient funds");

  // 2. Lock rows to prevent race conditions
  await db.transaction(async (tx) => {
    // 3. Debit fromAccount
    await tx.update('accounts', { balance: fromAccount.balance - amount }, { where: { id: fromAccount.id } });

    // 4. Credit toAccount
    await tx.update('accounts', { balance: toAccount.balance + amount }, { where: { id: toAccount.id } });
  });

  return { success: true };
};
```

This is **all application logic**—what if the rules changed? You’d need to update *every* deployment.

### **3. Database Logic is Hard to Access**
Even if you *could* move logic to the database, it’s often scattered:
- **Constraints** (e.g., `CHECK` clauses) in the schema.
- **Triggers** for side effects (e.g., notifications).
- **Stored procedures** for complex workflows.

But stored procedures are rarely used for **GraphQL mutations**—mostly for ad-hoc queries or ETL.

---
## **The Solution: Offload Mutations to Stored Procedures**

The **"Mutation Execution via Stored Procedures"** pattern shifts business logic to the database, treating mutations as **direct procedure calls**. Here’s how it works:

1. **GraphQL resolver calls a stored procedure** (via JDBC/ODBC, pooling, or ORM).
2. **Stored procedure executes** business logic, transactions, and validations.
3. **Result is returned to the client** (either directly or via a GQL resolver).

### **Why This Works for GraphQL**
✔ **Centralized logic**: Business rules live *once* in the database.
✔ **Optimized execution**: The DB runs complex logic where it’s fastest.
✔ **Version control**: Stored procedures can be tracked in Git alongside your app code.
✔ **Security**: Procedures can enforce auth/permissions at the DB level.

### **When to Use This Pattern**
✅ **Complex transactions** (e.g., financial transfers, inventory updates).
✅ **Strict data consistency** (e.g., ETL, auditing, multi-table updates).
✅ **Performance-critical logic** (e.g., heavy computations, aggregations).
❌ **Simple CRUD** (use ORM/resolvers instead).
❌ **Frequent schema changes** (procedures can be harder to refactor).

---

## **Components & Solutions**

### **1. Database Layer: Stored Procedures**
Stored procedures handle the business logic. They:
- Validate inputs.
- Execute transactions.
- Return structured results.

#### **Example: PostgreSQL Procedure for `transferFunds`**
```sql
CREATE OR REPLACE FUNCTION transfer_funds(
  p_from_account_id UUID,
  p_to_account_id UUID,
  p_amount DECIMAL(10, 2)
) RETURNS JSON AS $$
DECLARE
  v_from_balance DECIMAL(10, 2);
  v_to_balance DECIMAL(10, 2);
BEGIN
  -- Check account existence
  SELECT balance INTO v_from_balance
  FROM accounts WHERE id = p_from_account_id;

  IF v_from_balance < p_amount THEN
    RETURN json_build_object(
      'success', false,
      'error', 'Insufficient funds'
    );
  END IF;

  -- Deduct from source account
  UPDATE accounts
  SET balance = balance - p_amount
  WHERE id = p_from_account_id
  RETURNING * INTO v_from;

  -- Credit to target account
  UPDATE accounts
  SET balance = balance + p_amount
  WHERE id = p_to_account_id
  RETURNING * INTO v_to;

  -- Return success
  RETURN json_build_object(
    'success', true,
    'fromAccount', v_from,
    'toAccount', v_to
  );
EXCEPTION WHEN OTHERS THEN
  RETURN json_build_object(
    'success', false,
    'error', SQLERRM
  );
END;
$$ LANGUAGE plpgsql;
```

### **2. Application Layer: Resolver Calls Procedure**
The GraphQL resolver acts as a **proxy** to the stored procedure.

#### **Option A: Direct JDBC Call (PostgreSQL Example)**
```javascript
// resolver.js
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

const transferFunds = async (_, { input }) => {
  const { fromAccountId, toAccountId, amount } = input;

  const client = await pool.connect();
  try {
    const result = await client.query(
      `SELECT * FROM transfer_funds($1, $2, $3)`,
      [fromAccountId, toAccountId, amount]
    );
    return result.rows[0];
  } finally {
    client.release();
  }
};
```

#### **Option B: ORM Wrapper (Prisma Example)**
If your ORM supports raw SQL (e.g., Prisma’s `$queryRaw`), you can call the procedure directly:

```typescript
// resolver.ts
const transferFunds = async (_, { input }) => {
  const { fromAccountId, toAccountId, amount } = input;

  const result = await prisma.$queryRaw`
    SELECT * FROM transfer_funds(${fromAccountId}, ${toAccountId}, ${amount})
  `;

  return result[0];
};
```

#### **Option C: GraphQL-Database Bridge (Hasura/PostgREST)**
If you’re using a **database-first GraphQL layer** (e.g., Hasura), you can expose the procedure via `remote_schema`:

```yaml
# hasura/metadata/databases/default/tables/public/transfer_funds.yaml
actions:
  - name: transferFunds
    definition:
      query:
        sql: SELECT transfer_funds($1, $2, $3)
        params:
          - { name: p_from_account_id, type: uuid }
          - { name: p_to_account_id, type: uuid }
          - { name: p_amount, type: decimal }
    permissions:
      - role: user
        operation: select
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Define the Procedure**
Start with a **clear contract** for your mutation. For `transferFunds`:
- Input: `fromAccountId`, `toAccountId`, `amount`.
- Output: `success`, `error`, or transaction results.

Example (PostgreSQL):
```sql
CREATE OR REPLACE FUNCTION transfer_funds(...)
RETURNS JSON AS $$
-- Implementation here
$$ LANGUAGE plpgsql;
```

### **Step 2: Expose the Procedure via GraphQL**
Choose your integration method:
1. **Direct JDBC/ODBC**: Use a connection pool to call the procedure.
2. **ORM Wrapper**: Use a `queryRaw` or similar feature.
3. **Database-First GQL**: Use Hasura/PostgREST to expose it as a remote action.

### **Step 3: Test Thoroughly**
Procedures should handle:
- **Edge cases** (e.g., invalid IDs, negative amounts).
- **Transactions** (rollbacks on failure).
- **Error messages** (return structured JSON).

Example test (PostgreSQL):
```sql
-- Test insufficient funds
SELECT * FROM transfer_funds('123', '456', 1000000); -- Should fail
```

### **Step 4: Secure the Procedure**
- **Input validation**: Use `CHECK` constraints or procedural checks.
- **Authorization**: Enforce DB-level permissions (e.g., row-level security in PostgreSQL).
- **Audit logging**: Track procedure calls in an `audit_log` table.

Example (PostgreSQL row-level security):
```sql
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY account_owner_policy ON accounts
  USING (id = current_setting('app.user_account_id')::uuid);
```

### **Step 5: Deploy & Monitor**
- **Version control**: Store procedure SQL in Git alongside your app code.
- **Performance**: Monitor slow procedures in your DB dashboard.
- **Rollback plan**: Ensure procedures can be reverted safely.

---

## **Common Mistakes to Avoid**

### **❌ 1. Overusing Stored Procedures for Simple Logic**
Stored procedures are **not** a silver bullet. If your mutation is just `CREATE` or `UPDATE`, stick with your ORM.

### **❌ 2. Ignoring Error Handling**
Procedures should **always** return structured JSON (not just `RAISE EXCEPTION`). Example:

```sql
-- BAD: Crashes the client
RAISE EXCEPTION 'Error: %', SQLERRM;

-- GOOD: Returns structured data
RETURN json_build_object(
  'success', false,
  'error', SQLERRM
);
```

### **❌ 3. Hardcoding Credentials**
Never hardcode DB credentials in procedures. Use **environment variables** or a **credential manager**.

### **❌ 4. Not Testing Transactions**
Procedures with `UPDATE`/`INSERT` must test:
- **Success cases**.
- **Partial failures** (e.g., one `UPDATE` succeeds, another fails).
- **Race conditions** (e.g., `SELECT...FOR UPDATE`).

### **❌ 5. Forgetting to Version Procedures**
Procedures change over time—**document breaking changes** and use a versioning scheme (e.g., `transfer_funds_v2`).

---

## **Key Takeaways**

✅ **Stored procedures centralize business logic**, reducing duplication.
✅ **They’re ideal for complex transactions** (e.g., financial ops, inventory).
✅ **GraphQL resolvers act as a proxy**, calling procedures via JDBC/ORM.
✅ **Test thoroughly**: Edge cases, errors, and transactions.
✅ **Secure procedures**: Input validation, RLS, and logging.
❌ **Don’t overuse them**: Simple mutations belong in the app layer.
❌ **Avoid tight coupling**: Keep procedures DB-agnostic where possible.

---

## **Conclusion**
The **"Mutation Execution via Stored Procedures"** pattern isn’t for every GraphQL API, but it’s a **powerful tool** for scenarios where:
- Business logic is **complex and centralized**.
- **Performance** requires DB-side execution.
- **Auditability** is critical (e.g., financial systems).

By offloading mutations to the database, you:
✔ **Reduce app-server load**.
✔ **Improve consistency** (logic lives in one place).
✔ **Leverage DB optimizations** for heavy workloads.

### **Start Small**
Don’t rewrite all mutations at once. Pick **one complex operation** (like `transferFunds`) and move it to a stored procedure. Measure the impact, then expand.

### **Alternatives to Explore**
- **Functional DBs**: For even more complex logic, consider databases like **PostgreSQL + PL/pgSQL** or **SQL Server CLR**.
- **Event-Driven**: For async workflows, pair stored procedures with **DB events** (e.g., PostgreSQL `NOTIFY`).

---
**What’s your experience with stored procedures in GraphQL?** Have you used this pattern successfully? Share your stories in the comments!

---
### **Further Reading**
- [PostgreSQL Stored Procedures Docs](https://www.postgresql.org/docs/current/plpgsql.html)
- [SQL Server Stored Procedures](https://learn.microsoft.com/en-us/sql/relational-databases/stored-procedures/stored-procedures-database-engine)
- [Hasura Remote Schema Actions](https://hasura.io/docs/latest/graphql/core/remote-schema-actions/)
```