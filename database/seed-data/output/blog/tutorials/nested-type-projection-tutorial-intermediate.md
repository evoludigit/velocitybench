---
title: "Nested Type Projection: Mastering Multi-Level Data Transformation in APIs"
date: "2023-11-15"
author: "Alex Carter"
---

# **Nested Type Projection: Mastering Multi-Level Data Transformation in APIs**

Are you tired of writing repetitive DTO (Data Transfer Object) mappings for nested data structures? Do your APIs send bloated responses that clients rarely use? If so, you’re not alone.

Modern applications often return multi-level data structures, whether fetching user profiles with nested addresses, orders with line items, or complex business hierarchies. Traditional one-to-one mapping approaches lead to verbose code, performance bottlenecks, and over-fetching. **Nested Type Projection** is a design pattern that elegantly solves these problems by dynamically shaping complex data into API-friendly structures.

In this tutorial, we’ll explore practical ways to implement nested type projection in TypeScript (with TypeORM and Prisma examples) and SQL-based applications. You’ll learn how to minimize database rounds trips, reduce payload sizes, and keep your codebase clean.

---

## **The Problem: Why Nested Data is a Nightmare**

Let’s start with a real-world scenario. Suppose we have an **e-commerce platform** where users place orders containing multiple line items. A naive REST API might fetch this data like this:

```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "address": {
      "street": "123 Main St",
      "city": "New York"
    }
  },
  "order": {
    "id": 101,
    "items": [
      {
        "product": {
          "id": 1,
          "name": "Premium Headphones"
        },
        "quantity": 2,
        "price": 199.99
      },
      {
        "product": {
          "id": 2,
          "name": "Wireless Charger"
        },
        "quantity": 1,
        "price": 49.99
      }
    ]
  }
}
```

### **The Challenges:**
1. **Over-Fetching:** The client may only need the user’s name and order items, but the API still sends the full user and product details.
2. **N+1 Query Problem:** If the API loads user, order, and product in separate queries, performance degrades.
3. **Complex DTOs:** You end up writing repetitive DTO classes for every possible nested structure.
4. **Tight Coupling:** Changes in the database schema force changes in API contracts.

### **The Ripple Effect**
- **Performance:** Slow APIs lead to poor user experience.
- **Maintainability:** Hard-coded paths make refactoring difficult.
- **Scalability:** Inefficient data transfer wastes bandwidth.

---

## **The Solution: Nested Type Projection**

**Nested Type Projection** is a design pattern that dynamically shapes nested database records into lightweight API responses. Instead of hard-coding DTOs for every possible query, we define **projection rules** that determine which fields to include, transform, or nest.

### **Core Principles:**
1. **Selective Projection:** Only include fields the client needs.
2. **Lazy Loading:** Avoid fetching unnecessary data upfront.
3. **Flexible Transformations:** Apply filters, aggregations, or custom logic.
4. **Consistent Contracts:** Use interfaces to enforce API shapes.

---

## **Components of Nested Type Projection**

To implement this pattern, we need:

1. **Projection Interfaces** – Define the shape of the API response.
2. **Query Builders** – Dynamically construct database queries with projections.
3. **Transformers** – Convert raw database records into structured responses.
4. **Caching Layer (Optional)** – For frequently accessed nested data.

---

## **Code Examples: Implementing Nested Type Projection**

We’ll demonstrate this in **TypeScript with TypeORM** (ORM) and **Prisma** (query builder). Both follow similar principles but have unique syntax.

---

### **1. TypeORM Example (Active Record + Query Builder)**

#### **Database Schema**
```typescript
// user.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, OneToMany } from 'typeorm';
import { Address } from './address.entity';
import { Order } from './order.entity';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;

  @Column()
  email: string;

  @OneToMany(() => Order, order => order.user)
  orders: Order[];
}
```

```typescript
// address.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, ManyToOne } from 'typeorm';
import { User } from './user.entity';

@Entity()
export class Address {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  street: string;

  @Column()
  city: string;

  @ManyToOne(() => User, user => user.addresses)
  user: User;
}
```

```typescript
// order.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, OneToMany } from 'typeorm';
import { User } from './user.entity';
import { OrderItem } from './order-item.entity';

@Entity()
export class Order {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  total: number;

  @ManyToOne(() => User, user => user.orders)
  user: User;

  @OneToMany(() => OrderItem, item => item.order)
  items: OrderItem[];
}
```

