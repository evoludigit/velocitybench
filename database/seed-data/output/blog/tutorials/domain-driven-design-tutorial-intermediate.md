```markdown
---
title: "Domain-Driven Design (DDD): Building Backend Systems That Align with Business Logic"
meta:
  description: Learn how Domain-Driven Design (DDD) helps structure your backend code to match real-world business problems. Practical examples, tradeoffs, and implementation tips for intermediate backend engineers.
  keywords: Domain-Driven Design, DDD, backend architecture, microservices, business logic, software patterns, event sourcing, CQRS, clean architecture
author: Jane Doe
date: 2023-11-15
---

# Domain-Driven Design (DDD): Building Backend Systems That Align with Business Logic

If you've ever stared at a monolithic database schema or felt your API endpoints were more like "RESTful" than "business logic," then Domain-Driven Design (DDD) might be just what you need. DDD isn't just another buzzword—it's a mindset that helps backend engineers build systems that genuinely reflect how businesses *actually* operate.

In this post, we’ll explore DDD through the lens of real-world backend engineering. You’ll see how to structure your code so that it mirrors business problems, not just technical abstractions. We’ll cover core concepts, practical examples, and the tradeoffs you should weigh before diving in.

---

## The Problem: When Your Code Doesn’t Match the Business

Most backend systems start with data. We create databases, design schemas, and build APIs to expose that data. But here’s the catch: **data and business logic are often mismatched**.

### Why Mismatch Happens
1. **API-Driven Design**: You design endpoints first (`/users/{id}/orders`) instead of starting with business concepts.
2. **Database-Centric**: Your tables (`users`, `orders`) reflect technical concerns (normalization, keys) rather than business objects (Customer, Order).
3. **Silos of Knowledge**: Business rules (e.g., "Premium customers get free shipping") are sprinkled across controllers, services, and database triggers, making them hard to maintain.

### The Consequences
- **Tight Coupling**: Changes to business rules require rewrites across the entire system.
- **Poor Testability**: Business logic hidden in repositories or scattered controllers is hard to unit test.
- **Scaling Nightmares**: When you split your monolith into microservices, you’ve already defined boundaries around technical concerns, not business domains.

### Example: The E-Commerce Nightmare
Imagine an e-commerce system where:
- Inventory is managed by a `ProductRepository`.
- Orders are handled by an `OrderService` that interacts with the `ProductRepository`.
- Discounts are applied in a controller based on hardcoded rules.

Now, the business decides to introduce **Subscription Plans** (e.g., "Pay monthly and get 10% off"). Suddenly, your `OrderService` needs to know about subscriptions, and your `ProductRepository` might need to track user tiers. The system becomes a tangled mess of dependencies.

---

## The Solution: DDD Aligns Code with Business

Domain-Driven Design (DDD) is a strategic approach to software development that focuses on modeling the core business logic and expressing that logic directly in code. It emphasizes three key ideas:

1. **Domain Models**: Objects that represent real-world business concepts (e.g., `Customer`, `Order`, `SubscriptionPlan`).
2. **Bounded Contexts**: Clear boundaries within which a domain model is valid and consistent.
3. **Ubiquitous Language**: A shared vocabulary between developers and domain experts to reduce ambiguity.

### Key DDD Concepts in Backend Engineering
| Concept               | Backend Implications                                                                 |
|-----------------------|--------------------------------------------------------------------------------------|
| **Aggregate Roots**   | Define data consistency boundaries (e.g., an `Order` can’t be split across services). |
| **Repositories**      | Persistence-agnostic interfaces to interact with aggregates (e.g., `OrderRepository`).  |
| **Services**          | Pure functions or stateless operations that don’t hold state (e.g., `DiscountCalculator`). |
| **Events**            | Domain events (e.g., `OrderPlaced`, `PaymentFailed`) to drive asynchronous workflows.   |

---

## Practical Example: E-Commerce with DDD

Let’s refactor the e-commerce system using DDD. We’ll focus on the **Order Processing** domain.

### 1. Define the Domain Model

First, we model the business concepts *as they’re understood by stakeholders*:
- A `Customer` has a `SubscriptionPlan`.
- An `Order` contains `OrderItems` and has a `Status`.
- Discounts are applied based on the customer’s subscription.

#### Domain Classes (TypeScript Example)
```typescript
// Domain models (business logic lives here)
class SubscriptionPlan {
  constructor(
    public id: string,
    public name: string,
    public discountPercentage: number,
  ) {}
}

class Customer {
  constructor(
    public id: string,
    public name: string,
    public subscriptionPlan: SubscriptionPlan,
  ) {}

  getDiscount(): number {
    return this.subscriptionPlan.discountPercentage;
  }
}

