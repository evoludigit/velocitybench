```markdown
# **Logistics Domain Patterns: Building Robust Shipping and Delivery Systems**

Ever tried to build a shipping or delivery platform—only to face headaches with tracking, inventory, or real-time updates? You're not alone. Logistics systems are complex: they involve multiple moving parts (warehouses, carriers, routes, delays, and customers), require real-time coordination, and must handle edge cases like cancellations, partial deliveries, or driver issues.

This is where **Logistics Domain Patterns** come in. These are proven strategies for modeling and implementing shipping workflows, inventory tracking, and delivery coordination in a way that feels natural to business logic while keeping your codebase maintainable and scalable. Whether you're working on an e-commerce platform, food delivery app, or courier service, these patterns will help you structure your system for success.

In this guide, we’ll break down common logistics problems, introduce key patterns, and provide practical code examples in **TypeScript (Node.js)** and **Python (Django)**. We’ll also discuss tradeoffs and pitfalls to avoid.

---

## **The Problem: Messy Logistics Without Patterns**

Without domain-driven design (DDD) principles tailored for logistics, your system might suffer from:

- **Tight coupling**: Business rules (e.g., "If a package is delayed by 24 hours, notify the customer") are scattered across services or monolithic code.
- **Poor event handling**: Tracking package status changes (e.g., "In Transit" → "Out for Delivery") becomes error-prone.
- **Race conditions**: Concurrent updates (e.g., two drivers claiming a package) lead to data inconsistencies.
- **Hard-to-test logic**: Shipping workflows are hard to mock or unit-test because they depend on external services (e.g., GPS tracking, carrier APIs).
- **Inflexible error handling**: Failures (e.g., failed pickup, incorrect address) are handled ad-hoc instead of systematically.

### Real-World Example: The "Lost Package" Scenario
Imagine a customer orders a product, but:
1. The warehouse mislabels the package.
2. The carrier system doesn’t validate the address.
3. The driver doesn’t pick up the package on time.
4. The customer calls support, but no one in the system knows where the package *actually* is.

Without domain patterns, your code might look like this:
```typescript
// ❌ Monolithic and hard to maintain
async processOrder(orderId: string) {
  const order = await Order.findById(orderId);
  const warehouse = await Warehouse.findById(order.warehouseId);
  const carrier = await CarrierService.getCarrier(order.carrierId);

  // Business logic mixed with persistence
  if (order.status === "PENDING") {
    if (warehouse.hasStock(order.productId)) {
      await warehouse.reserveStock(order.productId, order.quantity);
      await carrier.createShipment(orderId);
      await sendNotification(order.customerId, "Your order is shipping!");
    } else {
      // ⚠️ Error handling is scattered
      await sendNotification(order.customerId, "Out of stock!");
    }
  }
}
```
This approach is **unmaintainable**, **hard to test**, and **couples** the domain logic too tightly to databases or external services.

---

## **The Solution: Logistics Domain Patterns**

Logistics domain patterns help you:
1. **Model the domain clearly** (e.g., `Order`, `Shipment`, `Driver` as rich objects).
2. **Separate business logic from infrastructure** (e.g., carrier APIs, databases).
3. **Handle events and state transitions** (e.g., "Package Delivered") in a predictable way.
4. **Decouple services** so changes to one part (e.g., a new carrier API) don’t break others.
5. **Make the system observable** (logs, events, and dashboards for tracking).

We’ll cover **three core patterns** with practical examples:

1. **Event Sourcing for Shipping Workflows**
2. **Command Query Responsibility Segregation (CQRS) for Tracking**
3. **Aggregate Root for Package Management**

### Assumptions
- You’re using **Node.js + TypeScript** or **Python + Django**.
- You have a basic understanding of DDD concepts like **entities**, **value objects**, and **aggregates**.
- You’re familiar with async/await for handling long-running operations.

---

## **Components/Solutions**

### 1. Event Sourcing for Shipping Workflows
**Problem**: Shipping involves a sequence of state changes (e.g., `CREATED` → `PICKING_UP` → `IN_TRANSIT` → `DELIVERED`). Traditional database updates are hard to audit and replay.

**Solution**: Use **event sourcing** to store every state change as an **immutable event**. This makes it easier to:
- Reconstruct the shipping history.
- Handle retries for failed steps (e.g., "Retry delivery if the package was not signed for").
- Integrate with external systems (e.g., carrier APIs) without polling.

#### Example: Event Sourcing for a Shipment
```typescript
// models/Shipment.ts
import { Entity } from "./Entity";