```typescript
// order-item.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, ManyToOne } from 'typeorm';
import { Order } from './order.entity';
import { Product } from './product.entity';

@Entity()
export class OrderItem {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  quantity: number;

  @Column('decimal')
  price: number;

  @ManyToOne(() => Order, order => order.items)
  order: Order;

  @ManyToOne(() => Product, product => product.orderItems)
  product: Product;
}
```

```typescript
// product.entity.ts
@Entity()
export class Product {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;

  @Column('decimal')
  price: number;
}
```

#### **Projection Interface**
Define the shape of the API response:
```typescript
// projections.ts
export interface UserProjection {
  id: number;
  name: string;
  email: string;
  address?: AddressProjection;
}

export interface AddressProjection {
  city: string;
  street: string;
}

export interface OrderProjection {
  id: number;
  total: number;
  items: OrderItemProjection[];
}

export interface OrderItemProjection {
  product: {
    id: number;
    name: string;
  };
  quantity: number;
  price: number;
}
```

#### **Transformer Function**
Convert raw entities into projections:
```typescript
// transformers.ts
export function transformUserProjection(user: User, includeAddress = false): UserProjection {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    ...(includeAddress && {
      address: {
        city: user.address?.city,
        street: user.address?.street,
      },
    }),
  };
}

export function transformOrderProjection(order: Order): OrderProjection {
  return {
    id: order.id,
    total: order.total,
    items: order.items.map(item => ({
      product: {
        id: item.product.id,
        name: item.product.name,
      },
      quantity: item.quantity,
      price: item.price,
    })),
  };
}
```

#### **Query Builder with Projections**
Use TypeORM’s query builder to fetch only the required fields:
```typescript
// api.ts
import { getRepository } from 'typeorm';
import { UserProjection, OrderProjection } from './projections';
import { transformUserProjection, transformOrderProjection } from './transformers';

export async function getUserWithOrderProjection(
  userId: number
): Promise<{ user: UserProjection; order?: OrderProjection }> {
  const userRepo = getRepository(User);
  const orderRepo = getRepository(Order);

  // Fetch user with selected fields
  const user = await userRepo
    .createQueryBuilder('user')
    .select(['user.id', 'user.name', 'user.email'])
    .leftJoinAndSelect('user.address', 'address')
    .where('user.id = :id', { id: userId })
    .getOne();

  if (!user) throw new Error('User not found');

  // Fetch only the required order data
  const order = await orderRepo
    .createQueryBuilder('order')
    .select([
      'order.id',
      'order.total',
      'order.items.id as itemId',
      'order.items.quantity as itemQuantity',
      'order.items.price as itemPrice',
      'item.product.id as productId',
      'item.product.name as productName',
    ])
    .innerJoin('order.items', 'item')
    .innerJoin('item.product', 'product')
    .where('order.userId = :userId', { userId })
    .getOne();

  return {
    user: transformUserProjection(user, true),
    order: order ? transformOrderProjection(order) : undefined,
  };
}
```

#### **Usage in an API Route**
```typescript
// server.ts
import express from 'express';
import { getUserWithOrderProjection } from './api';

const app = express();

app.get('/users/:id', async (req, res) => {
  try {
    const result = await getUserWithOrderProjection(parseInt(req.params.id));
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

**Response Example:**
```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "address": {
      "city": "New York",
      "street": "123 Main St"
    }
  },
  "order": {
    "id": 101,
    "total": 349.97,
    "items": [
      {
        "product": {
          "id": 1,
          "name": "Premium Headphones"
        },
        "quantity": 2,
        "price": 199.99
      },
      {
        "product": {
          "id": 2,
          "name": "Wireless Charger"
        },
        "quantity": 1,
        "price": 49.99
      }
    ]
  }
}
```

---

### **2. Prisma Example (GraphQL + REST)**

Prisma makes nested projections even easier with its **`include`** and **`select`** clauses.

#### **Schema Definition**
```prisma
// schema.prisma
model User {
  id      Int     @id @default(autoincrement())
  name    String
  email   String
  address Address?
  orders  Order[]

  @@map("users")
}

model Address {
  id      Int     @id @default(autoincrement())
  street  String
  city    String
  user    User    @relation(fields: [userId], references: [id])

  userId  Int

  @@map("addresses")
}

model Order {
  id        Int     @id @default(autoincrement())
  total     Float
  user      User    @relation(fields: [userId], references: [id])
  items     OrderItem[]

  userId    Int
  createdAt DateTime @default(now())

  @@map("orders")
}

model OrderItem {
  id        Int     @id @default(autoincrement())
  quantity  Int
  price     Float
  order     Order   @relation(fields: [orderId], references: [id])
  product   Product @relation(fields: [productId], references: [id])

  orderId   Int
  productId Int

  @@map("order_items")
}

