---
# **Mastering Data Polymorphism with Union Type Definition**

*How to Handle Multiple Data Structures in a Single API Response*

---

## **Introduction**

When building APIs, you often need to return different types of data through a single endpoint—whether it's combining accounts, transactions, or business entities in a unified response. Traditional RESTful designs force you to either:

- **Split endpoints** (e.g., `/users`, `/products`, `/orders`), which leads to over-fetching or client-side logic to stitch responses.
- **Use nested objects** (e.g., `{"type": "user", "data": {...}}`), which bloats payloads and complicates parsing.

This is where the **Union Type Definition** (UTD) pattern shines. By defining a standardized structure that accommodates multiple data types, you reduce redundancy, improve API flexibility, and make clients happier.

In this post, we’ll explore:
✅ How union types resolve messy data structures
✅ Practical examples in SQL, JSON, and API design
✅ Tradeoffs and anti-patterns
✅ Best practices for implementation

---

## **The Problem: Why Union Types Matter**

### **Real-World Pain Points**
Imagine a payments API that must return **both bank transfers and cryptocurrency transactions** in the same response. Without a unified approach:

```json
// Problem: Inconsistent response shapes
{
  "id": "tx-123",
  "type": "bank_transfer",
  "amount": 500.00,
  "currency": "USD",
  "sender": "Alice",
  "recipient": "Bob"
}
{
  "id": "tx-456",
  "type": "crypto_transfer",
  "amount": 0.02,
  "currency": "BTC",
  "network": "Ethereum",
  "address": "0x..."
}
```

**Issues:**
- Clients must write **type-checking logic** to handle each case.
- **Over-fetching**: The API returns fields irrelevant to the request.
- **Client-side complexity**: Libraries like Axios or GraphQL clients struggle with dynamic schemas.

### **Database-Side Challenges**
Even in SQL, polymorphism is tricky. For example, storing `User`, `Customer`, and `Guest` in a single table with a `type` column:

```sql
-- Problem: Discriminator columns + nulls
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20),  -- 'user', 'customer', or 'guest'
    email VARCHAR(255),  -- NULL for guests
    membership_level VARCHAR(50)  -- NULL for guests
);
```

**Problems:**
- Joins become messy when filtering by `type`.
- ORMs like Django or Prisma complain about incomplete fields.
- Indexes on discriminators add overhead.

---

## **The Solution: Union Type Definition**

A **Union Type Definition** (UTD) is a schema or contract that:

1. **Standardizes fields** across all variants (e.g., always include `id` and `created_at`).
2. **Validates required fields** per type (e.g., `email` for `User` but not for `Guest`).
3. **Reduces client-side branching** by surfacing only relevant data.

### **How It Works**
1. **Define the union schema** (e.g., OpenAPI/Swagger, JSON Schema, Prisma schema).
2. **Query database tables** and map results to the union type.
3. **Return structured payloads** that clients can deserialize cleanly.

---

## **Components of Union Type Definition**

### **1. Schema Definition (OpenAPI Example)**
```yaml
# openapi.yaml
components:
  schemas:
    Transaction:
      type: object
      discriminator:
        propertyName: type
        mapping:
          bank_transfer: '#/components/schemas/BankTransfer'
          crypto_transfer: '#/components/schemas/CryptoTransfer'
      properties:
        id:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        # Shared fields
    BankTransfer:
      allOf:
        - $ref: '#/components/schemas/Transaction'
        - type: object
          properties:
            amount:
              type: number
              format: float
            currency:
              type: string
              enum: [USD, EUR]
            sender:
              type: string
            recipient:
              type: string
    CryptoTransfer:
      allOf:
        - $ref: '#/components/schemas/Transaction'
        - type: object
          properties:
            amount:
              type: number
              format: float
            currency:
              type: string
              enum: [BTC, ETH]
            network:
              type: string
```

