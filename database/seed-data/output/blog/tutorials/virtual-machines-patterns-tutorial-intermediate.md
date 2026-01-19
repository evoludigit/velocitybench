```markdown
---
title: "Virtual Machines Pattern: Building Flexible Stateful APIs Without the Overhead"
date: YYYY-MM-DD
author: Jane Doe
tags: ["backend-patterns", "database-design", "api-patterns", "stateful-systems"]
series: ["Design Patterns for Modern Backends"]
---

# The Virtual Machines Pattern: Modeling Stateful Processes with Clean APIs

As backend systems grow more complex, developers often face a recurring challenge: how to model stateful processes in a way that's both flexible and scalable. Traditional database-driven applications often struggle with tight coupling between business logic and persistence, leading to brittle architectures that are hard to modify or extend.

APIs today need to do more than just CRUD—users expect complex workflows (e.g., order processing, workflow automation, or game turn-based systems) that maintain state across multiple operations. The **Virtual Machines (VM) Pattern** is a powerful way to encapsulate these stateful processes into clean, reusable components that can be invoked via API calls while maintaining their internal state.

In this guide, we'll explore how to implement this pattern using modern Node.js/TypeScript, with PostgreSQL as our data store. We'll cover when to use this pattern, its architectural implications, and common pitfalls—plus practical code examples to bring the concept to life.

---

## The Problem: Modeling Stateful Workflows Without Mess

Let's consider a common scenario: building an **e-commerce order processing system**. A typical order involves multiple steps:

1. Product selection (cart creation)
2. Shipping address configuration
3. Payment processing
4. Order fulfillment
5. Refund requests

Each step depends on the previous one, and the system must remember its state between API calls. If we model this naively:

```typescript
// ❌ Traditional approach - global state
const orders: Order[] = [{ id: 1, status: 'cart', items: [...] }];
const paymentProcessor = new PaymentService();

// API endpoint that modifies shared state
app.post('/process-order/:id', async (req, res) => {
  const order = orders.find(o => o.id == req.params.id);
  if (!order) return res.status(404);

  // ⚠️ Direct manipulation of shared state
  order.status = 'paid';
  await paymentProcessor.process(order);

  // ⚠️ Next step might fail while state is inconsistent
  // ...
});
```

This leads to several problems:

1. **Tight coupling**: The database (or in-memory objects) directly encodes business logic
2. **Race conditions**: Concurrent requests can corrupt state
3. **Inconsistent state**: Partial transactions leave systems in invalid states
4. **Testing difficulties**: Stateful behavior is hard to mock and verify
5. **Scalability issues**: Shared state becomes a bottleneck in distributed systems

The problem isn't just technical—it's about **design clarity**. When systems become stateful, their behavior becomes harder to reason about, and changes require careful consideration of all possible execution paths.

---

## The Solution: Virtual Machines as Stateful API Components

The **Virtual Machines Pattern** solves these issues by:

- Encapsulating stateful processes in **isolated, reusable components** that can be:
  - Triggered via API calls
  - Persisted independently of the main application
  - Inhibited or resumed as needed
- Providing a **clean separation** between:
  - Public API (what clients interact with)
  - Internal state (how the process actually works)
- Enabling **time-based** and **event-driven** execution of workflows

Our implementation will use three core concepts:
1. **Process definitions**: Blueprints for stateful workflows
2. **Process instances**: Individual executions with their own state
3. **State machines**: The mechanism that coordinates transitions

---

## Components/Solutions: Building the Virtual Machine

Let's break down the implementation into practical components:

### 1. Process Definitions (The Blueprint)

First, we define what a process *can* do by specifying:
- Valid states
- State transitions
- Events that trigger transitions

```typescript
// models/ProcessDefinition.ts
export type ProcessEvent =
  | { type: 'create' }
  | { type: 'payment_processed'; amount: number }
  | { type: 'shipping_created'; tracking_id: string }
  | { type: 'refund_requested'; amount: number }
  | { type: 'cancel' };