export interface ShipmentCreatedEvent {
  type: "shipment.created";
  shipmentId: string;
  orderId: string;
  status: "CREATED";
  createdAt: Date;
}

export interface ShipmentPickedUpEvent {
  type: "shipment.pickedup";
  shipmentId: string;
  driverId: string;
  pickupTime: Date;
  status: "IN_TRANSIT";
}

export type ShipmentEvent = ShipmentCreatedEvent | ShipmentPickedUpEvent;

export class Shipment extends Entity {
  private _status: "CREATED" | "IN_TRANSIT" | "DELIVERED";
  private events: ShipmentEvent[] = [];

  constructor(shipmentId: string) {
    super(shipmentId);
    this._status = "CREATED";
    this.events.push({
      type: "shipment.created",
      shipmentId,
      status: "CREATED",
      orderId: "order-123", // Placeholder
      createdAt: new Date(),
    });
  }

  markAsPickedUp(driverId: string): void {
    if (this._status !== "CREATED") {
      throw new Error("Shipment is not in the correct state");
    }
    this._status = "IN_TRANSIT";
    this.events.push({
      type: "shipment.pickedup",
      shipmentId: this.id,
      driverId,
      pickupTime: new Date(),
      status: "IN_TRANSIT",
    });
  }

  getEvents(): ShipmentEvent[] {
    return [...this.events];
  }

  getStatus(): string {
    return this._status;
  }
}
```

#### Event Store (Persistence)
```typescript
// repositories/EventStore.ts
import { ShipmentEvent } from "../models/Shipment";

export class EventStore {
  private events: ShipmentEvent[] = [];

  append(shipmentId: string, event: ShipmentEvent): void {
    this.events.push(event);
    console.log(`[Event Store] Appended event for shipment ${shipmentId}`);
  }

  getEventsForShipment(shipmentId: string): ShipmentEvent[] {
    return this.events.filter(e => e.shipmentId === shipmentId);
  }
}
```

#### Usage Example
```typescript
// services/ShipmentService.ts
import { Shipment } from "../models/Shipment";
import { EventStore } from "../repositories/EventStore";

export class ShipmentService {
  private eventStore = new EventStore();

  async createShipment(shipmentId: string): Promise<Shipment> {
    const shipment = new Shipment(shipmentId);
    this.eventStore.append(shipmentId, shipment.getEvents()[0]);
    return shipment;
  }

  async markAsPickedUp(shipmentId: string, driverId: string): Promise<void> {
    const shipment = new Shipment(shipmentId); // In reality, reconstruct from events
    shipment.markAsPickedUp(driverId);
    shipment.getEvents().slice(1).forEach(event =>
      this.eventStore.append(shipmentId, event)
    );
  }
}
```

**Tradeoffs**:
- **Pros**: Audit trail, easier testing, better for long-running workflows.
- **Cons**: More complex to implement; requires careful handling of concurrency.

---

### 2. Command Query Responsibility Segregation (CQRS) for Tracking
**Problem**: Shipping systems need to:
- **Write**: Update package status (e.g., "Delivered").
- **Read**: Get real-time tracking info (e.g., "Package is at 123 Main St").

But mixing these in one model leads to **tight coupling** and **inefficient queries**.

**Solution**: **CQRS** separates reads and writes:
- **Commands** handle mutations (e.g., `UpdateShipmentStatusCommand`).
- **Queries** handle reads (e.g., `GetShipmentTrackingQuery`).
- Use **eventual consistency** (e.g., read from a cached view).

#### Example: CQRS for Shipment Tracking
```typescript
// commands/UpdateShipmentStatusCommand.ts
import { CommandHandler, ICommandHandler } from "../domain/CommandHandler";

export interface UpdateShipmentStatusCommand {
  shipmentId: string;
  status: "IN_TRANSIT" | "DELIVERED";
}

