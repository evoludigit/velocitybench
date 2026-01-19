```markdown
# **Unifying Variants: The Union Type Definition Pattern in Backend Development**

Modern backend systems often deal with complex, polymorphic data where entities share common traits but diverge in specifics. Whether it’s handling different payment methods, logging varied event types, or processing business rules across multiple data sources, you’ll frequently need a way to combine disparate but related data structures into a single, cohesive type.

A well-designed **union type definition** pattern lets you elegantly represent this polymorphic nature while maintaining type safety, clean API contracts, and flexible querying. Without it, you risk bloating your schema with redundant fields, writing fragile type checks, or settling for dynamic solutions that sacrifice performance or maintainability.

In this post, I’ll break down:
- Why traditional schemas struggle with union types
- How to model them effectively using SQL and application logic
- Practical tradeoffs and anti-patterns
- Real-world examples in TypeScript/PostgreSQL

---

## **The Problem: When Your Data Doesn’t Fit a Single Mold**

Let’s start with an example. Suppose you’re building a financial system with different types of transactions:

1. **Bank Transfers**: From account A to account B with a fee.
2. **Visa Payments**: From a credit card to a merchant with a CVV requirement.
3. **Wire Transfers**: Between international accounts with a SWIFT code.

If you try to model all of these under a single `Transaction` table, you’ll hit awkward tradeoffs:

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20),          -- Discriminator column (yuck!)
    sender_id INT,
    receiver_id INT,
    amount DECIMAL(10,2),
    fee DECIMAL(10,2),
    card_number VARCHAR(19),  -- Only applicable for Visa
    cvv VARCHAR(4),          -- Only applicable for Visa
    swift_code VARCHAR(20)   -- Only applicable for wire
);
```

### **Problems with This Approach**
1. **Nullable Columns**: Most fields won’t be used for every transaction type, forcing you to store nulls.
2. **Complex Joins**: To fetch a Visa transaction, you’d need:
   ```sql
   SELECT t.*, v.card_number, v.cvv
   FROM transactions t
   LEFT JOIN visa_payments v ON t.id = v.transaction_id
   WHERE t.type = 'visa';
   ```
3. **Type Safety**: Your application code must manually handle the discriminator (`t.type`), leading to runtime errors if logic is missed.
4. **Schema Rigidity**: Adding a new transaction type requires schema migrations, which can be painful in production.

### **The Core Challenge**
This pattern—where a single table must accommodate multiple, distinct variants—is a classic **union type** problem. Without proper abstraction, your system becomes harder to maintain, query, and extend.

---

## **The Solution: Union Type Definition**

The **Union Type Definition** pattern addresses this by:
- **Decoupling variants** into separate tables (or polymorphic columns) but representing them as a single type in your application logic.
- **Using discriminators** (like `type` or `record_type`) to identify variants, but encapsulating behavior behind a unified interface.
- **Leveraging JSON/JSONB** to handle dynamic fields when SQL isn’t flexible enough.

Here’s how we’ll model our transactions:

```sql
-- Core transaction metadata (shared by all types)
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    type VARCHAR(20) NOT NULL
);

-- Payment-specific fields (Visa)
CREATE TABLE visa_payments (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id),
    card_number VARCHAR(19),
    cvv VARCHAR(4),
    expiration_date DATE
);

-- Wire-specific fields (SWIFT)
CREATE TABLE wire_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id),
    swift_code VARCHAR(20),
    beneficiary_name VARCHAR(100)
);
```

Now, when querying, you can **union all variants** while preserving type information:

```sql
SELECT
    t.id,
    t.amount,
    t.type,
    v.card_number,
    w.swift_code
FROM transactions t
LEFT JOIN visa_payments v ON t.id = v.transaction_id
LEFT JOIN wire_transactions w ON t.id = w.transaction_id
WHERE t.type IN ('visa', 'wire');
```

---

## **Implementation Guide**

### **1. Define the Base Type (Shared Schema)**
Start with a lightweight table containing only fields common to all variants. This ensures all transactions adhere to a **contract**.

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('visa', 'bank', 'wire'))
);
```

### **2. Create Variant Tables (Single-Table Inheritance)**
For each variant, create a table with only the unique fields. Use a foreign key to link back to the base table.

```sql
-- Visa-specific data
CREATE TABLE visa_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    card_number VARCHAR(19) NOT NULL,
    cvv VARCHAR(4),
    expiration_date DATE NOT NULL
);

-- Bank transfer-specific data
CREATE TABLE bank_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id) ON DELETE CASCADE,
    fee DECIMAL(10,2),
    sender_id INT,
    receiver_id INT
);
```

### **3. Use Discriminators Wisely**
The `type` column should:
- Be **enumerated** (use `CHECK` constraints or an enum).
- Never be nullable.
- Map directly to your variant definitions.

```sql
ALTER TABLE transactions ADD CONSTRAINT valid_type CHECK (
    type = 'visa' OR type = 'bank' OR type = 'wire'
);
```

### **4. Query Variants with Unions**
When fetching data, use `LEFT JOIN` to combine all variants:

```sql
SELECT
    t.id,
    t.amount,
    t.type,
    v.card_number,
    v.expiration_date,
    bt.fee,
    wt.swift_code
