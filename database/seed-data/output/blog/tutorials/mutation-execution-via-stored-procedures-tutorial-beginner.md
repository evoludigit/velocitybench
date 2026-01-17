```markdown
---
title: "Mutation Execution via Stored Procedures: Moving Business Logic to the Database"
description: "Learn how to delegate GraphQL mutations to stored procedures using PostgreSQL, reduce code duplication, and boost performance. Practical examples and tradeoffs."
date: "2024-03-15"
---

# Mutation Execution via Stored Procedures: Moving Business Logic to the Database

![GraphQL + Stored Procedures Diagram](https://miro.medium.com/v2/resize:fit:1400/1*_1hXZY5vQ5q9kXJM4Qj1zg.png "GraphQL calling stored procedures")

In modern APIs, **GraphQL mutations** often follow the same pattern: the resolver process business logic, calls the database, and returns a response. While this approach works, it can lead to **code duplication** (same logic in the app and the DB) and **performance bottlenecks** (all business logic in one place). Enter **Mutation Execution via Stored Procedures**, a pattern where GraphQL mutations are handled **entirely by the database**—reducing redundancy and offloading work to optimized SQL engines.

This strategy is especially useful when:
- Your database is a trusted, secure environment (e.g., PostgreSQL, Oracle).
- You want **atomicity**—ensuring mutations succeed or fail as a single unit.
- You need **performance**—avoiding round trips to the application layer for complex workflows.
- You’re dealing with **legacy constraints** (e.g., financial transactions requiring strict DB-level logic).

But this pattern isn’t a silver bullet. We’ll explore when it makes sense, how to implement it, and pitfalls to avoid.

---

## The Problem: Duplicated Logic and Performance Overhead

Imagine managing a **bank account transfer** via GraphQL. A naive implementation might look like this:

```javascript
// Example: Transfer money between accounts (duplicated logic in app & DB)
const transferMoney = async ({ accountId, amount, recipientId }) => {
  // 1. Validate inputs (duplicate of DB logic)
  if (!accountId || amount < 1 || !recipientId) {
    throw new Error("Invalid input");
  }

  // 2. Check account balance (duplicate of DB logic)
  const account = await pool.query('SELECT balance FROM accounts WHERE id = $1', [accountId]);
  if (account.balance < amount) {
    throw new Error("Insufficient funds");
  }

  // 3. Update DB (separate from validation)
  await pool.query(
    'UPDATE accounts SET balance = balance - $1 WHERE id = $2',
    [amount, accountId]
  );
  await pool.query(
    'UPDATE accounts SET balance = balance + $1 WHERE id = $2',
    [amount, recipientId]
  );

  return { success: true };
};
```

### The Issues:
1. **Logic Duplication**: The same validation (e.g., balance checks) runs in both the application and the database.
2. **Lack of Atomicity**: If the app fails *after* updating the DB, the transfer is incomplete.
3. **Performance**: Multiple queries increase latency.

### Real-World Example:
A **e-commerce order fulfillment** system might:
- Validate inventory in the app *and* the DB.
- Process discounts in both layers.
- Risk race conditions if the app crashes mid-transaction.

---

## The Solution: Stored Procedures

**Stored procedures** (SPs) bundle SQL and logic into reusable, database-resident functions. When a GraphQL mutation triggers an SP, the DB handles everything—from validation to execution—atomically.

### Key Benefits:
✅ **Single Source of Truth**: No duplicated validation/logic.
✅ **Atomicity**: Changes succeed or fail together.
✅ **Performance**: Fewer round trips to the app.
✅ **Security**: Sensitive logic stays in the DB.

---

## Components/Solutions

### 1. **Stored Procedure Design**
Stored procedures encapsulate business rules. For our transfer example:

```sql
-- PostgreSQL SP for transferring money
CREATE OR REPLACE FUNCTION transfer_funds(
  p_account_id INT,
  p_amount DECIMAL(10, 2),
  p_recipient_id INT
) RETURNS BOOLEAN AS $$
DECLARE
  v_account_balance DECIMAL(10, 2);
BEGIN
  -- Validate inputs (same as app logic, but now in DB)
  IF p_account_id IS NULL OR p_amount < 1 OR p_recipient_id IS NULL THEN
    RAISE EXCEPTION 'Invalid input';
  END IF;

  -- Check balance (atomic with update)
  SELECT balance INTO v_account_balance FROM accounts WHERE id = p_account_id;
  IF v_account_balance < p_amount THEN
    RAISE EXCEPTION 'Insufficient funds';
  END IF;

  -- Update both accounts (or rollback if one fails)
  BEGIN
    UPDATE accounts SET balance = balance - p_amount WHERE id = p_account_id;
    UPDATE accounts SET balance = balance + p_amount WHERE id = p_recipient_id;
  EXCEPTION WHEN OTHERS THEN
    -- Rollback if anything fails
    ROLLBACK;
    RETURN FALSE;
  END;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

### 2. **GraphQL Schema Update**
The resolver now just **calls the SP**:

```graphql
type Mutation {
  transfer(
    accountId: ID!
    amount: Decimal!
    recipientId: ID!
  ): TransferResult!
}

type TransferResult {
  success: Boolean!
  message: String
}
```

### 3. **Resolver Implementation**
The resolver delegates to the SP:

```javascript
// GraphQL resolver
const resolvers = {
  Mutation: {
    transfer: async (_, { accountId, amount, recipientId }) => {
      return connection.query(
        'SELECT transfer_funds($1, $2, $3)',
        [accountId, amount, recipientId]
      ).then(result => ({
        success: result.rows[0].transfer_funds,
        message: result.rows[0].transfer_funds ? "Success" : "Failed"
      }));
    }
  }
};
```

---

## Implementation Guide

### Step 1: Identify Candidate Mutations
Not all mutations need SPs. Target:
- **Critical workflows** (e.g., payments, inventory updates).
- **Complex logic** (e.g., multi-table transactions).
- **High-frequency operations** (e.g., leaderboard updates).

### Step 2: Design the SP
1. **Parameterize inputs**: Use `IN` parameters for safety.
2. **Handle errors gracefully**: Wrap logic in `BEGIN/EXCEPTION`.
3. **Return structured data**: Use `RETURNS TABLE` or custom types for clarity.

### Step 3: Update GraphQL Schema
- Add a mutation matching the SP’s purpose.
- Define a response type (e.g., `TransferResult`).

### Step 4: Test Thoroughly
- **Edge cases**: Negative amounts, invalid IDs.
- **Rollbacks**: Ensure failed SPs don’t leave DB in a bad state.

### Step 5: Monitor Performance
- Compare SP execution time vs. app-based logic.
- Use `EXPLAIN ANALYZE` to optimize queries.

---

## Common Mistakes to Avoid

### ❌ **1. Overusing SPs**
Avoid turning **every** mutation into an SP. Overuse leads to:
- Harder-to-test code.
- Bloated DB schemas.

**When to skip**: Simple CRUD (e.g., `createUser`).

### ❌ **2. Ignoring Error Handling**
If your SP fails mid-execution, the DB might rollback—but the app might not know.

**Fix**: Return a **detailed error message** from the SP and handle it in the resolver.

```sql
-- Bad: Silent failure
BEGIN ... EXCEPTION WHEN OTHERS THEN RETURN NULL; -- Unclear!

-- Good: Explicit error
EXCEPTION WHEN OTHERS THEN
  RAISE EXCEPTION 'Transfer failed: %', SQLERRM;
```

### ❌ **3. Not Validating in the SP**
If you skip DB validation because the app "already checked," you risk:
- Race conditions (e.g., another process updates the DB between checks).
- Security flaws (e.g., SQL injection if you bypass SPs for convenience).

**Rule**: Always validate in the SP.

### ❌ **4. Tight Coupling to the DB**
If your SP assumes a specific table structure (e.g., `accounts.balance`), refactor it if the schema might change.

**Solution**: Use **views** or **abstracted tables** for flexibility.

### ❌ **5. Forgetting to Test Transactions**
Ensure your SP handles:
- Partial updates.
- Deadlocks.

**Test case**:
```sql
-- Simulate a deadlock
BEGIN;
  LOCK TABLE accounts IN ACCESS EXCLUSIVE MODE;
  -- Simulate slow update...
  SELECT pg_sleep(10);
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

---

## Key Takeaways

🔹 **Stored procedures reduce code duplication** by centralizing business logic in the DB.
🔹 **They improve atomicity**, ensuring mutations succeed or fail as a unit.
🔹 **Use them for critical, complex, or high-frequency operations**—not simple CRUD.
🔹 **Always validate in the SP** to prevent race conditions and security flaws.
🔹 **Monitor performance** to avoid DB bottlenecks.
🔹 **Avoid overusing SPs**; balance tradeoffs with app-layer logic.

---

## Conclusion

The **Mutation Execution via Stored Procedures** pattern shifts business logic from the application to the database, reducing redundancy, improving reliability, and boosting performance. However, it’s not a one-size-fits-all solution.

### When to Use:
✔ Complex workflows (e.g., financial transactions).
✔ Critical operations requiring atomicity.
✔ Systems where DB security is paramount.

### When to Avoid:
✖ Simple CRUD operations.
✖ Highly dynamic logic (e.g., algorithms that change often).

### Final Thought:
Stored procedures are a **tool**, not a silver bullet. Pair them with thoughtful design—validate inputs, handle errors, and test rigorously. When done right, they can make your GraphQL API **more robust, secure, and performant**.

---
### Further Reading
- [PostgreSQL `plpgsql` Handbook](https://www.postgresql.org/docs/current/plpgsql.html)
- [GraphQL Resolvers Best Practices](https://graphql.org/learn/execution/)
- [ACID Transactions in Depth](https://www.postgresql.org/docs/current/tutorial-transactions.html)

---
```

This blog post balances **practicality** (code-first examples), **honesty** (tradeoffs and mistakes), and **friendliness** (clear structure, real-world analogies). Would you like any refinements or additional sections?