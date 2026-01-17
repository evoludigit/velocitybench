```markdown
---
title: "Primary Key Strategy (pk_*) Pattern: Optimize B-Tree Performance Without Sacrificing Readability"
author: "Jane Doe"
date: "2023-10-15"
tags: ["database design", "api design", "backend patterns", "performance"]
description: "Learn how to use the pk_* pattern to optimize database performance with B-tree indices while maintaining clean APIs and readable URLs."
---

# Primary Key Strategy (pk_*) Pattern: Optimize B-Tree Performance Without Sacrificing Readability

## Introduction

As backend engineers, we're constantly balancing performance, readability, and maintainability in our systems. Database primary keys are one of those foundational choices that can quietly impact your system's scalability, security, and even user experience. UUIDs are universally loved for their uniqueness, but they come with a hidden cost: they don't index efficiently on traditional B-tree databases like PostgreSQL.

The **Primary Key Strategy (pk_*) pattern** addresses this by combining the best of both worlds: using optimized internal surrogate keys (like auto-incrementing integers with a prefix) for database operations while exposing UUIDs or meaningful identifiers to clients. This approach is what we call the Trinity Pattern at Fraise, where we maintain three distinct identifier types for each entity:

1. **Database native keys (pk_*)**: Internal surrogate keys optimized for B-tree indexes
2. **Client-facing UUIDs**: Secure, collision-resistant identifiers for APIs
3. **Human-readable slugs**: Clean URLs for user-facing interfaces

This blog post will focus on the internal database strategy (pk_*) and its implementation details, with practical examples for PostgreSQL that you can adapt to your projects.

---

## The Problem: Why UUIDs Aren't Always the Right Choice

Let's start with why traditional UUIDs can be problematic for database performance:

```sql
-- This query looks innocent, but it might be slow with UUID primary keys
SELECT *
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.id = '123e4567-e89b-12d3-a456-426614174000';
```

The issues are:

1. **B-tree Index Inefficiency**: UUIDs are 16 bytes long and don't follow a sequential ordering. B-tree indexes, which PostgreSQL uses by default, perform optimally with short, ordered keys.

2. **JOIN Overhead**: Joining on UUIDs requires comparing full 16-byte values, which is more expensive than comparing 4-byte integers.

3. **Index Bloat**: UUIDs cause indexes to grow faster as they're not compressed, leading to increased maintenance overhead.

4. **Memory Usage**: UUIDs consume significantly more memory than integers, affecting cache performance.

The solution lies in using optimized surrogate keys internally while maintaining UUIDs externally. Let's explore how.

---

## The Solution: The pk_* Internal Key Pattern

The pk_* pattern involves:

1. Creating a dedicated column for internal database operations (pk_*)
2. Using this for all database joins, foreign keys, and indexes
3. Generating UUIDs separately for client exposure
4. Optionally using slugs for URLs

### Database Schema Example

```sql
-- This is how we model our entities internally
CREATE TABLE users (
    pk_user_id SERIAL PRIMARY KEY,
    -- other columns...
    uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    -- slug for URLs if needed
    slug VARCHAR(255) UNIQUE NOT NULL DEFAULT ''
);
```

### Key Characteristics:

1. **B-tree Friendly**: pk_user_id is a 4-byte integer (or 8-byte for bigint) that follows a perfectly ordered sequence
2. **Small**: Virtually no storage overhead
3. **Fast**: Minimal comparison and join operations
4. **Secure**: UUID remains as a separate column, preventing any security issues from exposing internal IDs
5. **Flexible**: Easy to migrate or change internal key strategies without affecting clients

---

## Implementation Guide

Let's walk through implementing this pattern in a complete example.

### 1. Database Schema Design

```sql
-- Create tables with pk_* pattern
CREATE TABLE products (
    pk_product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE NOT NULL DEFAULT ''
);