export class UpdateShipmentStatusCommandHandler
  implements ICommandHandler<UpdateShipmentStatusCommand>
{
  async handle(command: UpdateShipmentStatusCommand): Promise<void> {
    console.log(
      `[Command] Updating shipment ${command.shipmentId} to ${command.status}`
    );
    // In a real app, this would update the event store or a write model.
  }
}
```

```typescript
// queries/GetShipmentTrackingQuery.ts
import { QueryHandler, IQueryHandler } from "../domain/QueryHandler";

export interface GetShipmentTrackingQuery {
  shipmentId: string;
}

export class GetShipmentTrackingQueryHandler
  implements IQueryHandler<GetShipmentTrackingQuery, { status: string }>
{
  async handle(query: GetShipmentTrackingQuery): Promise<{ status: string }> {
    // Simulate reading from a read model (e.g., Redis or a separate DB)
    return {
      status: "IN_TRANSIT", // In reality, this would come from the event store
    };
  }
}
```

#### Usage Example
```typescript
// app.ts
import { UpdateShipmentStatusCommandHandler } from "./commands/UpdateShipmentStatusCommand";
import { GetShipmentTrackingQueryHandler } from "./queries/GetShipmentTrackingQuery";

const commandHandler = new UpdateShipmentStatusCommandHandler();
const queryHandler = new GetShipmentTrackingQueryHandler();

// Write: Update shipment status
await commandHandler.handle({
  shipmentId: "ship-123",
  status: "DELIVERED",
});

// Read: Get tracking info
const tracking = await queryHandler.handle({ shipmentId: "ship-123" });
console.log(tracking); // { status: "DELIVERED" }
```

**Tradeoffs**:
- **Pros**: Decouples reads/writes, scales reads independently.
- **Cons**: Adds complexity; requires careful event propagation.

---

### 3. Aggregate Root for Package Management
**Problem**: A package involves multiple entities (e.g., `Order`, `Shipment`, `Driver`), but you need to ensure **invariants** (e.g., "A shipment can only be delivered if it’s assigned to a driver").

**Solution**: Use an **aggregate root** (`Shipment`) to control access to its child entities. This prevents inconsistencies.

#### Example: Aggregate Root for Shipment
```typescript
// models/ShipmentAggregate.ts
import { AggregateRoot } from "./AggregateRoot";

export class ShipmentAggregate extends AggregateRoot {
  private _shipment: {
    id: string;
    status: "CREATED" | "IN_TRANSIT" | "DELIVERED";
    driverId?: string;
    orderId: string;
  };

  constructor(shipmentId: string, orderId: string) {
    super(shipmentId);
    this._shipment = {
      id: shipmentId,
      status: "CREATED",
      orderId,
    };
  }

  assignDriver(driverId: string): void {
    if (this._shipment.status !== "CREATED") {
      throw new Error("Shipment must be created to assign a driver");
    }
    this._shipment.driverId = driverId;
    this._shipment.status = "IN_TRANSIT";
    this.applyChange(
      new ShipmentDriverAssignedEvent(driverId, this._shipment.id)
    );
  }

  markAsDelivered(): void {
    if (this._shipment.status !== "IN_TRANSIT") {
      throw new Error("Shipment must be in transit to be delivered");
    }
    this._shipment.status = "DELIVERED";
    this.applyChange(new ShipmentDeliveredEvent(this._shipment.id));
  }

  getStatus(): string {
    return this._shipment.status;
  }
}

class ShipmentDriverAssignedEvent {
  constructor(
    public driverId: string,
    public shipmentId: string,
    public timestamp = new Date()
  ) {}
}

class ShipmentDeliveredEvent {
  constructor(
    public shipmentId: string,
    public timestamp = new Date()
  ) {}
}
```

#### Usage Example
```typescript
// services/ShipmentAggregateService.ts
import { ShipmentAggregate } from "../models/ShipmentAggregate";

export class ShipmentAggregateService {
  private aggregates = new Map<string, ShipmentAggregate>();

  createShipment(shipmentId: string, orderId: string): ShipmentAggregate {
    const aggregate = new ShipmentAggregate(shipmentId, orderId);
    this.aggregates.set(shipmentId, aggregate);
    return aggregate;
  }

