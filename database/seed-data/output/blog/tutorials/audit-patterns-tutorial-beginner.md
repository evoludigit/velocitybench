```markdown
---
title: "Audit Patterns: How to Track Changes and Build Trust in Your Applications"
date: 2023-10-15
author: Jane Doe
tags: ["database design", "backend engineering", "API patterns", "audit trails", "DDD"]
coverImage: "https://images.unsplash.com/photo-1628157524484-3728c786bcbc?ixlib=rb-1.2.1&auto=format&fit=crop&w=1470&q=80"
---

# Audit Patterns: How to Track Changes and Build Trust in Your Applications

Have you ever wondered how financial applications like PayPal or banking platforms ensure that every transaction is tracked immutably? Or how healthcare systems maintain detailed records of patient data changes to comply with regulations like HIPAA? The answer lies in **audit patterns**, a fundamental yet often overlooked aspect of robust backend design.

Audit patterns aren’t just about logging what changed—they’re about creating a verifiable history of your application’s state. Whether you're building a SaaS platform, an internal tool, or even a critical infrastructure system, ensuring that every action is trackable, secure, and traceable can make the difference between a reliable application and one that’s hard to trust. In this guide, we’ll dive into the world of audit patterns, explore their challenges, and walk through practical ways to implement them in your projects.

By the end of this post, you’ll have a clear understanding of when to use audit patterns, how to design them effectively, and real-world code examples to start implementing them immediately. Let’s get started!

---

## The Problem: Why Audit Trails Matter

Imagine this scenario: A user reports that their account balance was incorrectly reduced by $100 after a payment was processed. Without an audit trail, you’re left guessing—was it a bug? A malicious attack? Or a data corruption? This is the reality for systems without proper audit patterns.

Without audit trails, your application risks:
- **Non-compliance** with regulations like GDPR, HIPAA, or SOX, which often require detailed tracking of data changes.
- **Unrecoverable mistakes**: In the absence of a historical record, fixing a bug or fraudulent activity can be nearly impossible.
- **Lack of trust**: Users and stakeholders rely on your system’s accuracy. Without transparency, confidence erodes.
- **Security vulnerabilities**: Malicious actors can manipulate or hide changes without detection.

Let’s explore how these challenges arise in the absence of proper audit patterns:

### Example: E-Commerce Order System
Consider an online store where users place orders. If an `Order` object is updated incorrectly (e.g., the status changes from "Pending" to "Shipped" without proper validation), here’s what happens without audits:

```javascript
// Incorrect: No audit trail or validation
const order = await Order.findById(orderId);
order.status = "Shipped"; // Who changed this? When? Why?
await order.save();
```

Now, if a dispute arises, you have no record of:
1. Who made the change?
2. When was it made?
3. What triggered the change (e.g., a button click, an API call, or an automated process)?
4. Was there any validation or authorization process before the change?

This lack of context makes it nearly impossible to resolve conflicts or ensure fairness.

---

## The Solution: Audit Patterns to the Rescue

Audit patterns provide a systematic way to track changes to your data. They answer fundamental questions like:
- What changed?
- When did it change?
- Who made the change?
- Why did it change?

There are several ways to implement audit patterns, each with tradeoffs. Below, we’ll cover the most common approaches and how to choose between them.

---

## Components/Solutions: Audit Pattern Approaches

### 1. **Separate Audit Table (Most Common)**
Store audit logs in a dedicated table alongside your main data. This is the most flexible and scalable approach.

#### Example: Audit Table Schema
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- e.g., "Order"
    entity_id INT NOT NULL,            -- foreign key to the entity
    action VARCHAR(20) NOT NULL,       -- e.g., "UPDATE", "DELETE"
    old_value JSONB,                   -- previous state (serialized)
    new_value JSONB,                   -- new state (serialized)
    changed_by INT REFERENCES users(id), -- who made the change
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB                     -- additional context (e.g., IP, request ID)
);
```

#### Pros:
- Flexible: Works for all entity types.
- Detailed: Captures full state changes.
- Queryable: You can search logs by time, user, or action.

#### Cons:
- Storage overhead: Requires additional writes.
- Complexity: Requires careful design to avoid bloating the database.

---

### 2. **Audit Columns (Simpler, but Less Detailed)**
Add columns to your main tables to track changes. This is simpler but less flexible.

#### Example: Audit Columns
```sql
ALTER TABLE orders ADD COLUMN (
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by INT REFERENCES users(id),
    previous_status VARCHAR(20)
);
```

#### Pros:
- Simple: No need for a separate table.
- Fast: No additional joins or queries.

#### Cons:
- Limited scope: Only tracks specific columns (e.g., `status`).
- Harder to query: You’d need to check `previous_status` for each record manually.

---

### 3. **Versioned Tables (Advanced)**
Use a separate table for each version of an entity. This is common in systems like Git or content management systems.

