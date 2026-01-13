```markdown
---
title: "Domain-Driven Design (DDD): Building Software That Models Business Reality"
date: 2024-02-15
tags: ["backend", "design-patterns", "ddd", "database-design", "api-design"]
---

# Domain-Driven Design (DDD): Building Software That Models Business Reality

![Domain-Driven Design Diagram](https://martinfowler.com/bliki/images/ddd/context-mapping.png)
*Context Mapping in Domain-Driven Design (Martin Fowler)*

---

## Introduction

As backend engineers, we often find ourselves writing code that feels like a forced fit—methods that don’t quite match real-world concepts, data structures that don’t align with business logic, and APIs that act as translation layers between the codebase and the actual domain. This disconnect isn’t just frustrating; it leads to brittle systems that are slow to change and hard to maintain. What if we could design our software to mirror how the business actually operates?

This is the core promise of **Domain-Driven Design (DDD)**. First articulated by Eric Evans in his 2003 book *Domain-Driven Design: Tackling Complexity in the Heart of Software*, DDD is a philosophical and practical approach to software design that emphasizes modeling the core domain of a business to solve complex problems. It’s not a framework or a set of hard-and-fast rules, but a mindset that encourages collaboration between developers and domain experts to create software that feels *natural*—like an extension of the business itself.

In this post, we’ll explore what DDD is, why you’d use it, how it fits into modern backend systems, and how to apply it in real-world scenarios. We’ll look at its key components, tradeoffs, and provide practical code examples to illustrate the concepts. By the end, you’ll understand why DDD isn’t just a buzzword but a pathway to building software that’s both resilient and meaningful.

---

## The Problem: When Code Doesn’t Match Reality

Imagine you’re building an e-commerce platform. Your database has tables like `users`, `products`, and `orders`, and your API endpoints include `/users`, `/products`, and `/orders`. At first glance, this seems straightforward. But here’s the rub: the business cares about *customers*, *inventory*, and *purchases*, not just technical artifacts. The differences can seem minor, but they compound over time:

- **Misaligned Models**: Your code might model a product as just an ID, name, and price, but the business cares about attributes like weight, dimensions, and tax classifications. This creates a gap between the data and the real-world decisions.
- **Brittle Logic**: Business rules, like discounts or shipping constraints, are scattered across controllers, services, and even the database. Changing a rule requires tracing through layers of code, risking unintended side effects.
- **Poor Collaboration**: Developers and domain experts speak different languages. Developers think in CRUD operations, while domain experts think in terms of *orders*, *fulfillment*, and *returns*. Without alignment, features take longer to implement and are riddled with bugs.
- **Technical Debt**: Over time, the system becomes harder to extend. Adding a new feature (e.g., subscription plans) requires rebuilding large portions of the codebase because the design doesn’t reflect the domain.

This is the "problem of the technical layer" in DDD parlance: when software is designed around implementation concerns rather than the problem domain itself. The result is a system that’s overly complex, slow to adapt, and difficult to understand.

---

## The Solution: Aligning Code with the Business Domain

DDD’s core idea is simple: **design your software to reflect the business domain, not the technology stack**. This doesn’t mean you’ll write everything in plain English or avoid abstraction—it means you’ll collaborate with domain experts to uncover the *true* entities, relationships, and rules that govern the business, and then model them in your code and database.

DDD achieves this through a few key principles:
1. **Ubiquitous Language**: A shared vocabulary between developers and domain experts. Instead of calling it a "database record," you call it an "Order," with methods like `applyDiscount()`.
2. **Domain Models**: Objects that represent real-world concepts (e.g., `Order`, `Customer`) with behavior tied directly to them (e.g., `calculateTotal()`, `voidOrder()`).
3. **Aggregates**: Clusters of domain objects treated as a single unit for data changes. This simplifies consistency checks and transaction boundaries.
4. **Repositories**: Interfaces for storing and retrieving domain objects, decoupling domain logic from data access.
5. **Domain Services**: Operations that don’t fit neatly into a single object but are essential to the domain (e.g., `ShippingCalculator`, `DiscountEngine`).

By focusing on the domain, DDD reduces the gap between code and business reality, making the system easier to maintain and extend.

---

## Components of Domain-Driven Design

DDD organizes software around a few core concepts. Let’s explore them with practical examples.

---

### 1. **Ubiquitous Language**

A shared language between developers and domain experts ensures everyone is on the same page. Instead of terms like "entity" or "service," you use terms like "Customer," "Inventory," or "Order Status."

**Example:**
- **Bad**: Discussing a "table with a foreign key to another table."
- **Good**: Discussing how an `Order` can be *fulfilled* or *canceled*, and how inventory levels must exceed the order quantity.

**Code Example:**
Let’s say we’re modeling an e-commerce checkout flow. Instead of a generic `cartService`, we’d use terms like `ShoppingCart` and `OrderProcessing`:

```javascript
// Instead of a generic service:
class CartService {
  updateCart(userId, items) { ... }
}

