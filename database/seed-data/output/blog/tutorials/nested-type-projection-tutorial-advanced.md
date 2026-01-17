```markdown
---
title: "Nested Type Projection: How to Restructure Complex Data Efficiently in Modern APIs"
date: 2024-05-20
tags: ["database", "API design", "backend engineering", "data projection", "TypeScript", "SQL", "REST", "GraphQL"]
author: "Alex Carter"
---

# **Nested Type Projection: How to Restructure Complex Data Efficiently in Modern APIs**

When building APIs that serve rich, multi-level data, you’ll eventually hit a wall: responses must either be **verbose** (dumping everything) or **fragmented** (requiring multiple calls), both of which hurt performance and developer experience. The **Nested Type Projection** pattern solves this by mapping relational database schemas into **nested API responses** that mirror real-world data hierarchies—without bloating payloads or overloading databases.

This pattern is especially valuable when working with:
- **Hierarchical data** (e.g., user profiles with nested addresses, orders with line items).
- **Composite entities** (e.g., a `Product` with related `Inventory` and `Reviews`).
- **APIs with strict transfer-size limits** (e.g., mobile apps, IoT devices).

The key insight? You’re not just writing a query—you’re **designing a data contract** that balances efficiency with usability.

---

## **The Problem: Why Nested Data Sucks Without Projection**

Consider a typical e-commerce system with these tables:

```sql
-- Users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100)
);

-- Addresses (belong to users)
CREATE TABLE addresses (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  street VARCHAR(200),
  city VARCHAR(100),
  state VARCHAR(100)
);

-- Orders (belong to users)
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  total DECIMAL(10, 2),
  status VARCHAR(20)
);

-- Order Items (belong to orders)
CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(id),
  product_id INT,
  quantity INT,
  unit_price DECIMAL(10, 2)
);
```

### **Option 1: Flat Response (No Nesting)**
```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  },
  "addresses": [
    { "id": 101, "street": "123 Main St", "city": "Boston", "state": "MA" },
    { "id": 102, "street": "456 Oak Ave", "city": "Boston", "state": "MA" }
  ],
  "orders": [
    {
      "id": 1001,
      "user_id": 1,
      "total": 150.00,
      "status": "completed",
      "items": [
        { "id": 5001, "product_id": 1, "quantity": 2, "unit_price": 75.00 }
      ]
    }
  ]
}
```
**Problems:**
- **Over-fetching**: The client may not need `addresses` or `items`.
- **Under-fetching**: The client might need more details (e.g., `product_name` in `order_items`).
- **No clear boundaries**: The response looks like a denormalized blob rather than a structured API.

### **Option 2: Multiple API Calls (Decomposition)**
```http
GET /users/1
GET /users/1/addresses
GET /users/1/orders
GET /users/1/orders/1001/items
```
**Problems:**
- **Latency**: Multiple round trips.
- **Complexity**: Clients must stitch responses manually (often using state machines or caching layers).
- **Inconsistent data**: If `orders` changes between calls, the client may see stale data.

---
## **The Solution: Nested Type Projection**

Instead of forcing a flat or fragmented approach, **Nested Type Projection** defines a **deliberate hierarchy** in your API responses that:
1. **Mirrors real-world relationships** (e.g., `User` → `Orders` → `Items`).
2. **Avoids over-fetching** by embedding only what’s needed.
3. **Reduces latency** by fetching related data in a single call.

### **Key Principles**
- **Projection as a contract**: Your API defines what nested responses look like, not just raw data.
- **Selective inclusion**: Clients can request shallow or deep nesting (e.g., `?include=orders.items`).
- **Lazy loading for pagination**: Deeply nested data can be paginated or loaded on demand.

---

## **Code Examples: Implementing Nested Projection**

We’ll use **TypeScript + Express** (Node.js) with **PostgreSQL** for examples. The goal: return a `User` with nested `Orders` and `Items`.

### **1. Database Schema (PostgreSQL)**
```sql
-- Users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100)
);

-- Orders (with JSONB for flexible nesting)
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  total DECIMAL(10, 2),
  status VARCHAR(20),
  metadata JSONB  -- For extensibility
);

-- Order Items
CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(id),
  product_id INT,
  quantity INT,
  unit_price DECIMAL(10, 2),
  product_name VARCHAR(100)  -- Simulating joined data
);
```

### **2. Type Definitions (TypeScript)**
```typescript
// src/types/user.types.ts
export interface Address {
  id: number;
  street: string;
  city: string;
  state: string;
}