### **2. Database Tables**
```sql
-- Separate tables for each variant
CREATE TABLE bank_transfers (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10, 2),
    currency VARCHAR(3),
    sender_id INTEGER REFERENCES accounts(id),
    recipient_id INTEGER REFERENCES accounts(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crypto_transfers (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10, 2),
    currency VARCHAR(3),
    network VARCHAR(20),
    recipient_address VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **3. API Endpoint (Node.js/Express + Prisma)**
```javascript
// src/routes/transactions.js
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

app.get('/transactions', async (req, res) => {
  const transactions = await Promise.all([
    prisma.bankTransfer.findMany(),
    prisma.cryptoTransfer.findMany()
  ])
  .then(([bank, crypto]) => [
    ...bank.map(tx => ({
      type: 'bank_transfer',
      ...tx,
      created_at: tx.created_at.toISOString()
    })),
    ...crypto.map(tx => ({
      type: 'crypto_transfer',
      ...tx,
      created_at: tx.created_at.toISOString()
    }))
  ]);

  res.type('application/json');
  res.json({ data: transactions });
});
```

### **Response Example**
```json
{
  "data": [
    {
      "type": "bank_transfer",
      "id": "tx-123",
      "created_at": "2023-10-01T00:00:00Z",
      "amount": 500.00,
      "currency": "USD",
      "sender": "Alice",
      "recipient": "Bob"
    },
    {
      "type": "crypto_transfer",
      "id": "tx-456",
      "created_at": "2023-10-01T00:00:00Z",
      "amount": 0.02,
      "currency": "BTC",
      "network": "Ethereum",
      "recipient_address": "0x..."
    }
  ]
}
```

---

## **Implementation Guide**

### **Step 1: Define Your Union Schema**
- Use **OpenAPI** (for APIs), **JSON Schema** (for validation), or **GraphQL’s interfaces** (if applicable).
- Start with a base type and **extend** for variants:
  ```yaml
  # Postgres (Table of Contents) example
  CREATE TYPE transaction_type AS ENUM ('bank_transfer', 'crypto_transfer');

  -- Shared column for all variants
  CREATE TABLE transactions (
      id UUID PRIMARY KEY,
      type transaction_type NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```

### **Step 2: Design Database Tables**
- **Option A**: Separate tables with a discriminator column (PostgreSQL `polymorphic` extension).
- **Option B**: Union tables (SQL Server’s `UNION ALL` joins).
- **Option C**: JSONB columns for dynamic fields (e.g., `metadata` for unknown attributes).

**Example: PostgreSQL Polymorphism**
```sql
-- Enable polymorphic extension
CREATE EXTENSION IF NOT EXISTS "polymorphic";

-- Define variants
CREATE TYPE transaction_variant AS ENUM ('bank_transfer', 'crypto_transfer');

-- Base table
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    variant transaction_variant NOT NULL,
    bank_transfer_data JSONB,  -- For bank_transfers
    crypto_transfer_data JSONB   -- For crypto_transfers
);