// Use ubiquitous language:
class ShoppingCart {
  constructor(customerId) {
    this.customerId = customerId;
    this.items = [];
  }

  addItem(productId, quantity) {
    this.items.push({ productId, quantity });
  }

  calculateTotal() {
    return this.items.reduce((sum, item) => sum + item.quantity * item.price, 0);
  }

  checkout() {
    if (this.items.length === 0) {
      throw new Error("Cannot checkout with empty cart");
    }
    // Create order, update inventory, etc.
    return new Order(this.customerId, this.items);
  }
}
```

---

### 2. **Domain Models and Value Objects**

Domain models are objects that encapsulate behavior and data relevant to the domain. They can be **entities** (with identity) or **value objects** (without identity, defined by attributes).

**Entities** have an identity (e.g., `Order` with an `id`), while **value objects** are defined by their attributes (e.g., `Money`, `Address`).

**Code Example:**
Let’s model a `Money` value object to avoid floating-point precision issues and enforce business rules:

```javascript
class Money {
  constructor(amount, currency) {
    if (typeof amount !== "number" || amount < 0) {
      throw new Error("Amount must be a positive number");
    }
    this.amount = amount;
    this.currency = currency;
  }

  add(other) {
    if (this.currency !== other.currency) {
      throw new Error("Cannot add money with different currencies");
    }
    return new Money(this.amount + other.amount, this.currency);
  }

  // Other methods like subtract(), isGreaterThan(), etc.
}

// Usage:
const price = new Money(19.99, "USD");
const discount = new Money(5.00, "USD");
const finalPrice = price.add(discount); // Throws error if currencies differ.
```

**Value Object Example: Address**
```javascript
class Address {
  constructor(street, city, postalCode) {
    if (!street || !city || !postalCode) {
      throw new Error("Address must have all fields");
    }
    this.street = street;
    this.city = city;
    this.postalCode = postalCode;
  }

  // Equality is based on value, not reference
  equals(other) {
    return (
      this.street === other.street &&
      this.city === other.city &&
      this.postalCode === other.postalCode
    );
  }
}
```

---

### 3. **Aggregates**

An **aggregate** is a cluster of domain objects treated as a single unit for data consistency. Changes to one object in the aggregate may require changes to others, and transactions must encompass the entire aggregate.

**Example: Order Aggregate**
An `Order` is an aggregate that includes `OrderItems`, `ShippingAddress`, and `PaymentInfo`. You can’t update a single `OrderItem` without considering the entire order.

```javascript
class Order {
  constructor(orderId) {
    this.orderId = orderId;
    this.orderItems = [];
    this.shippingAddress = null;
    this.paymentInfo = null;
    this.status = "CART";
  }

  addItem(productId, quantity, price) {
    if (this.status !== "CART") {
      throw new Error("Cannot add items to a checked-out order");
    }
    this.orderItems.push({ productId, quantity, price });
  }

  checkout() {
    if (this.orderItems.length === 0) {
      throw new Error("Cannot checkout with no items");
    }
    this.status = "CHECKED_OUT";
    // Validate payment, save order, etc.
  }
}
```

**Key Points:**
- The `Order` is the **root** of the aggregate. You can’t directly modify `orderItems`; you must do so through the `Order`.
- Transactions must include the entire aggregate to maintain consistency.

---

### 4. **Repositories**

Repositories provide an interface for storing and retrieving domain objects. They abstract away data access details (e.g., SQL queries, database connection pooling).

**Example:**
```javascript
class OrderRepository {
  constructor(dbClient) {
    this.dbClient = dbClient;
  }