class OrderItem {
  constructor(
    public productId: string,
    public quantity: number,
    public unitPrice: number,
  ) {}

  getTotal(): number {
    return this.quantity * this.unitPrice;
  }
}

class Order {
  private _status: OrderStatus = OrderStatus.Pending;
  private _items: OrderItem[] = [];

  constructor(
    public id: string,
    public customer: Customer,
    public items: OrderItem[],
  ) {
    this._items = items;
  }

  addItem(item: OrderItem): void {
    this._items.push(item);
  }

  calculateSubtotal(): number {
    return this._items.reduce((sum, item) => sum + item.getTotal(), 0);
  }

  calculateTotal(): number {
    const subtotal = this.calculateSubtotal();
    return subtotal * (1 - this.customer.getDiscount());
  }

  // Business logic: transition to "Paid" status
  pay(): void {
    if (this._status !== OrderStatus.Pending) {
      throw new Error("Order is not pending");
    }
    this._status = OrderStatus.Paid;
    // Emit domain event
    this.on("OrderPaid", {
      orderId: this.id,
      amount: this.calculateTotal(),
      customerId: this.customer.id,
    });
  }

  // Example of emitting a domain event
  private emit<T extends string>(eventName: T, payload: any): void {
    console.log(`Domain Event: ${eventName}`, payload);
  }
}

enum OrderStatus {
  Pending = "Pending",
  Paid = "Paid",
  Shipped = "Shipped",
  Cancelled = "Cancelled",
}
```

### 2. Repository Pattern for Persistence

Repositories decouple domain models from persistence. Here’s how we’d define them:

```typescript
// Repository interfaces (abstraction)
interface OrderRepository {
  findById(id: string): Promise<Order>;
  save(order: Order): Promise<void>;
  // Other CRUD methods...
}

interface CustomerRepository {
  findById(id: string): Promise<Customer>;
  // Other methods...
}

// Implementation (e.g., using TypeORM)
class TypeOrmOrderRepository implements OrderRepository {
  private readonly orderRepository: EntityRepository<OrderEntity>;

  constructor(orderRepository: EntityRepository<OrderEntity>) {
    this.orderRepository = orderRepository;
  }

  async findById(id: string): Promise<Order> {
    const entity = await this.orderRepository.findOne({ id });
    return this.fromEntity(entity);
  }

  async save(order: Order): Promise<void> {
    const entity = this.toEntity(order);
    await this.orderRepository.save(entity);
  }

  // Helper methods to convert between domain and entity
  private fromEntity(entity: OrderEntity): Order {
    // Map database fields to domain objects
    return new Order(
      entity.id,
      new Customer(entity.customerId, entity.customerName, new SubscriptionPlan(
        entity.subscriptionPlanId,
        entity.subscriptionPlanName,
        entity.discountPercentage,
      )),
      entity.items.map(item => new OrderItem(item.productId, item.quantity, item.unitPrice)),
    );
  }

  private toEntity(order: Order): OrderEntity {
    // Map domain objects to database fields
    return new OrderEntity({
      id: order.id,
      customerId: order.customer.id,
      customerName: order.customer.name,
      // ... other fields
    });
  }
}
```

### 3. Services for Cross-Cutting Logic

Services handle operations that don’t naturally belong to a single aggregate. For example:
- A `PaymentService` might validate payment and interact with external APIs.
- A `DiscountCalculator` could pre-calculate discounts based on customer tiers.

```typescript
// Domain service (pure logic)
class DiscountCalculator {
  static calculateDiscount(customer: Customer): number {
    return customer.getDiscount();
  }
}

// Application service (coords aggregates/repositories)
class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly paymentService: PaymentService,
  ) {}

  async placeOrder(order: Order): Promise<void> {
    const discount = DiscountCalculator.calculateDiscount(order.customer);
    order.applyDiscount(discount); // Hypothetical method

    await this.orderRepository.save(order);
    await this.paymentService.process(order.calculateTotal());
  }
}
```

### 4. Events for Asynchronous Workflows

Domain events drive asynchronous behavior (e.g., sending emails, updating inventory). Here’s how we’d handle `OrderPaid` events:

```typescript
// Domain event handler
class OrderPaidEventHandler {
  constructor(
    private readonly emailService: EmailService,
  ) {}

