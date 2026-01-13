```markdown
---
title: "Manufacturing Domain Patterns: Building Robust Backends for Production Lines"
date: 2024-03-15
tags: ["backend", "database", "domain-driven design", "API design", "patterns"]
description: "Dive into Manufacturing Domain Patterns—a practical approach to designing APIs and databases for production environments. Learn implementation details, tradeoffs, and real-world examples."
---

# Manufacturing Domain Patterns: Building Robust Backends for Production Lines

In modern backend development, we often face complex domains where business rules are tightly coupled with data flow. Manufacturing systems—where orders, schedules, inventory, and production steps interact—are a prime example. Poor design in these systems can lead to brittle APIs, inconsistent data, and operational nightmares during high-volume production.

The **Manufacturing Domain Pattern** is a structured approach to modeling production-related workflows where:
- **State changes** are inevitable and must be carefully validated
- **Dependencies** between entities (e.g., orders → production steps → inventory) create cascading effects
- **Concurrency** is critical (e.g., multiple shifts, parallel production lines)
- **Auditability** is required (e.g., traceability for quality control)

In this guide, we’ll explore how to design APIs and databases for manufacturing workflows with practical examples in Go, PostgreSQL, and GraphQL. We’ll cover event-driven architectures, optimized queries, and how to balance consistency with performance.

---

## The Problem: Without Domain Patterns, Chaos Ensues

Imagine a high-volume manufacturing plant with:
- **Thousands of production orders** generated daily
- **Real-time updates** to shop floors via cellular IoT devices
- **Strict compliance requirements** (e.g., FDA/GMP for pharma)

Without proper domain patterns, your system might suffer from:

1. **Data Race Conditions**:
   ```sql
   -- Race condition: Two shifts update inventory simultaneously
   UPDATE inventory SET quantity = quantity - 10 WHERE product_id = 123;
   -- Race 1 wins; Race 2 sees incorrect quantity
   ```
   This leads to **overdue orders** or **safety stock violations**.

2. **Inconsistent State Transitions**:
   ```go
   // Pseudo-code for production step approval
   func ApproveStep(ctx context.Context, stepID int) error {
       step := getStep(stepID) // Step 1: Approve raw material
       step.Status = "Approved" // Step 2: Update step
       _ = saveStep(step)      // Step 3: Save (race condition here)

       // Race 2: Step 1 is approved, but Step 2 is still pending
   }
   ```
   Orders get stuck in **limbo** because approvals are asynchronous.

3. **Poor Query Performance**:
   ```sql
   -- Brute-force query for production line efficiency
   SELECT * FROM production_steps
   JOIN orders ON production_steps.order_id = orders.id
   WHERE orders.customer_id = 42
     AND production_steps.status NOT IN ('completed', 'cancelled');
   ```
   On 100,000 orders, this query takes **60+ seconds**—far too slow for real-time dashboards.

4. **Lack of Auditability**:
   Without a **change log**, traceability is impossible. Regulators need to know *when* and *why* a batch was halted.

---

## The Solution: Structuring Manufacturing Workflows

The **Manufacturing Domain Pattern** combines:
- **Domain-Specific Events**: Replace direct queries with events (e.g., `OrderCreated`, `ProductionStepApproved`).
- **State Machines**: Model workflows as finite state machines (FSMs) to enforce valid transitions.
- **Optimized Repositories**: Denormalize critical data for performance.
- **Audit Tables**: Track all changes for compliance.

Let’s break this down with a practical example: a **pharmaceutical batch production system**.

---

## Core Components of the Pattern

### 1. **Event-Driven Workflows**
Use events to decouple state changes. Example:
```go
// Event types
type Event interface {
    Timestamp() time.Time
    OrderID() int
}

type OrderCreated struct {
    orderID    int
    timestamp  time.Time
}

type ProductionStepApproved struct {
    stepID     int
    orderID    int
    timestamp  time.Time
}

// Event store (simplified)
type EventStore struct {
    db *sql.DB
}

func (es *EventStore) Publish(e Event) error {
    _, err := es.db.Exec(`
        INSERT INTO events (event_type, payload, order_id)
        VALUES ($1, $2, $3)
    `, string(e.Type()), jsonBytes(e), e.OrderID())
    return err
}
```

**Tradeoff**: Events add latency but improve scalability. For critical paths, consider a **command query responsibility segregation (CQRS)** architecture.

---

### 2. **State Machines for Workflows**
Model production steps as an FSM:
```go
type ProductionStep struct {
    ID          int
    OrderID     int
    StepName    string // "Mix", "Heat", "Cool", "QC"
    CurrentState State // "raw_material", "processing", "completed"
    CreatedAt   time.Time
}