FROM transactions t
LEFT JOIN visa_transactions v ON t.id = v.transaction_id
LEFT JOIN bank_transactions bt ON t.id = bt.transaction_id
LEFT JOIN wire_transactions wt ON t.id = wt.transaction_id
WHERE t.type IN ('visa', 'bank');
```

### **5. Apply Type Safety in Your Application**
In TypeScript, define interfaces for each variant and a union type:

```typescript
interface TransactionBase {
  id: number;
  amount: number;
  type: 'visa' | 'bank' | 'wire';
  createdAt: string;
}

interface VisaTransaction extends TransactionBase {
  type: 'visa';
  cardNumber: string;
  cvv?: string;
  expirationDate: string;
}

interface BankTransaction extends TransactionBase {
  type: 'bank';
  fee?: number;
  senderId: number;
  receiverId: number;
}

type Transaction = VisaTransaction | BankTransaction | WireTransaction;
// ... (other types)
```

### **6. Handle JSON for Dynamic Fields (Optional)**
If variants have unpredictable schemas, use `JSONB`:

```sql
ALTER TABLE transactions ADD COLUMN payload JSONB;

-- Example for wire transfer:
INSERT INTO transactions (amount, type, payload)
VALUES (1000.00, 'wire', '{"swift_code": "ABCD1234", "beneficiary": "Example Corp"}');
```

Then query with `->>` or `->`:

```sql
SELECT payload->>'swift_code' FROM transactions WHERE type = 'wire';
```

---

## **Common Mistakes to Avoid**

### **1. Overusing JSON for All Fields**
- **Problem**: If you store everything in `payload`, you lose the benefits of relational constraints and indexing.
- **Fix**: Use `JSONB` only for truly unpredictable fields.

### **2. Missing Discriminator Checks**
- **Problem**: Forgetting to validate `type` before accessing variant fields leads to runtime errors.
- **Fix**: Always check `t.type` before joining:

```sql
SELECT ... FROM transactions t
LEFT JOIN bank_transactions bt ON t.id = bt.transaction_id AND t.type = 'bank'
```

### **3. Poor Indexing Strategy**
- **Problem**: Without an index on `type`, queries become slow:
  ```sql
  CREATE INDEX idx_transactions_type ON transactions(type);
  ```

### **4. Violating Referential Integrity**
- **Problem**: Foreign keys on variant tables without `ON DELETE CASCADE` can orphan records.
- **Fix**: Ensure cascading deletes are intentional:

```sql
ALTER TABLE visa_transactions DROP CONSTRAINT IF EXISTS
  visa_transactions_transaction_id_fkey;
ALTER TABLE visa_transactions ADD CONSTRAINT
  visa_transactions_transaction_id_fkey
  FOREIGN KEY (transaction_id) REFERENCES transactions(id)
  ON DELETE CASCADE;
```

### **5. Ignoring Nullable Fields**
- **Problem**: Forgetting that variant-specific fields are null for other types:
  ```sql
  -- ❌ Bad: Assumes card_number is always set
  SELECT card_number FROM transactions WHERE type = 'visa';

  -- ✅ Better: Explicitly join only visa_transactions
  SELECT v.card_number FROM transactions t
  JOIN visa_transactions v ON t.id = v.transaction_id;
  ```

---

## **Key Takeaways**

✅ **Decouple variants** into separate tables to avoid nullable columns.
✅ **Use discriminators** to identify types but enforce them rigorously.
✅ **Union queries** for flexible fetching while preserving type safety.
✅ **Leverage JSONB** only for truly dynamic fields.
✅ **Index discriminators** for performance.
✅ **Fail fast** with discriminator checks in your application code.
✅ **Avoid over-engineering**—this pattern works best for 2–5 variants. More? Reevaluate.

---

## **Conclusion**

The **Union Type Definition** pattern is a powerful tool for modeling polymorphic data in SQL-based systems. By separating variants into logical tables while maintaining a shared contract, you gain:
- Cleaner queries with `LEFT JOIN`-based unions.
- Stronger type safety in application code.
- Flexibility to add new variants without breaking existing logic.

### **When to Use It**
- Your data has **2–5 distinct but related types**.
- You need **efficient querying** of all variants together.
- Your team can **maintain discipline** with discriminators.

### **When to Avoid It**
- You have **10+ variants** (consider a different approach, like EAV).
- Your data is **highly dynamic** (JSON might be better).
- Your ORM lacks **polymorphic query support** (e.g., Django’s `AbstractBaseModel`).

### **Next Steps**
- Extend this pattern with **database-level triggers** for invariants.
- Use **application-level polymorphic repositories** (e.g., NestJS’s `Aggregates`).
- Experiment with **PostgreSQL’s JSONB functions** for advanced queries.

---

**Final Thought**
Union types aren’t about hiding complexity—they’re about organizing it. Once you’ve normalized your variants, the rest (type safety, querying, and extensibility) falls into place.

Now go build something that scales gracefully!
```