  async findById(orderId) {
    const [rows] = await this.dbClient.query(
      `SELECT * FROM orders WHERE id = $1`,
      [orderId]
    );
    return rows[0] ? this.hydrateOrder(rows[0]) : null;
  }

  async save(order) {
    if (order.orderId) {
      await this.dbClient.query(
        `UPDATE orders SET ... WHERE id = $1`,
        [order.orderId]
      );
    } else {
      const [result] = await this.dbClient.query(
        `INSERT INTO orders (...) VALUES (...) RETURNING id`,
        // Parameters...
      );
      order.orderId = result.rows[0].id;
    }
    return order;
  }

  // Helper to convert DB row to Order object
  hydrateOrder(row) {
    return new Order(row.id, row.status, /* other fields */);
  }
}
```

**Usage:**
```javascript
const dbClient = new DatabaseClient();
const orderRepo = new OrderRepository(dbClient);

async function processOrder(orderId) {
  const order = await orderRepo.findById(orderId);
  if (!order) throw new Error("Order not found");
  // Business logic...
  await orderRepo.save(order);
}
```

---

### 5. **Domain Services**

Domain services are operations that don’t fit neatly into a single object but are critical to the domain. Examples include `ShippingCalculator` or `DiscountEngine`.

**Example: DiscountEngine**
```javascript
class DiscountEngine {
  // Apply discounts based on customer tier, product category, etc.
  applyDiscounts(order) {
    let totalDiscount = new Money(0, order.orderItems[0].currency);

    // Apply customer tier discount
    const customerTierDiscount = this.calculateTierDiscount(order.customer);
    totalDiscount = totalDiscount.add(customerTierDiscount);

    // Apply product category discounts
    const categoryDiscounts = order.orderItems.reduce((sum, item) => {
      const categoryDiscount = this.getCategoryDiscount(item.productId);
      return sum.add(categoryDiscount);
    }, new Money(0, order.orderItems[0].currency));

    totalDiscount = totalDiscount.add(categoryDiscounts);

    return totalDiscount;
  }

  calculateTierDiscount(customer) {
    // Logic based on customer tier (e.g., silver, gold, platinum)
    // ...
  }

  getCategoryDiscount(productId) {
    // Lookup category discounts (e.g., 10% off electronics)
    // ...
  }
}
```

**Usage:**
```javascript
const discountEngine = new DiscountEngine();
const discount = discountEngine.applyDiscounts(order);
order.orderItems.forEach(item => {
  item.price = item.price.subtract(discount.divide(item.quantity));
});
```

---

## Implementation Guide: A Practical Example

Let’s walk through a complete example: modeling a **Subscription Service** for an SaaS platform. We’ll focus on:
1. Defining the domain concepts.
2. Implementing aggregates, repositories, and services.
3. Handling business rules.

---

### Step 1: Define the Domain Concepts

**Key Entities/Value Objects:**
- `Customer` (entity)
- `Subscription` (entity, part of a `SubscriptionAggregate`)
- `BillingPlan` (value object)
- `Payment` (entity)
- `Invoice` (value object)

**Domain Rules:**
1. A `Subscription` belongs to a `Customer`.
2. A `Subscription` has a `BillingPlan` (e.g., "Monthly Pro," "Annual Enterprise").
3. Payments must align with the billing cycle (e.g., no partial payments for annual plans).
4. Subscriptions can be `ACTIVE`, `CANCELED`, or `PAID_UP`.

---

### Step 2: Implement the Aggregate

The `SubscriptionAggregate` includes `Subscription` and `Payment` objects.

```javascript
class Subscription {
  constructor(customerId, billingPlan) {
    this.subscriptionId = this.generateId(); // UUID or similar
    this.customerId = customerId;
    this.billingPlan = billingPlan;
    this.status = "ACTIVE";
    this.nextBillingDate = this.calculateNextBillingDate();
    this.payments = [];
  }