export type ProcessState =
  | { state: 'cart'; items: string[] }
  | { state: 'payment_pending' }
  | { state: 'payment_processing' }
  | { state: 'payment_completed'; payment_id: string }
  | { state: 'shipped'; tracking_id: string }
  | { state: 'cancelled' };

export interface ProcessDefinition {
  id: string;
  name: string;
  initialState: ProcessState;
  events: ProcessEvent[];
  transitions: Record<
    `from ${ProcessState['state']}`,
    Record<
      ProcessEvent['type'],
      ProcessState
    >
  >;
}
```

### 2. Process Instances (Running Workflows)

Instances store their current state and execution history:

```typescript
// models/ProcessInstance.ts
import { ProcessState, ProcessEvent } from './ProcessDefinition';

export interface ProcessInstance {
  id: string;
  definitionId: string;
  currentState: ProcessState;
  history: ProcessEvent[];
  createdAt: Date;
  updatedAt: Date;
}
```

### 3. The Virtual Machine (Execution Engine)

This component:
- Validates state transitions
- Applies business logic to events
- Persists state changes

```typescript
// virtualMachine.ts
import { ProcessDefinition, ProcessInstance, ProcessState, ProcessEvent } from './models';

export class VirtualMachine {
  constructor(private processDefinitions: Map<string, ProcessDefinition>) {}

  async handleEvent(
    instanceId: string,
    event: ProcessEvent,
    db: Database
  ): Promise<ProcessInstance> {
    // Fetch the current process instance
    const instance = await db.getProcessInstance(instanceId);
    if (!instance) throw new Error('Process not found');

    // Get the definition for this process
    const definition = this.processDefinitions.get(instance.definitionId);
    if (!definition) throw new Error('Definition not found');

    // Validate the event is allowed from current state
    const allowedEvents = this.getAllowedEvents(instance.currentState, definition);
    if (!allowedEvents.includes(event.type)) {
      throw new Error(`Event ${event.type} not allowed from ${instance.currentState.state}`);
    }

    // Apply the transition
    const newState = this.applyTransition(instance.currentState, event, definition);
    const newHistory = [...instance.history, event];

    // Persist the updated state
    return await db.updateProcessInstance(instanceId, {
      currentState: newState,
      history: newHistory,
      updatedAt: new Date()
    });
  }

  private getAllowedEvents(currentState: ProcessState, definition: ProcessDefinition): string[] {
    const stateType = currentState.state;
    return Object.keys(definition.transitions[`from ${stateType}`] || {});
  }