  assignDriver(shipmentId: string, driverId: string): void {
    const aggregate = this.aggregates.get(shipmentId);
    if (!aggregate) throw new Error("Shipment not found");
    aggregate.assignDriver(driverId);
  }

  markAsDelivered(shipmentId: string): void {
    const aggregate = this.aggregates.get(shipmentId);
    if (!aggregate) throw new Error("Shipment not found");
    aggregate.markAsDelivered();
  }
}
```

**Tradeoffs**:
- **Pros**: Enforces domain invariants, simplifies transactions.
- **Cons**: Harder to test in isolation; requires careful boundary definition.

---

## **Implementation Guide**

### Step 1: Define Core Domain Entities
Start by modeling the key entities in your logistics domain:
- `Order` (customer, items, status)
- `Shipment` (tracking number, status, events)
- `Driver` (routes, availability)
- `Warehouse` (stock, locations)

Example:
```typescript
// models/Order.ts
export class Order {
  constructor(
    public id: string,
    public customerId: string,
    public items: { productId: string; quantity: number }[],
    public status: "PENDING" | "SHIPPED" | "DELIVERED"
  ) {}

  ship(): void {
    if (this.status !== "PENDING") {
      throw new Error("Order must be pending to ship");
    }
    this.status = "SHIPPED";
  }
}
```

### Step 2: Implement Event Sourcing
Use an event store (e.g., in-memory for testing, or a database like MongoDB for production).

```typescript
// repositories/EventStoreInMemory.ts
import { ShipmentEvent } from "../models/Shipment";

export class InMemoryEventStore implements EventStore {
  private events: ShipmentEvent[] = [];

  append(shipmentId: string, event: ShipmentEvent): void {
    this.events.push(event);
  }

  getEventsForShipment(shipmentId: string): ShipmentEvent[] {
    return this.events.filter(e => e.shipmentId === shipmentId);
  }

  getAllEvents(): ShipmentEvent[] {
    return [...this.events];
  }
}
```

### Step 3: Separate Commands and Queries
Use a **command bus** (e.g., `event-bus` or `Nakadi`) to dispatch commands.

```typescript
// domain/CommandBus.ts
type CommandHandler<T> = (command: T) => Promise<void>;

export class CommandBus {
  private handlers = new Map<string, CommandHandler<any>>();

  register<T>(commandType: string, handler: CommandHandler<T>): void {
    this.handlers.set(commandType, handler);
  }

  async dispatch<T>(command: T): Promise<void> {
    const handler = this.handlers.get(command.constructor.name);
    if (!handler) throw new Error("No handler for command");
    await handler(command);
  }
}
```

### Step 4: Use an Aggregate Root for Transactions
Ensure all child objects are updated atomically.

```typescript
// services/TransactionService.ts
export class TransactionService {
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    const result = await fn();
    // Simulate a DB transaction
    console.log("[Transaction] Committed");
    return result;
  }
}
```

### Step 5: Build a Read Model for Tracking
Use a **read model** (e.g., Redis, Elasticsearch) to cache tracking data.

```typescript
// repositories/ShipmentTrackingRepository.ts
import { Shipment } from "../models/Shipment";

export class ShipmentTrackingRepository {
  private cache = new Map<string, { status: string }>();

  async save(shipment: Shipment): Promise<void> {
    this.cache.set(shipment.id, { status: shipment.getStatus() });
  }

  async getTracking(shipmentId: string): Promise<{ status: string }> {
    return this.cache.get(shipmentId) || { status: "UNKNOWN" };
  }
}
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Domain Invariants**
   - ❌ Let `Shipment.status` be updated freely.
   - ✅ Enforce rules via aggregate roots (e.g., only `CREATED` → `IN_TRANSIT`).

2. **Tight Coupling to Databases**
   - ❌ Store `Shipment` directly in a relational DB without an event store.
   - ✅ Use event sourcing to decouple persistence from domain logic.

3. **Not Handling Concurrency**
   - ❌ Assume all operations are sequential.
   - ✅ Use **optimistic locking** (e.g., `ETag` headers) or **pessimistic locking** (reserved rows).

4. **Overcomplicating CQRS**
   - ❌ Separate reads/writes unless you have a **clear scaling need**.
   - ✅ Start simple; split only when