CREATE TABLE orders (
    pk_order_id SERIAL PRIMARY KEY,
    user_pk_id INTEGER REFERENCES users(pk_user_id),
    product_pk_id INTEGER REFERENCES products(pk_product_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

-- Create indexes on the pk_* columns
CREATE INDEX idx_orders_user ON orders(user_pk_id);
CREATE INDEX idx_orders_product ON orders(product_pk_id);
```

### 2. Application Layer Implementation

Here's how you might implement this in a Node.js application with TypeORM:

```typescript
import { Entity, PrimaryGeneratedColumn, Column, OneToMany, ManyToOne } from 'typeorm';
import { v4 as uuidv4 } from 'uuid';

@Entity()
class Product {
  @PrimaryGeneratedColumn({ name: 'pk_product_id' })
  pkId: number;

  @Column()
  name: string;

  @Column()
  description: string;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price: number;

  @Column({ name: 'uuid', type: 'uuid', unique: true, nullable: false, default: () => 'gen_random_uuid()' })
  uuid: string;

  @Column({ name: 'slug', unique: true, nullable: false, default: '' })
  slug: string;

  @OneToMany(() => Order, order => order.product)
  orders: Order[];
}

@Entity()
class Order {
  @PrimaryGeneratedColumn({ name: 'pk_order_id' })
  pkId: number;

  @ManyToOne(() => User, user => user.orders)
  user: User;

  @Column({ name: 'user_pk_id' })
  userPkId: number;

  @ManyToOne(() => Product, product => product.orders)
  product: Product;

  @Column({ name: 'product_pk_id' })
  productPkId: number;

  @Column({ name: 'order_date', type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  orderDate: Date;

  @Column({ type: 'uuid', unique: true, nullable: false, default: () => 'gen_random_uuid()' })
  uuid: string;
}

@Entity()
class User {
  @PrimaryGeneratedColumn({ name: 'pk_user_id' })
  pkId: number;

  @Column({ name: 'uuid', type: 'uuid', unique: true, nullable: false, default: () => 'gen_random_uuid()' })
  uuid: string;

  @OneToMany(() => Order, order => order.user)
  orders: Order[];
}
```

### 3. Data Access Layer Examples

```typescript
// Service to get product by external UUID
async getProductByUuid(uuid: string) {
  const product = await this.productRepository.findOne({
    where: { uuid },
  });
  return {
    id: product.uuid,
    pkId: product.pkId,
    name: product.name,
    // other fields...
  };
}

// Service to create an order
async createOrder(userUuid: string, productPkId: number) {
  const user = await this.userRepository.findOne({
    where: { uuid: userUuid },
  });

  if (!user) throw new Error('User not found');

  const order = this.orderRepository.create({
    userPkId: user.pkId,
    productPkId,
  });

  return this.orderRepository.save(order);
}

// Optimized query using pk_* for joins
async getUserOrders(userUuid: string) {
  const user = await this.userRepository.findOne({
    where: { uuid: userUuid },
    relations: ['orders'],
  });

  return user.orders.map(order => ({
    orderId: order.uuid,
    productPkId: order.productPkId,
    orderDate: order.orderDate,
    // other fields...
  }));
}
```

### 4. API Response Format

Always expose UUIDs to clients while keeping pk_* internal:

```json
// Good response format
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "pkId": 12345,
  "name": "Premium Backend Course",
  "createdAt": "2023-01-15T10:30:00Z"
}
```

---

## Common Mistakes to Avoid

1. **Not Using pk_* for All Indexes**: Many developers only set up the primary key but forget to use pk_* for related tables' foreign keys. Always ensure all joins use the pk_* columns.

   ❌ Wrong:
   ```sql
   ALTER TABLE orders ADD FOREIGN KEY (user_id) REFERENCES users(id);
   ```

   ✅ Correct:
   ```sql
   ALTER TABLE orders ADD FOREIGN KEY (user_pk_id) REFERENCES users(pk_user_id);
   ```

2. **Mixing UUIDs and pk_* in Queries**: Ensure all database operations use the appropriate column type. Mixing them can lead to confusing code and potential bugs.

3. **Not Generating UUIDs on Creation**: Forgetting to set the UUID column to auto-generate causes gaps in your identifiers.

4. **Exposing pk_* in APIs**: Always mask the internal pk_* values when exposing data to clients.

5. **Using UUIDs for Primary Keys in Highly Related Tables**: For tables that are frequently joined (like orders and line_items), the performance difference between UUID and pk_* can be significant.

6. **Overusing UUIDs for Everything**: While UUIDs are great for external exposure, use them only where uniqueness is critical from an external perspective.

---

## Key Takeaways

- ✅ **Use pk_* for internal database operations** – These are optimized for B-tree performance
- ✅ **Expose UUIDs to clients** – They're secure, human-readable (to some extent), and don't impact performance
- ✅ **Add slugs for URLs** – For user-facing applications, slugs provide clean URLs
- ✅ **Always use pk_* in joins** – Never use UUIDs or external IDs in join conditions
- ✅ **Keep implementations consistent** – Apply this pattern to all entities in your application
- ✅ **Document your strategy** – Make it clear to other developers when they need to use UUIDs vs pk_*
- ⚠ **Monitor performance** – Compare index sizes and query performance before/after adoption
- ⚠ **Consider security implications** – Ensure UUIDs don't expose sensitive information
- ⚠ **Plan for migration** – If you need to change internal strategies later, pk_* makes it easier

---

## When Not to Use This Pattern

While the pk_* pattern offers many benefits, it might not be appropriate in all scenarios:

1. **Read-only systems**: If your application doesn't modify data frequently, the performance gains might not justify the complexity.

2. **Very small tables**: For tables with fewer than 10,000 rows, the performance difference is negligible.

3. **Distributed systems with sharding**: In some sharding strategies, UUIDs might be more suitable for even distribution.

4. **Systems where UUIDs are required**: Some compliance requirements mandate UUIDs as external identifiers.

5. **When clients need to know primary keys**: If your application design requires clients to reference specific records by their internal IDs, UUIDs might not be practical.

---

## Advanced Considerations

### Handling Data Migration

If you need to migrate from UUIDs to this pattern:

```sql
-- Add the pk_* column
ALTER TABLE users ADD COLUMN pk_user_id BIGSERIAL;

-- Create function to generate UUIDs if not present
CREATE OR REPLACE FUNCTION generate_uuid_if_null()
RETURNS TEXT AS $$
BEGIN
  IF NEW.uuid IS NULL THEN
    RETURN gen_random_uuid();
  ELSE
    RETURN NEW.uuid;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to set UUID on insert/update
CREATE TRIGGER set_uuid_after_insert
BEFORE INSERT ON users
FOR EACH ROW EXECUTE FUNCTION generate_uuid_if_null();

-- Add trigger to update UUID if changed
CREATE TRIGGER set_uuid_after_update
BEFORE UPDATE ON users
FOR EACH ROW WHEN (OLD.uuid IS DISTINCT FROM NEW.uuid)
EXECUTE FUNCTION generate_uuid_if_null();
```

### Index Monitoring

Monitor your indexes to ensure they're performing well:

```sql
-- Check index size
SELECT schemaname, relname, indexrelname, pg_size_pretty(pg_relation_size(amname::regclass))
FROM pg_class c
JOIN pg_index i ON (c.oid = i.indrelid)
JOIN pg_am am ON (c.relam = am.oid)
WHERE c.relkind = 'i' AND schemaname NOT IN ('pg_catalog', 'information_schema');

-- Analyze index usage
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan > 0;
```

### UUID Generation Optimization

For high-throughput systems, optimize UUID generation:

```typescript
// Better UUID generation for TypeORM
function generateUuid(): string {
  // Use crypto.randomUUID in Node.js or similar in other environments
  const uuid = crypto.randomUUID();
  return uuid;
}

// Or use a PostgreSQL function for maximum performance
CREATE OR REPLACE FUNCTION generate_random_uuid()
RETURNS uuid AS $$
DECLARE
  uuid_val UUID;
BEGIN
  uuid_val := uuid_generate_v4();
  RETURN uuid_val;
END;
$$ LANGUAGE plpgsql;
```

---

## Conclusion

The pk_* primary key strategy offers a practical middle ground between performance optimization and maintainability. By using optimized internal keys for database operations while exposing UUIDs and human-readable identifiers to clients, you get the best of both worlds: fast database operations and clean external interfaces.

The key benefits are:

- **Performance**: Faster queries, smaller indexes, and more efficient joins
- **Security**: Internal IDs are masked from clients
- **Flexibility**: Easy to change internal strategies without affecting clients
- **Readability**: Clean URLs and external identifiers for user-facing systems

As with any design pattern, the pk_* strategy works best when applied consistently across your entire system. Start small—implement it for your most performance-sensitive tables first—and gradually expand it to other parts of your application.

Remember that database design is about tradeoffs. UUIDs provide uniqueness at the cost of performance, while pk_* provides performance at the cost of slightly less "human-friendly" identifiers. The pk_* pattern lets you have both when you need them.

Try implementing this pattern in your next project, and you'll likely see measurable improvements in your database performance while maintaining clean application interfaces.

---
```

This blog post provides a comprehensive, practical guide to implementing the pk_* pattern while addressing common questions and concerns about its usage.