#### Example: Versioned Tables
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version INT NOT NULL DEFAULT 1  -- Track versions
);

CREATE TABLE order_versions (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    version INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by INT REFERENCES users(id)
);
```

#### Pros:
- Immutable history: You can always revert to a previous state.
- No joins needed: Each version is self-contained.

#### Cons:
- Storage overhead: Duplicates data for each version.
- Complex queries: Requires careful handling to avoid performance issues.

---

### 4. **Event Sourcing (Most Advanced)**
Instead of storing the current state, store a sequence of events. This is the most complex but powerful approach.

#### Example: Event Sourcing
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    current_state JSONB NOT NULL  -- Derived from events
);

CREATE TABLE order_events (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    event_type VARCHAR(50) NOT NULL, -- e.g., "OrderCreated", "OrderStatusUpdated"
    event_data JSONB NOT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### Pros:
- Full replayability: You can reconstruct the state at any point.
- Audit-proof: No direct data manipulation.

#### Cons:
- Complex: Requires a different architecture (e.g., projections).
- Performance overhead: Rebuilding state can be slow.

---

## Code Examples: Implementing Audit Patterns

Let’s dive into a practical example using **separate audit tables**, as it’s the most common and balanced approach. We’ll implement this in **Node.js with TypeScript** using PostgreSQL.

---

### Step 1: Define the Database Schema
First, create the `orders` and `audit_logs` tables as shown above. Here’s a complete setup using Prisma ORM:

#### `prisma/schema.prisma`
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id       Int      @id @default(autoincrement())
  name     String
  orders   Order[]
}

model Order {
  id         Int      @id @default(autoincrement())
  customerId Int
  status     String
  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt

  customer   User     @relation(fields: [customerId], references: [id])
  auditLogs  AuditLog[]
}

model AuditLog {
  id         Int      @id @default(autoincrement())
  entityType String   @default("Order")
  entityId   Int
  action     String   // "CREATE", "UPDATE", "DELETE"
  oldValue   Json?
  newValue   Json?
  changedBy  Int      @default(autoincrement())
  changedAt  DateTime @default(now())

  entity     Order    @relation(fields: [entityId], references: [id])
}
```

---

### Step 2: Create a Middleware for Auditing
We’ll create a middleware that automatically generates audit logs for all `Order` operations.

#### `src/middleware/audit.ts`
```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function audit<OrderT>(
  action: 'CREATE' | 'UPDATE' | 'DELETE',
  entityType: string,
  entityId: number,
  entityData: any,
  oldData?: any,
  changedBy?: number
) {
  const log = await prisma.auditLog.create({
    data: {
      entityType,
      entityId,
      action,
      oldValue: oldData,
      newValue: entityData,
      changedBy
    }
  });
  return log;
}
```

---

### Step 3: Override Prisma Hooks for Automatic Auditing
We’ll override Prisma’s hooks to log changes automatically.

#### `src/prisma/hooks.ts`
```typescript
import { PrismaClient } from '@prisma/client';
import { audit } from '../middleware/audit';

const prisma = new PrismaClient();

// Override Order creation
prisma.$use(async (params, next) => {
  if (params.model === 'Order' && params.action === 'create') {
    const result = await next(params);
    await audit('CREATE', 'Order', params.args.data.id, params.args.data);
    return result;
  }
  return next(params);
});

// Override Order updates
prisma.$use(async (params, next) => {
  if (params.model === 'Order' && params.action === 'update') {
    const currentData = await prisma.order.findUnique({
      where: { id: params.args.where.id as number }
    });

    const result = await next(params);
    await audit('UPDATE', 'Order', params.args.where.id as number, params.args.data, currentData);
    return result;
  }
  return next(params);
});

// Override Order deletions
prisma.$use(async (params, next) => {
  if (params.model === 'Order' && params.action === 'delete') {
    const deletedData = await prisma.order.findUnique({
      where: { id: params.args.where.id as number }
    });
    const result = await next(params);
    await audit('DELETE', 'Order', params.args.where.id as number, deletedData, deletedData);
    return result;
  }
  return next(params);
});
```

---

### Step 4: Test the Audit Flow
Let’s create a simple API endpoint to test our audit pattern.

#### `src/controllers/order.ts`
```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function createOrder(customerId: number, status: string) {
  const order = await prisma.order.create({
    data: {
      customerId,
      status
    }
  });
  return { order, message: 'Order created successfully' };
}

export async function updateOrderStatus(orderId: number, status: string) {
  const updatedOrder = await prisma.order.update({
    where: { id: orderId },
    data: { status }
  });
  return { order: updatedOrder, message: 'Order status updated' };
}

export async function deleteOrder(orderId: number) {
  const deletedOrder = await prisma.order.delete({
    where: { id: orderId }
  });
  return { order: deletedOrder, message: 'Order deleted' };
}
```