type State string

func (s *ProductionStep) Transition(nextState State) error {
    switch s.CurrentState {
    case "raw_material":
        if nextState != "processing" {
            return fmt.Errorf("invalid transition: %s -> %s", s.CurrentState, nextState)
        }
    case "processing":
        if nextState != "completed" && nextState != "rejected" {
            return fmt.Errorf("invalid transition: %s -> %s", s.CurrentState, nextState)
        }
    }
    s.CurrentState = nextState
    return nil
}
```

**Database backing**:
```sql
CREATE TABLE production_steps (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    step_name VARCHAR(50),
    current_state VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_step_order_state ON production_steps(order_id, current_state);
```

---

### 3. **Optimized Repositories for Performance**
For high-frequency reads, denormalize data:
```sql
-- Original normalized schema (slow for batch queries)
SELECT * FROM orders
JOIN production_steps ON orders.id = production_steps.order_id;

-- Optimized denormalized schema
CREATE TABLE order_stats (
    order_id INT PRIMARY KEY REFERENCES orders(id),
    steps_completed INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20)  -- "pending", "in_production", "completed"
);

-- Update stats in a separate transaction
INSERT INTO order_stats (order_id, status)
VALUES (42, 'in_production')
ON CONFLICT (order_id) DO UPDATE
SET status = 'in_production', last_updated = NOW();
```

---

### 4. **Audit Trails for Compliance**
```sql
CREATE TABLE production_audit (
    id SERIAL PRIMARY KEY,
    step_id INT REFERENCES production_steps(id),
    action VARCHAR(20),  -- "approved", "rejected", "reverted"
    changed_by VARCHAR(50),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    before_state JSONB,
    after_state JSONB
);
```

**Example INSERT**:
```go
// Log a state transition
_, err := db.Exec(`
    INSERT INTO production_audit (
        step_id, action,
        changed_by,
        before_state, after_state
    ) VALUES ($1, $2, $3, $4, $5)
`, step.ID, "approved", "system_user", oldState, newState)
```

---

## Implementation Guide: Step-by-Step

### Step 1: Define Core Entities and Events
```go
// Entities
type Order struct {
    ID        int
    Customer  int
    DueDate   time.Time
    Steps     []ProductionStep
}

// Events
type WorkflowEvent int

const (
    OrderSubmitted WorkflowEvent = iota
    StepCompleted
    BatchRejected
)
```

### Step 2: Set Up the Database Schema
```sql
-- Start with a clean slate
DROP SCHEMA IF EXISTS manufacturing CASCADE;
CREATE SCHEMA manufacturing;

-- Core tables
CREATE TABLE manufacturing.orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    due_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
);