export interface OrderItem {
  id: number;
  productId: number;
  productName: string;
  quantity: number;
  unitPrice: number;
}

export interface Order {
  id: number;
  total: number;
  status: string;
  items: OrderItem[];
}

export interface UserProjection {
  id: number;
  name: string;
  email: string;
  addresses: Address[];
  orders?: Order[];  // Optional; clients can omit with ?include=orders
}
```

### **3. SQL Query with JSON Aggregation (PostgreSQL)**
To fetch a `User` with nested `Orders` and `Items`, use PostgreSQL’s `JSONB_AGG` and `JSONB_BUILD_OBJECT`:

```sql
WITH user_data AS (
  SELECT
    u.id, u.name, u.email,
    jsonb_agg(a) AS addresses
  FROM users u
  LEFT JOIN addresses a ON u.id = a.user_id
  WHERE u.id = $1
  GROUP BY u.id, u.name, u.email
),
order_data AS (
  SELECT
    o.id, o.total, o.status,
    jsonb_agg(
      JSONB_BUILD_OBJECT(
        'id', oi.id,
        'product_id', oi.product_id,
        'product_name', oi.product_name,
        'quantity', oi.quantity,
        'unit_price', oi.unit_price
      )
    ) AS items
  FROM orders o
  LEFT JOIN order_items oi ON o.id = oi.order_id
  WHERE o.user_id = $1
  GROUP BY o.id, o.total, o.status
)
SELECT
  ud.*,
  jsonb_agg(
    JSONB_BUILD_OBJECT(
      'id', od.id,
      'total', od.total,
      'status', od.status,
      'items', od.items
    )
  ) AS orders
FROM user_data ud
LEFT JOIN order_data od ON true
WHERE ud.id = $1
GROUP BY ud.id, ud.name, ud.email, ud.addresses;
```

### **4. API Implementation (Express + TypeScript)**
```typescript
// src/controllers/user.controller.ts
import { Request, Response } from 'express';
import { UserProjection } from '../types/user.types';

export const getUserWithNestedData = async (req: Request, res: Response) => {
  const { id } = req.params;
  const includeOrders = req.query.include === 'orders';

  try {
    const query = `
      WITH user_data AS (
        SELECT
          u.id, u.name, u.email,
          jsonb_agg(a) AS addresses
        FROM users u
        LEFT JOIN addresses a ON u.id = a.user_id
        WHERE u.id = $1
        GROUP BY u.id, u.name, u.email
      ),
      order_data AS (
        SELECT
          o.id, o.total, o.status,
          jsonb_agg(
            JSONB_BUILD_OBJECT(
              'id', oi.id,
              'product_id', oi.product_id,
              'product_name', oi.product_name,
              'quantity', oi.quantity,
              'unit_price', oi.unit_price
            )
          ) AS items
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = $1
        GROUP BY o.id, o.total, o.status
      )
      SELECT
        ud.*,
        jsonb_agg(
          JSONB_BUILD_OBJECT(
            'id', od.id,
            'total', od.total,
            'status', od.status,
            'items', od.items
          )
        ) AS orders
      FROM user_data ud
      LEFT JOIN order_data od ON true
      WHERE ud.id = $1
      GROUP BY ud.id, ud.name, ud.email, ud.addresses
    `;

    const result = await db.query(query, [id]);

    if (!result.rows.length) {
      return res.status(404).send({ error: 'User not found' });
    }

    const userData = result.rows[0];
    const response: UserProjection = {
      id: userData.id,
      name: userData.name,
      email: userData.email,
      addresses: userData.addresses,
      orders: includeOrders ? userData.orders : undefined,
    };

    res.json(response);
  } catch (err) {
    console.error(err);
    res.status(500).send({ error: 'Server error' });
  }
};
```

### **5. API Endpoint**
```typescript
// src/routes/user.routes.ts
import express from 'express';
import { getUserWithNestedData } from '../controllers/user.controller';

const router = express.Router();

router.get('/users/:id', getUserWithNestedData);
router.get('/users/:id?include=orders', getUserWithNestedData);  // Optional nesting