  // Privately generate a unique ID
  generateId() {
    return uuidv4(); // Use a library like uuid
  }

  calculateNextBillingDate() {
    const now = new Date();
    const { interval } = this.billingPlan;
    switch (interval) {
      case "monthly":
        return new Date(now.getFullYear(), now.getMonth() + 1, 1);
      case "annual":
        return new Date(now.getFullYear() + 1, now.getMonth(), 1);
      default:
        throw new Error(`Unsupported interval: ${interval}`);
    }
  }

  recordPayment(amount, paymentDate) {
    if (this.status === "PAID_UP" || this.status === "CANCELED") {
      throw new Error("Cannot record payment for a terminated subscription");
    }

    const payment = new Payment(this.subscriptionId, amount, paymentDate);
    this.payments.push(payment);

    // Check if payment covers the next billing cycle
    if (this.isPaymentComplete(amount)) {
      this.status = "PAID_UP";
    }
  }

  isPaymentComplete(amount) {
    return amount >= this.billingPlan.price;
  }

  cancel() {
    this.status = "CANCELED";
  }

  // Other methods like getRemainingBalance(), getNextBillingDate(), etc.
}

class Payment {
  constructor(subscriptionId, amount, date) {
    this.paymentId = this.generateId();
    this.subscriptionId = subscriptionId;
    this.amount = amount;
    this.date = date;
  }

  generateId() {
    return uuidv4();
  }
}
```

---

### Step 3: Implement the Repository

```javascript
class SubscriptionRepository {
  constructor(dbClient) {
    this.dbClient = dbClient;
  }

  async findById(subscriptionId) {
    const [rows] = await this.dbClient.query(
      `SELECT * FROM subscriptions WHERE id = $1`,
      [subscriptionId]
    );
    if (rows.length === 0) return null;
    return this.hydrateSubscription(rows[0]);
  }

  async save(subscription) {
    if (subscription.subscriptionId) {
      await this.dbClient.query(
        `UPDATE subscriptions SET
          customer_id = $2,
          billing_plan = $3,
          status = $4,
          next_billing_date = $5
          WHERE id = $1`,
        [
          subscription.subscriptionId,
          subscription.customerId,
          subscription.billingPlan,
          subscription.status,
          subscription.nextBillingDate,
        ]
      );
    } else {
      const [result] = await this.dbClient.query(
        `INSERT INTO subscriptions (
          id, customer_id, billing_plan, status, next_billing_date
        ) VALUES ($1, $2, $3, $4, $5) RETURNING *`,
        [
          subscription.subscriptionId,
          subscription.customerId,
          subscription.billingPlan,
          subscription.status,
          subscription.nextBillingDate,
        ]
      );
      subscription = this.hydrateSubscription(result.rows[0]);
    }

    // Save payments
    if (subscription.payments.length > 0) {
      for (const payment of subscription.payments) {
        await this.dbClient.query(
          `INSERT INTO payments (
            id, subscription_id, amount, date
          ) VALUES ($1, $2, $3, $4)`,
          [payment.paymentId, payment.subscriptionId, payment.amount, payment.date]
        );
      }
    }

    return subscription;
  }

  hydrateSubscription(row) {
    const subscription = new Subscription(
      row.customer_id,
      new BillingPlan(row.billing_plan)
    );
    subscription.subscriptionId = row.id;
    subscription.status = row.status;
    subscription.nextBillingDate = new Date(row.next_billing_date);
    return subscription;
  }
}
```

**SQL for Tables:**
```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL,
  billing_plan JSONB NOT NULL, -- stores { price: number, interval: string, etc. }
  status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE', 'PAID_UP', 'CANCELED')),
  next_billing_date TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
  id UUID PRIMARY KEY,
  subscription_id UUID NOT NULL REFERENCES subscriptions(id),
  amount DECIMAL(10, 2) NOT NULL,
  date TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Step 4: Implement Domain Services

Let’s add a `SubscriptionService` to handle high-level operations like **updating billing plans** or **generating invoices**.

```javascript
class SubscriptionService {
  constructor(subscriptionRepo, billingPlanRepo) {
    this.subscriptionRepo = subscriptionRepo;
    this.billingPlanRepo = billingPlanRepo;