  handle(event: { orderId: string; amount: number; customerId: string }): void {
    this.emailService.sendOrderConfirmation(
      customerId,
      `Your order #${event.orderId} for $${event.amount} has been processed.`,
    );
  }
}
```

---

## Implementation Guide: DDD in Your Backend

### Step 1: Identify Bounded Contexts
Start by asking: *"What are the distinct business domains in our system?"*
For e-commerce, examples might include:
- **Customer Management** (users, subscriptions).
- **Order Processing** (orders, items, payments).
- **Inventory Management** (products, stock).

Each context should have its own:
- Domain model.
- Repository.
- Event system.

### Step 2: Model Aggregates
An **aggregate** is a cluster of objects treated as a single unit for data changes. Rules:
- Every aggregate has a **root** (e.g., `Order` is the root for `OrderItem`).
- Changes to aggregates must go through the root.

Example aggregate root for `Order`:
```typescript
class Order {
  // ... previous code ...

  // Only the Order root can modify items
  addItem(item: OrderItem): void {
    // Validation logic here (e.g., check inventory)
    this._items.push(item);
  }
}
```

### Step 3: Use Ubiquitous Language
Collaborate with domain experts to define a shared vocabulary. Avoid technical terms like "user" or "product"—use terms like `Customer` or `CatalogItem`.

### Step 4: Build Repositories
Repositories should:
- Hide persistence details (use interfaces).
- Map between domain objects and database entities.

Example with SQL (PostgreSQL):
```sql
-- Database schema for Order (simplified)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL REFERENCES customers(id),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Pending', 'Paid', 'Shipped', 'Cancelled')),
  total DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id),
  product_id UUID NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL
);
```

### Step 5: Implement Event Sourcing (Optional)
For auditability and eventual consistency, use event sourcing to track changes as a sequence of events.

Example:
```typescript
class Order {
  private _events: DomainEvent[] = [];

  // ... previous code ...

  pay(): void {
    // Business logic
    this._status = OrderStatus.Paid;
    this._events.push({
      name: "OrderPaid",
      payload: { ... },
      timestamp: new Date(),
    });
  }

  replayEvents(): void {
    this._events.forEach(event => {
      switch (event.name) {
        case "OrderPaid":
          this._status = OrderStatus.Paid;
          break;
        // ... other events
      }
    });
  }
}
```

### Step 6: Design APIs Around Domain Logic
Instead of exposing `/orders/{id}`, consider:
- `/orders/{id}/pay` (domain-driven endpoint).
- `/customers/{id}/subscriptions` (bounded context).

Example API route:
```typescript
// Express route (simplified)
router.post("/customers/:customerId/orders", async (req, res) => {
  const customer = await customerRepository.findById(req.params.customerId);
  const order = new Order(customer, req.body.items);
  await orderService.placeOrder(order);
  res.status(201).send(order);
});
```

---

## Common Mistakes to Avoid

1. **Overdoing DDD**: Start small. DDD is a tool, not a crutch. Don’t model everything as a domain concept if it’s not business-critical.
2. **Ignoring Infrastructure**: DDD is about *modeling*, not *persistence*. Use repositories to abstract away SQL/NoSQL.
3. **Tight Coupling to Domain Events**: Events should be *declarative*, not imperative. Avoid business logic in event handlers.
4. **Forgetting Ubiquitous Language**: If developers and stakeholders use different words for the same thing, miscommunication will follow.
5. **Skipping Tests**: Domain logic is complex—write unit tests for aggregates and services.

---

## Key Takeaways

- **DDD aligns code with business logic**, not technical concerns.
- **Bounded contexts** help partition a large domain into manageable pieces.
- **Aggregates** define consistency boundaries for data changes.
- **Repositories** decouple domain models from persistence.
- **Events** enable asynchronous workflows and auditability.
- **Start small**: DDD is a journey, not a sprint. Begin with one bounded context.

---

## Conclusion

Domain-Driven Design is more than a technical pattern—it’s a way to think about software that *serves* the business, not just *serves* the code. By modeling your backend around real-world concepts, you’ll build systems that are easier to understand, maintain, and scale.

Remember:
- **DDD isn’t a silver bullet**. It’s most valuable when the business logic is complex or evolving.
- **Collaborate with domain experts**. Their understanding of the business is invaluable.
- **Iterate**. Refactor as you learn more about the domain.

Start with one bounded context (e.g., Order Processing) and gradually expand. Your future self—and your stakeholders—will thank you.

---
### Further Reading
- [Domain-Driven Design: Tackling Complexity in the Heart of Software](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215) (Eric Evans).
- [EventStorming](https://eventstorming.com/) (for modeling domains collaboratively).
- [CQRS Patterns in Practice](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf) (Greg Young).

---
### Code Repository
Check out this [GitHub repo](https://github.com/janedoe/ddd-ecommerce-example) for a full implementation of the e-commerce example.
```

---
This post balances theory with practical code examples, highlights tradeoffs, and provides actionable steps for implementation.