#### `src/routes/order.ts`
```typescript
import { Router } from 'express';
import { createOrder, updateOrderStatus, deleteOrder } from '../controllers/order';

const router = Router();

router.post('/orders', async (req, res) => {
  const { customerId, status } = req.body;
  const result = await createOrder(customerId, status);
  res.json(result);
});

router.put('/orders/:id/status', async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  const result = await updateOrderStatus(Number(id), status);
  res.json(result);
});

router.delete('/orders/:id', async (req, res) => {
  const { id } = req.params;
  const result = await deleteOrder(Number(id));
  res.json(result);
});

export default router;
```

---

### Step 5: Querying Audit Logs
Now, let’s write a utility to fetch audit logs for a specific order.

#### `src/services/audit.ts`
```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function getOrderAuditLogs(orderId: number) {
  const logs = await prisma.auditLog.findMany({
    where: { entityId: orderId },
    orderBy: { changedAt: 'desc' }
  });
  return logs;
}
```

#### Example Usage
```typescript
const auditLogs = await getOrderAuditLogs(1);
console.log(auditLogs);
```

Output:
```json
[
  {
    "id": 1,
    "entityType": "Order",
    "entityId": 1,
    "action": "UPDATE",
    "oldValue": { "status": "Pending" },
    "newValue": { "status": "Shipped" },
    "changedBy": 1,
    "changedAt": "2023-10-15T12:00:00Z"
  },
  {
    "id": 2,
    "entityType": "Order",
    "entityId": 1,
    "action": "CREATE",
    "newValue": { "customerId": 5, "status": "Pending" },
    "changedBy": 1,
    "changedAt": "2023-10-15T11:00:00Z"
  }
]
```

---

## Implementation Guide: Best Practices

Now that you’ve seen how to implement audit patterns, let’s discuss best practices to ensure your system is robust and maintainable.

### 1. Choose the Right Approach
- **Separate audit table**: Best for most applications. Flexible and scalable.
- **Audit columns**: Only for simple use cases where you don’t need full history.
- **Versioned tables**: Use for critical systems where immutability is key.
- **Event sourcing**: Reserved for advanced architectures like time-series data or blockchain-like systems.

### 2. Automate Auditing
- Use middleware (like we did with Prisma hooks) to avoid manual logging.
- Consider database triggers for SQL-based systems if you prefer not to rely on application logic.

### 3. Include Useful Metadata
Your audit logs should include:
- **User context**: Who made the change (e.g., `changedBy`).
- **IP address**: Where the change originated (useful for security).
- **Request ID**: For correlating logs with API requests.
- **Timestamp**: When the change occurred.
- **Action type**: CREATE, UPDATE, DELETE, or a custom action.

Example:
```json
{
  "ip": "192.168.1.1",
  "requestId": "req_123",
  "userAgent": "Postman/7.0.0"
}
```

### 4. Secure Audit Logs
- Ensure audit logs cannot be tampered with. Store them in a read-only database or immutable storage.
- Use database constraints or application logic to prevent deletions or modifications to audit logs.
- For high-security systems, consider hashing or signing logs.

### 5. Optimize Performance
- Avoid over-fetching: Only store necessary fields in audit logs.
- Use indexes on frequently queried columns (e.g., `entityId`, `changedAt`).
- Consider batching logs for high-throughput systems.

### 6. Handle Sensitive Data
- Never store sensitive data (e.g., passwords, credit card numbers) in audit logs.
- Mask or hash sensitive fields (e.g., `userId` instead of `email`).

### 7. Design for Queryability
- Allow querying logs by:
  - Entity type and ID.
  - Time range.
  - User (who made the change).
  - Action type (CREATE, UPDATE, etc.).

Example query:
```sql
SELECT * FROM audit_logs
WHERE entityType = 'Order'
  AND changedAt BETWEEN '2023-10-01' AND '2023-10-31'
  AND changedBy = 5;
```

---

## Common Mistakes to Avoid

While audit patterns are powerful, there are pitfalls to avoid:

### 1. Over-Auditing
- **Problem**: Logging every single database operation (e.g., `SELECT` queries) can bloat your logs and slow down the system.
- **Solution**: Focus on auditing only critical operations (e.g., `CREATE`, `UPDATE`, `DELETE`) on important entities.

### 2. Ignoring Performance
- **Problem**: Poorly designed audit tables can lead to slow queries or high storage costs.
- **Solution**: Use indexes, avoid storing large blobs, and consider archiving old logs.

### 3. Incomplete Audit Logs
- **Problem**: Missing fields (e.g., `changedBy`) or incomplete metadata makes logs useless.
- **Solution**: Always include essential fields like timestamps, user context, and action types.

### 4. Not Handling Edge Cases
- **Problem**: What happens when an audit log insert fails? Your application might silently fail.
- **Solution**: Implement retries or fallback mechanisms for audit logging.

### 5. Assuming All Changes Are Auditable
- **Problem**: Not all changes are visible to your