model Product {
  id    Int     @id @default(autoincrement())
  name  String
  price Float

  @@map("products")
}
```

#### **Projection Queries**
```typescript
// prisma.service.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function getUserWithOrderProjection(
  userId: number
): Promise<{
  user: {
    id: number;
    name: string;
    email: string;
    address?: { city: string; street: string };
  };
  order?: {
    id: number;
    total: number;
    items: Array<{
      product: { id: number; name: string };
      quantity: number;
      price: number;
    }>;
  };
}> {
  return prisma.user
    .findUnique({
      where: { id: userId },
      include: {
        address: {
          select: { city: true, street: true },
        },
        orders: {
          where: { id: 101 }, // Filter specific order
          include: {
            items: {
              include: {
                product: {
                  select: { id: true, name: true },
                },
              },
              select: { quantity: true, price: true },
            },
          },
          select: { id: true, total: true },
        },
      },
    })
    .then(result => ({
      user: {
        id: result.id,
        name: result.name,
        email: result.email,
        ...(result.address && {
          address: {
            city: result.address.city,
            street: result.address.street,
          },
        }),
      },
      order: result.orders?.length
        ? {
            id: result.orders[0].id,
            total: result.orders[0].total,
            items: result.orders[0].items.map(item => ({
              product: { id: item.product.id, name: item.product.name },
              quantity: item.quantity,
              price: item.price,
            })),
          }
        : undefined,
    }));
}
```

#### **API Route**
```typescript
// server.ts
import express from 'express';
import { getUserWithOrderProjection } from './prisma.service';

const app = express();

app.get('/users/:id', async (req, res) => {
  const result = await getUserWithOrderProjection(parseInt(req.params.id));
  res.json(result);
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

---

## **Implementation Guide**

### **Step 1: Define Projection Interfaces**
Start by documenting the expected API response shapes. Use TypeScript interfaces to enforce consistency.

### **Step 2: Selective Field Loading**
Use ORM/query builder to fetch only the fields you need:
- TypeORM: `select()` clause.
- Prisma: `select()` clause.
- SQL: Explicit column selection.

### **Step 3: Nesting with `include`/`join`**
- For relationships, use `include` (Prisma) or manual joins (TypeORM/SQL).
- Avoid full joins when possible; prefer left joins with optional fields.

### **Step 4: Transform Data with Mappers**
Write transformation functions to convert raw entities into projections. Use `map` for collections.

### **Step 5: Handle Edge Cases**
- Missing optional fields (e.g., `address`).
- Lazy-loaded relationships (avoid N+1 queries).

### **Step 6: Cache Frequently Accessed Data**
Use Redis or a database cache to store pre-computed nested projections.

---

## **Common Mistakes to Avoid**

### **1. Over-Fetching**
- **Problem:** Fetching entire entities when only a few fields are needed.
- **Solution:** Always use `select()` clauses to limit fields.

### **2. N+1 Query Problems**
- **Problem:** Loading parent entities and then each child in separate queries.
- **Solution:** Use `include` (Prisma) or eager loads (TypeORM).

### **3. Ignoring Performance**
- **Problem:** Complex joins or aggregations slow down queries.
- **Solution:** Test with `EXPLAIN` and optimize.

### **4. Hard-Coded Paths**
- **Problem:** Magic strings like `'user.addr.street'` make code hard to maintain.
- **Solution:** Use interfaces and transformers.

### **5. Over-Abstraction**
- **Problem:** Writing complex transformers for simple cases.
- **Solution:** Start simple; optimize later.

---

## **Key Takeaways**

✅ **Selective Projection** – Only fetch what you need.
✅ **Lazy Loading** – Avoid N+1 queries with eager loads.
✅ **Projection Interfaces** – Define clear API contracts.
✅ **Transformers** – Separate entity conversion logic.
✅ **ORM/Query Builder Power** – Leverage tools like TypeORM and Prisma.
✅ **Caching** – Speed up frequent nested queries.

---

## **Conclusion**

Nested Type Projection is a powerful pattern for managing complex data in APIs. By combining **selective field loading**, **eager joins**, and **clean transformations**, you can reduce payload sizes, improve performance, and keep your code maintainable.

### **Next Steps**
- Experiment with **GraphQL** (which natively supports nested projections).
- Explore **GraphQL Data Loaders** for batching nested queries.
- Consider **Event Sourcing** for audit-friendly nested data.

Would you like a follow-up post on **GraphQL vs. REST with Nested Projection**? Let me know in the comments!

---
**Happy coding!** 🚀