export default router;
```

### **6. Client-Side Usage**
```typescript
// Example GET request with optional nesting
fetch(`/users/1?include=orders`)
  .then(res => res.json())
  .then((data: UserProjection) => {
    console.log(data);
// Output:
// {
//   id: 1,
//   name: "Alice",
//   email: "alice@example.com",
//   addresses: [...],
//   orders: [  // Only included due to ?include=orders
//     {
//       id: 1001,
//       total: 150.00,
//       status: "completed",
//       items: [ ... ]
//     }
//   ]
// }
```

---

## **Implementation Guide**

### **Step 1: Define Your Projection Types**
- Start with your database schema, then **redesign for API consumption**.
- Use TypeScript (or similar) to enforce nested structures.

### **Step 2: Choose a Database Approach**
| Strategy               | Pros                          | Cons                          | Best For                  |
|------------------------|-------------------------------|-------------------------------|---------------------------|
| **JSON/JSONB fields**  | Flexible, no schema changes   | Harder to query               | Polyglot persistence      |
| **Materialized views** | Pre-computed, efficient       | Stale if data changes         | Read-heavy workloads      |
| **Graph databases**    | Native nesting support        | Overkill for relational data  | Complex hierarchies       |

### **Step 3: Handle Optional Nesting**
- Use query parameters (`?include=orders`) or headers (`Accept: application/vnd.api.v1+json`).
- Example in Express:
  ```typescript
  const includeOrders = req.query.include?.includes('orders');
  ```

### **Step 4: Optimize for Performance**
- **Index foreign keys** (e.g., `CREATE INDEX ON orders(user_id)`).
- **Limit nesting depth** (e.g., only include 1 level of `items` by default).
- **Use pagination** for deep nesting (e.g., `?limit=5&offset=0`).

### **Step 5: Version Your Projections**
- API changes should **not break clients**. Example:
  ```typescript
  // v1: Minimal nesting
  {
    user: { id, name },
    orders: [{ id, total }]
  }

  // v2: Deep nesting (backward-compatible)
  {
    user: { id, name },
    orders: [
      {
        id,
        total,
        items: [{ product_name, quantity }] // New field
      }
    ]
  }
  ```

---

## **Common Mistakes to Avoid**

### **1. Over-Nesting Without Boundaries**
- **Bad**: Returning the entire database graph in one call.
- **Good**: Document maximum nesting depth (e.g., `User → Orders → Items (1 level)`).

### **2. Ignoring Query Performance**
- **Bad**: Joining 10 tables without indexes.
- **Good**: Pre-aggregate nested data (e.g., `JSONB_AGG` in PostgreSQL).

### **3. Not Handling Circular References**
- **Bad**: Nested responses with `A → B → A` loops.
- **Good**: Flatten or use `id` references (e.g., `{ id: 1, parent_id: 2 }`).

### **4. Forgetting Caching**
- **Bad**: Recomputing nested data for every request.
- **Good**: Cache projections (Redis) with TTLs.

### **5. Overcomplicating with GraphQL**
- **Bad**: Using GraphQL for everything just to support nesting.
- **Good**: Use REST for simple nesting, GraphQL for ad-hoc queries.

---

## **Key Takeaways**
- **Nested Projection = API Shape ≠ Database Shape**: Redesign for consumption, not storage.
- **Balance control and flexibility**: Let clients request shallow or deep nesting.
- **Database-aware design**: Use JSON/JSONB or materialized views for efficiency.
- **Document your projections**: Treat them as part of your API contract.
- **Avoid silos**: Reuse nested types across endpoints (e.g., `Order` in `GET /users` and `GET /orders`).

---

## **Conclusion: When to Use Nested Projection**

Nested Type Projection shines when:
✅ You have **multi-level relationships** (e.g., `User → Orders → Items`).
✅ Clients need **consistent data models** (e.g., mobile apps).
✅ You want to **reduce latency** compared to N+1 queries.

Avoid it when:
❌ Your data is **flat** (e.g., key-value stores).
❌ Clients need **highly dynamic shapes** (use GraphQL instead).

### **Next Steps**
1. **Experiment**: Start with a single nested endpoint (e.g., `GET /users/{id}?include=orders`).
2. **Measure**: Compare latency and payload size vs. decomposed APIs.
3. **Iterate**: Refine based on client feedback.

By treating nested projections as a **first-class design choice**, you’ll build APIs that feel **intuitive** and perform **efficiently**—without sacrificing flexibility.

---
### **Further Reading**
- [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [REST API Design Best Practices](https://restfulapi.net/)
- [GraphQL vs. REST for Nested Data](https://www.howtographql.com/basics/1-graphql-is-the-better-rest/)
```