  private applyTransition(
    currentState: ProcessState,
    event: ProcessEvent,
    definition: ProcessDefinition
  ): ProcessState {
    const stateType = currentState.state;
    const transition = definition.transitions[`from ${stateType}`]?.[event.type];
    if (!transition) throw new Error('Invalid transition');

    switch (event.type) {
      case 'payment_processed':
        return {
          ...transition,
          payment_id: `payment_${Math.random().toString(36).substring(2, 9)}`
        };
      case 'shipping_created':
        return {
          ...transition,
          tracking_id: `TRACKING_${Math.random().toString(36).substring(2, 8)}`
        };
      default:
        return transition;
    }
  }
}
```

### 4. Database Schema

We'll use PostgreSQL with pg-promise for our persistence:

```sql
-- schema.sql
CREATE TABLE process_definitions (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  definition_json JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE process_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  definition_id INTEGER NOT NULL REFERENCES process_definitions(id),
  current_state JSONB NOT NULL,
  history JSONB[] NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_process_instances_definition_id ON process_instances(definition_id);
```

### 5. Process Registry (Initialization)

We initialize our VM with process definitions:

```typescript
// server.ts
import { VirtualMachine } from './virtualMachine';
import { Database } from './database';
import { orderProcessingDefinition } from './definitions';

const db = new Database();
const processDefinitions = new Map<string, ProcessDefinition>();
processDefinitions.set('order-processing', orderProcessingDefinition);

const vm = new VirtualMachine(processDefinitions);

// API integration
app.post('/processes/:instanceId/events', async (req, res) => {
  try {
    const result = await vm.handleEvent(
      req.params.instanceId,
      req.body.event,
      db
    );
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

---

## Code Examples: Complete Implementation

Let's walk through a complete order processing example:

### 1. Process Definition

```typescript
// definitions/orderProcessing.ts
import { ProcessDefinition, ProcessState } from '../models';

export const orderProcessingDefinition: ProcessDefinition = {
  id: 'order-processing',
  name: 'Order Processing',
  initialState: {
    state: 'cart',
    items: []
  },
  events: [
    { type: 'create' },
    { type: 'payment_processed', amount: null },
    { type: 'shipping_created', tracking_id: null }
  ],
  transitions: {
    'from cart': {
      create: {
        state: 'cart',
        items: [] // Default empty cart
      },
      'payment_processed': {
        state: 'payment_pending',
        items: undefined // Items no longer needed after payment
      }
    },
    'from payment_pending': {
      'payment_processed': {
        state: 'payment_processing'
      }
    },
    'from payment_processing': {
      'payment_processed': {
        state: 'payment_completed',
        payment_id: 'placeholder'
      }
    },
    'from payment_completed': {
      'shipping_created': {
        state: 'shipped',
        tracking_id: undefined
      }
    }
  }
};
```

### 2. API Endpoints

```typescript
// api/orders.ts
import { VirtualMachine } from '../virtualMachine';
import { Database } from '../database';

export class OrderAPI {
  constructor(
    private vm: VirtualMachine,
    private db: Database
  ) {}

  async createOrder(req: Request): Promise<{ instanceId: string }> {
    // Create a new process instance
    const instance = {
      id: crypto.randomUUID(),
      definitionId: 'order-processing',
      currentState: {
        state: 'cart',
        items: req.body.items
      },
      history: [{ type: 'create' }],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.db.createProcessInstance(instance);
    return { instanceId: instance.id };
  }

  async payOrder(req: Request): Promise<ProcessInstance> {
    return this.vm.handleEvent(
      req.params.instanceId,
      { type: 'payment_processed', amount: req.body.amount },
      this.db
    );
  }

  async shipOrder(req: Request): Promise<ProcessInstance> {
    return this.vm.handleEvent(
      req.params.instanceId,
      { type: 'shipping_created', tracking_id: req.body.tracking_id },
      this.db
    );
  }
}
```

### 3. Example Usage Flow

```typescript
// Client usage example
async function processOrder() {
  // 1. Create a new order
  const { instanceId } = await client.createOrder({
    items: [
      { productId: 'p123', quantity: 2 },
      { productId: 'p456', quantity: 1 }
    ]
  });
  console.log('Order created', instanceId);

  // 2. Pay the order
  const afterPayment = await client.payOrder(instanceId, {
    amount: 129.99
  });
  console.log('Payment status:', afterPayment.currentState.state);

  // 3. Ship the order (would only be available after payment)
  const shipped = await client.shipOrder(instanceId, {
    tracking_id: 'USPS-12345'
  });
  console.log('Tracking:', shipped.currentState.tracking_id);
}
```

---

## Implementation Guide: Building Your Virtual Machines

### Step 1: Define Your Process Flow

1. Identify all possible states in your workflow
2. For each state, determine:
   - What events can occur?
   - What are the valid outcomes?
3. Document your process definition thoroughly

**Example workflow diagram:**
```
cart --(create)--> cart
cart --(payment_processed)--> payment_pending
payment_pending --(payment_processed)--> payment_processing
payment_processing --(payment_processed)--> payment_completed
payment_completed --(shipping_created)--> shipped
any_state --(cancel)--> cancelled
```

### Step 2: Create Database Schema

1. Use JSON/JSONB columns to store:
   - Current state
   - Event history
   - Any state-specific data
2. Add indexes for frequently queried fields
3. Consider adding a version column for audit purposes

### Step 3: Implement the Virtual Machine

1. Start with a basic state machine implementation
2. Add validation for state transitions
3. Implement event processing with clear error handling
4. Add serialization/deserialization for state

### Step 4: Build API Integration

1. Create endpoints that trigger events
2. Design a consistent API for all process types
3. Implement proper error handling and retries
4. Consider adding async processing for long-running operations

### Step 5: Add Monitoring

1. Track process execution times
2. Monitor state transitions
3. Set up alerts for stalled processes
4. Implement process health checks

---

## Common Mistakes to Avoid

1. **Overly complex state definitions**: Start simple and refactor as you discover needed complexity
   - ❌ `state: 'payment_completed_with_discount_applied'`
   - ✅ `state: 'payment_completed'; discount_applied: boolean`

2. **Ignoring event history**: Always track what happened to your state
   ```typescript
   // Avoid this:
   // const state = { state: 'shipped' };

   // Use this:
   const history = [...currentHistory, { type: 'shipping_created' }];
   ```

3. **Not validating transitions**: Always check if an event is allowed from the current state
   ```typescript
   // ❌ Nothing prevents invalid transitions
   function applyTransition() {
     // ...business logic...
   }

   // ✅ Validate transitions first
   if (!isAllowedTransition(currentState, event)) {
     throw new Error('Invalid transition');
   }
   ```

4. **Tight coupling to specific processes**: Design your VM to handle multiple workflow types
   ```typescript
   // Avoid process-specific logic in VM
   function handleEvent(instance: ProcessInstance, event: Event) {
     if (instance.definitionId === 'order-processing') {
       // ❌ Tight coupling
     }
     // ...
   }
   ```

5. **Neglecting concurrency**: Always consider how multiple clients might interact with instances
   ```typescript
   // Always use optimistic concurrency or locks
   await db.beginTransaction(async (trx) => {
     const instance = await trx.getProcessInstance(instanceId);
     // Validate version/stamp
     if (instance.version !== expectedVersion) {
       throw new ConflictError('Concurrent modification');
     }
     // Update with new version
     await trx.updateProcessInstance(instanceId, { version: expectedVersion + 1 });
   });
   ```

6. **No cleanup mechanism**: Implement process finalization and cleanup
   - For long-running processes, add timeout handling
   - Implement state cleanup for completed processes

7. **Poor error handling**: Provide meaningful error messages for each failure case
   ```typescript
   // Instead of generic errors:
   // throw new Error('Payment failed');

   // Use specific error codes:
   throw new PaymentError({
     status: 'failed',
     reason: 'insufficient_funds',
     retries_remaining: 2
   });
   ```

---

## Key Takeaways

✅ **Encapsulation**: Hide complex workflows behind clean, stateless APIs
✅ **Isolation**: Each process instance maintains its own state
✅ **Extensibility**: New workflows are just new process definitions
✅ **Auditability**: Complete event history makes debugging easier
✅ **Resilience**: Design for concurrent access and partial failures

⚠️ **Tradeoffs to consider**:
- **Complexity**: Process definitions add design overhead
- **Persistence**: State needs to be serialized/deserialized
- **Scalability**: Each long-running process consumes resources
- **Testing**: More complex systems require more test coverage

🔧 **When to use this pattern**:
- When you need to model complex, multi-step workflows
- When state must be preserved between API calls
- When you need to implement async or time-based processing
- When you want to separate API contracts from business logic

---

## Conclusion

The Virtual Machines Pattern provides a powerful way to model stateful processes in modern backend systems. By encapsulating workflows as first-class citizens of your architecture, you gain several advantages:

1. **Cleaner API contracts**: Clients interact with simple event triggers
2. **Better separation of concerns**: Business logic is isolated from persistence
3. **Increased maintainability**: Changes to workflows are localized
4. **Improved testability**: Process behavior can be verified in isolation

The key to successful implementation is starting small and focusing on the core problem. Begin with a single process definition, validate it with real use cases, then gradually expand. Remember that no pattern is a silver bullet—be prepared to adapt as your requirements evolve.

For systems with extremely simple workflows, a direct database approach might suffice. For complex, long-running processes, consider complementary patterns like:

- **Saga Pattern** for coordinating multiple services
- **Event Sourcing** for auditability
- **CQRS** for separating read/write models

But for most stateful API scenarios, the Virtual Machines Pattern provides a robust foundation. By treating your business workflows as virtual machines, you unlock cleaner architecture and more maintainable code.

Now go forth and encapsulate those workflows!
```

```typescript
// Additional utility functions you might want