-- Index for fast lookups
CREATE INDEX idx_transactions_variant ON transactions(variant);
```

### **Step 3: Query and Map Results**
- Use **CTEs (Common Table Expressions)** to merge results:
  ```sql
  WITH bank_transfers AS (
      SELECT
          tx.id,
          'bank_transfer' AS variant,
          jsonb_build_object(
              'amount', tx.amount,
              'currency', tx.currency,
              'sender_id', tx.sender_id,
              'recipient_id', tx.recipient_id
          ) AS data
      FROM bank_transfers tx
  ),
  crypto_transfers AS (
      SELECT
          tx.id,
          'crypto_transfer' AS variant,
          jsonb_build_object(
              'amount', tx.amount,
              'currency', tx.currency,
              'network', tx.network,
              'recipient_address', tx.recipient_address
          ) AS data
      FROM crypto_transfers tx
  )
  SELECT
      id,
      variant,
      data,
      NOW() AS created_at  -- Shared field
  FROM bank_transfers
  UNION ALL
  SELECT
      id,
      variant,
      data,
      created_at
  FROM crypto_transfers;
  ```

### **Step 4: Validate and Serialize**
- Use a library like **Zod** (JavaScript) or **Pydantic** (Python) to enforce the union schema:
  ```javascript
  // Using Zod
  const TransactionSchema = z.discriminatedUnion('type', [
    z.object({
      type: z.literal('bank_transfer'),
      amount: z.number(),
      currency: z.enum(['USD', 'EUR']),
      sender: z.string(),
      recipient: z.string(),
    }),
    z.object({
      type: z.literal('crypto_transfer'),
      amount: z.number(),
      currency: z.enum(['BTC', 'ETH']),
      network: z.string(),
      recipient_address: z.string(),
    })
  ]);

  // Example usage
  const response = await TransactionSchema.parseAsync(transactions.data);
  ```

---

## **Common Mistakes to Avoid**

### **❌ Overly Complex Discriminators**
- **Bad**: Using `type`, `kind`, or `category` without a standardized naming convention.
- **Fix**: Stick to terms like `variant`, `type`, or `class` for clarity.

### **❌ Inconsistent Field Naming**
- **Bad**: `BankTransfer` has `sender_id` but `CryptoTransfer` has `from_address`.
- **Fix**: Use **shared field names** where possible (e.g., `source` and `destination`).

### **❌ No Schema Validation**
- **Bad**: Letting clients parse raw JSON without validation.
- **Fix**: Enforce schemas at the **API gateway** (Kong, Apigee) or **database layer** (Postgres JSON validation).

### **❌ Ignoring Performance**
- **Bad**: Using `JSONB` for every variant without indexing.
- **Fix**: Use **columnar storage** for frequently accessed fields (e.g., `currency`).

### **❌ Deep Nesting**
- **Bad**: Returning a nested object like:
  ```json
  {
    "type": "bank_transfer",
    "data": {
      "amount": 500,
      "details": { ... }
    }
  }
  ```
- **Fix**: Flatten the structure unless necessary.

---

## **Key Takeaways**

✔ **Union types unify disparate data** under a single contract.
✔ **Separate tables > single-table inheritance** (avoid the "spaghetti database" problem).
✔ **Use discriminators** (PostgreSQL `polymorphic` or `type` column) to enforce structure.
✔ **Validate early**: Schema validation at API/database boundaries saves clients from errors.
✔ **Index shared fields** (e.g., `type`, `created_at`) for performance.
✔ **Document variants clearly**—clients need to know all possible field sets.

---

## **Conclusion**

Union type definitions are a powerful pattern for **scalable, maintainable APIs** that handle polymorphic data elegantly. By combining:
- **Structured schemas** (OpenAPI/JSON Schema),
- **Database efficiency** (separate tables + JSONB),
- **Runtime validation** (Zod/Pydantic),

you eliminate messy client-side logic and reduce API bloat.

**When to Use This Pattern:**
- When multiple data types share a core structure (e.g., `Transaction`, `User`, `Order`).
- When you need **flexibility without splitting endpoints**.
- When clients demand **predictable payloads**.

**Alternatives to Consider:**
- **GraphQL**: Handles polymorphism natively with interfaces.
- **Protobuf**: For high-performance microservices with strict schemas.
- **Event Sourcing**: If state changes are more important than shape consistency.

Start small—implement union types for one variant type and expand as needed. Your API (and clients) will thank you.

---
**Further Reading:**
- [PostgreSQL Polymorphic Extension](https://www.postgresql.org/docs/current/polymorphic.html)
- [Zod Union Schemas](https://zod.dev/?id=discriminated-unions)
- [GraphQL Interfaces](https://graphql.org/learn/global-object-types/#interfaces)

---
*What’s your go-to pattern for handling polymorphic data? Share in the comments!*