CREATE TABLE manufacturing.production_steps (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES manufacturing.orders(id),
    step_name VARCHAR(50) NOT NULL,
    current_state VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Optimized denormalized table
CREATE TABLE manufacturing.order_stats (
    order_id INT PRIMARY KEY REFERENCES manufacturing.orders(id),
    steps_completed INT DEFAULT 0,
    status VARCHAR(20),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Audit trail
CREATE TABLE manufacturing.audit (
    id SERIAL PRIMARY KEY,
    step_id INT REFERENCES manufacturing.production_steps(id),
    action VARCHAR(20) NOT NULL,
    changed_by VARCHAR(50),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    before_state JSONB,
    after_state JSONB
);
```

### Step 3: Implement the State Machine Logic
```go
type ProductionStepMachine struct {
    db *sql.DB
}

func (m *ProductionStepMachine) ExecuteTransition(
    stepID int,
    action string,
    currentState State,
    nextState State,
    changedBy string,
) error {
    // Validate transition
    if err := m.validateTransition(currentState, nextState); err != nil {
        return err
    }

    // Get current state
    var current State
    err := m.db.QueryRow(`
        SELECT current_state FROM production_steps WHERE id = $1
    `, stepID).Scan(&current)
    if err != nil {
        return err
    }

    // Log the change
    _, err = m.db.Exec(`
        INSERT INTO audit (
            step_id, action, changed_by,
            before_state, after_state
        ) VALUES ($1, $2, $3, TO_JSONB($4::production_steps), TO_JSONB($5::production_steps))
    `, stepID, action, changedBy, current, nextState)
    if err != nil {
        return err
    }

    // Update step state
    _, err = m.db.Exec(`
        UPDATE production_steps
        SET current_state = $1, updated_at = NOW()
        WHERE id = $2
    `, nextState, stepID)
    return err
}

func (m *ProductionStepMachine) validateTransition(
    current State,
    next State,
) error {
    switch current {
    case "raw_material":
        if next != "processing" {
            return fmt.Errorf("invalid transition: %s -> %s", current, next)
        }
    case "processing":
        if next != "completed" && next != "rejected" {
            return fmt.Errorf("invalid transition: %s -> %s", current, next)
        }
    }
    return nil
}
```

### Step 4: Design the API Layer
Use **GraphQL** for flexible querying with **Materialized Paths** (e.g., `production_steps` filtered by `order_id` and `current_state`).
Example schema:
```graphql
type ProductionStep {
    id: Int!
    stepName: String!
    currentState: String!
    order: Order!
}

type Order {
    id: Int!
    customer: Customer!
    steps: [ProductionStep!]!
    stats: OrderStats!
}

type Query {
    getOrder(id: Int!): Order
    getOrderSteps(orderID: Int!): [ProductionStep!]!
    getProductionLineStats(): [OrderStats!]!
}
```

### Step 5: Handle Concurrency
Use **advisory locks** for critical sections:
```go
func (m *ProductionStepMachine) ApproveStep(stepID int) error {
    // Get advisory lock
    defer pgx.BeginTx(func(tx pgx.Tx) {
        // Check lock ownership
        if _, err := tx.Exec(`
            SELECT pg_advisory_xact_lock($1)
        `, stepID); err != nil {
            return err
        }
    })

    // Proceed with the transition
    return m.ExecuteTransition(stepID, "approved", "raw_material", "processing", "operator123")
}
```

---

## Common Mistakes to Avoid

1. **Overusing Transactions**
   - ❌ *Mistake*: Wrapping *every* step in a transaction.
   - ✅ *Fix*: Use **sagas** for long-running workflows (e.g., order processing), but keep individual steps lightweight.

2. **Ignoring Denormalization**
   - ❌ *Mistake*: Always prefer 3NF for manufacturing data (e.g., 10+ joins for simple queries).
   - ✅ *Fix*: Denormalize for performance-critical paths (e.g., shop floor dashboards).

3. **Poor Event Sourcing**
   - ❌ *Mistake*: Storing raw events in a text column without a schema.
   - ✅ *Fix*: Use a **polyglot persistence** approach (e.g., JSONB for flexible events + a dedicated event table for indexing).

4. **Insufficient Auditing**
   - ❌ *Mistake*: Only auditing final states (e.g., "batch completed").
   - ✅ *Fix*: Log **every** change, even intermediate states.

5. **Blocking APIs for Real-Time Updates**
   - ❌ *Mistake*: Polling the database every 50ms for IoT device updates.
   - ✅ *Fix*: Use **WebSockets** or **SSE** for push notifications.

---

## Key Takeaways

- **State Machines**: Enforce valid workflow transitions with FSMs.
- **Event-Driven**: Decouple state changes with events for scalability.
- **Optimize Queries**: Denormalize for performance-critical paths.
- **Audit Everything**: Compliance is non-negotiable; log all changes.
- **Handle Concurrency**: Use locks or CQRS for high-contention workflows.
- **API Flexibility**: GraphQL or REST with well-defined schemas.

---

## Conclusion: Building for Scale and Compliance

Manufacturing domain patterns aren’t a silver bullet, but they provide a **structured way to handle complexity** in production systems. By modeling workflows as state machines, decoupling changes with events, and optimizing for critical queries, you’ll build systems that:
- **Scale** under high load (e.g., thousands of concurrent production steps).
- **Resist corruption** with strict state transitions.
- **Meet compliance** with audit trails.
- **Adapt** to changing requirements (e.g., new FDA guidelines).

Start with a **small workflow** (e.g., batch approvals) and iterate. Tools like **PostgreSQL advisory locks**, **GraphQL subscriptions**, and **event stores** (e.g., EventStoreDB) will help you refine your approach.

For further reading:
- [Domain-Driven Design (DDD) Patterns](https://domainlanguage.com/ddd/) (Eric Evans)
- [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) (Martin Kleppmann)
- [PostgreSQL Advisory Locks](https://www.postgresql.org/docs/current/explicit-locking.html)

Now go build that **production-grade backend**!
```