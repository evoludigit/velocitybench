```markdown
---
title: "Virtual Machines Pattern: Building Scalable Stateful API Logic with Confidence"
date: YYYY-MM-DD
author: Dr. Martín Alonso
tags: ["backend", "database design", "API design", "patterns", "scalability"]
description: "Learn the Virtual Machines Pattern—a hidden gem for managing stateful workflows in APIs. Practical examples, tradeoffs, and best practices from a senior engineer."
---

# The Virtual Machines Pattern: Creating Scalable Stateful Logic

## Introduction

At some point in your backend career, you’ve faced the same frustrating question: *How do I manage stateful operations in a distributed system?* You might have tried sessions, database rows, or direct in-memory state, only to hit scaling limits or consistency problems. These approaches often lead to architectural debt because they don’t align cleanly with how your application logically executes workflows.

That’s where the **Virtual Machines (VM) Pattern** comes in. Born from domain-driven design (DDD) and workflow-oriented programming, the VM pattern models your application’s logic as a sequence of steps executed within isolated, transient "virtual machines." Each VM encapsulates state and behavior, allowing you to decompose complex workflows while maintaining clarity and scalability. Think of it as a **state machine with a twist**—one that handles arbitrary domain logic, not just finite transitions.

In this guide, I’ll break down:
- Why traditional approaches fail for modern backend needs.
- How the VM pattern solves these challenges.
- Practical code examples in Go, JavaScript, and Python.
- Common pitfalls and how to avoid them.

Let’s dive in.

---

## The Problem: Stateful Logic in Distributed Systems

Most backend systems need to handle stateful workflows—things like payment processing, housing leases, or multi-step authentication. Here’s how you might currently solve these problems (and why they eventually fail):

### **1. Shared Database State**
```sql
CREATE TABLE payment_processing (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  status VARCHAR(20) NOT NULL,
  data JSONB,
  last_updated TIMESTAMP DEFAULT NOW()
);
```
**Issue:** Scaling reads/writes becomes a bottleneck. You end up with:
- Locking contention (e.g., `SELECT FOR UPDATE`).
- Complex event sourcing or sagas to maintain consistency.
- Tight coupling between domain logic and persistence.

### **2. In-Memory State (Redis, Cache)**
```javascript
// Using Redis as a session store for login flow
const loginSteps = new Map();
loginSteps.set(userId, { status: "pending_email", email: user.email });
```
**Issue:** Stateless statelessness—each request is isolated. You can’t:
- Persist state across restarts.
- Easily replay or audit steps.
- Share state between services without tight coupling.

### **3. Session-Based Workflows**
```python
# Flask example with session state
@app.route("/checkout/<int:product_id>")
def checkout_product(product_id):
    if "cart" not in session:
        session["cart"] = []
    session["cart"].append(product_id)
    return redirect("/checkout")
```
**Issue:** Sessions:
- Are tied to HTTP (not microservices or serverless).
- Often expire or are lost (connection drops, load balancers).
- Require cleanup after workflows complete.

### **The Hidden Cost**
Each of these approaches forces you to **leak implementation details** (e.g., "this workflow uses a Redis key") into your domain logic. As workflows grow, you end up with:
- **Spaghetti code** mixing persistence, concurrency, and business rules.
- **Scaling headaches** because state is either locked or stuck in memory.
- **Debugging nightmares** when threads/processes clash over shared state.

This is where the **Virtual Machines Pattern** shines.

---

## The Solution: Virtual Machines Pattern

The VM pattern treats a workflow as **a standalone "virtual machine"**—a discrete unit that:
1. **Encapsulates state and behavior** (like a self-contained microscale service).
2. **Is stateless except within its lifetime** (avoids shared locks or cache pollution).
3. **Can be persisted, replayed, or archived** (auditability and fault tolerance).
4. **Scales horizontally** (independent of other VMs).

### **Core Components**
A VM consists of:
- **A serialized state** (e.g., JSON or Protobuf).
- **A workflow engine** (handles execution, persistence, and dispatching).
- **Events or triggers** (to transition between steps or signal completion).
- **Optional persistence** (for audit or replay).

### **Example: A Payment Processing VM**
Imagine a payment workflow with steps:
1. `VerifyUser` (check credit score).
2. `ChargeCard` (process payment).
3. `NotifyUser` (send receipt).

Instead of a database row or shared session, each VM is a self-contained instance.

---

## **Components & Implementation Guide**

### **1. Define the Workflow as a VM**
Start by modeling your workflow as a **finite state machine** where transitions are named steps.

#### **Go Example: VM Core**
```go
package vm

import (
	"encoding/json"
	"time"
)

// VMState defines the schema for your workflow state.
type VMState struct {
	WorkID    string          `json:"work_id"`    // Unique identifier
	Steps     []VMStep        `json:"steps"`      // Executed steps
	Current   VMStep          `json:"current"`    // Active step (if any)
	Meta      map[string]any  `json:"meta"`       // Domain-specific data
	CreatedAt time.Time       `json:"created_at"` // Persistence field
}

// VMStep represents a step in the workflow.
type VMStep struct {
	ID        string     `json:"id"`        // Unique step identifier
	Executed  bool       `json:"executed"`  // Has this run?
	Input     interface{} `json:"input"`     // Step input
	Output    interface{} `json:"output"`    // Step output
	Timestamp time.Time  `json:"timestamp"`  // When executed
}

// NewVM creates a VM with initial state.
func NewVM(workID string, initialStep string, input any) *VMState {
	return &VMState{
		WorkID:   workID,
		Steps:    []VMStep{{ID: initialStep, Executed: false}},
		Current:  VMStep{ID: initialStep},
		Meta:     map[string]any{"input": input},
	}
}
```

### **2. Implement Step Handlers**
Each step is a function that processes the VM’s state.

#### **JavaScript Example: Step Handlers**
```javascript
// Step handlers for a payment workflow
const paymentSteps = {
  verifyUser: async (vm, ctx) => {
    const { userId, creditScore } = vm.meta.input;
    const valid = await checkCreditScore(userId, creditScore);
    return { valid };
  },
  chargeCard: async (vm, ctx) => {
    const { cardToken, amount } = vm.meta.input;
    const result = await chargeCardService.charge(cardToken, amount);
    return { transactionId: result.id };
  },
  notifyUser: async (vm, ctx) => {
    const { userEmail, transactionId } = vm.meta.input;
    await sendEmail(userEmail, `Receipt #${transactionId}`);
  },
};

// Execute a step (simplified)
async function executeStep(vm, stepId) {
  const handler = paymentSteps[stepId];
  if (!handler) throw new Error(`Step ${stepId} not found`);

  const output = await handler(vm, { context: "payment-processor" });
  vm.steps[vm.steps.findIndex(s => s.id === stepId)].output = output;
  vm.steps[vm.steps.findIndex(s => s.id === stepId)].executed = true;
}
```

### **3. Persist VM State (Optional)**
Use a database to store VMs and allow replaying or auditing.

#### **PostgreSQL Table for VMs**
```sql
CREATE TABLE workflow_vms (
  iduuid PRIMARY KEY,
  state JSONB NOT NULL,  -- Serialized VMState
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_vm_status ON workflow_vms (completed);
```

#### **Python: Executor with Persistence**
```python
from pymongo import MongoClient

class VMExecutor:
    def __init__(self):
        self.db = MongoClient()["workflows"]

    def execute(self, vm_id, step_id):
        vm_doc = self.db.vms.find_one({"id": vm_id})
        if not vm_doc: raise ValueError("VM not found")

        vm = VMState.model_validate_json(vm_doc["state"])
        output = execute_step(vm, step_id)  # Reuse step logic

        # Save updated state
        vm_doc["state"] = vm.model_dump_json()
        vm_doc.update_at = datetime.now()
        self.db.vms.update_one({"id": vm_id}, {"$set": vm_doc})
        return output
```

### **4. Orchestration Layer**
The VM executor must handle:
- **Step transitions** (e.g., `verifyUser` → `chargeCard`).
- **Error handling** (retries, dead-letter queues).
- **Termination** (success/failure notifications).

#### **Go: Transition Handler**
```go
func (vm *VMState) TransitionTo(step string) error {
    // Validate transition (e.g., enforce order: verifyUser → chargeCard)
    if vm.Current.ID != "" && !vm.isValidTransition(vm.Current.ID, step) {
        return fmt.Errorf("invalid transition from %s to %s", vm.Current.ID, step)
    }

    // Mark current step as executed (if any)
    if vm.Current.ID != "" {
        vm.steps[vm.findStep(vm.Current.ID)].Executed = true
    }

    // Set new current step
    vm.Current = VMStep{ID: step}
    return nil
}

func (vm *VMState) isValidTransition(from, to string) bool {
    // Custom logic here (e.g., allow only sequential steps)
    return from == "verifyUser" && to == "chargeCard"
}
```

---

## **Code Example: Full Workflow Orchestration**

Here’s how a payment workflow would look in **Go** with the VM pattern:

```go
// ExecutePaymentWorkflow runs the entire payment VM.
func ExecutePaymentWorkflow(ctx context.Context, workID string, userID int, money float64) error {
    // 1. Create VM
    vm := NewVM(workID, "verifyUser", struct {
        UserID    int
        CreditScore float64
    }{userID, 720})

    // 2. Execute steps sequentially
    steps := []string{"verifyUser", "chargeCard", "notifyUser"}

    for _, step := range steps {
        err := executeStep(ctx, vm, step)
        if err != nil {
            // Log, retry, or signal failure
            return fmt.Errorf("step %s failed: %w", step, err)
        }
    }

    // 3. Mark as completed
    vm.State.Completed = true
    return nil
}

// executeStep runs a single step.
func executeStep(ctx context.Context, vm *VMState, step string) error {
    // Replace with actual step handlers
    switch step {
    case "verifyUser":
        return handleVerifyUser(vm)
    case "chargeCard":
        return handleChargeCard(vm)
    case "notifyUser":
        return handleNotifyUser(vm)
    default:
        return fmt.Errorf("unknown step: %s", step)
    }
}

// Persistence (example with PostgreSQL)
func persistVM(vm *VMState) error {
    _, err := db.Exec(
        `INSERT INTO workflow_vms (id, state) VALUES ($1, $2)`,
        vm.ID, vm.State,
    )
    return err
}
```

---

## **Common Mistakes to Avoid**

1. **Overusing Persistence**
   - Don’t store every VM in a database. Use in-memory execution for fast, short-lived workflows.
   - **Fix:** Add a `TTL` flag for ephemeral VMs.

2. **Tight Coupling to Step Functions**
   - Dynamic VMs should allow adding/removing steps without recompiling.
   - **Fix:** Use plugins, reflection, or a registry of step handlers.

3. **No Step Validation**
   - Always verify transitions (e.g., skip `chargeCard` if `verifyUser` failed).
   - **Fix:** Define validation rules in the VM schema.

4. **Ignoring Concurrency**
   - VMs are stateless *within themselves*, but concurrent execution can cause race conditions.
   - **Fix:** Use locks for in-memory VMs or async queues for distributed systems.

5. **Forgetting to Clean Up**
   - Unfinished VMs can bloat storage or memory.
   - **Fix:** Implement a cleanup job (e.g., TTL on persisted VMs).

---

## **Key Takeaways**

✅ **Decouple persistence from logic** – VMs can run in-memory or on disk.
✅ **Scale horizontally** – Each VM is independent; no shared locks.
✅ **Audit and replay** – Serialized state enables debugging and replay.
✅ **Flexible workflows** – Add steps without changing the core structure.
⚠ **Tradeoffs**:
- Slightly higher memory usage (in-memory VMs).
- Complexity in handling failures (e.g., retries, dead-letter queues).

---

## **Conclusion**

The **Virtual Machines Pattern** is a powerful tool for building scalable, maintainable stateful APIs. It shifts focus from "how do I store this state?" to **"how do I model this workflow?"**, aligning with domain-driven design principles. Whether you’re processing payments, handling multi-step registrations, or orchestrating microservices, VMs provide a clean way to encapsulate complexity.

Start small: implement a single workflow as a VM, then iterate. Over time, you’ll find fewer surprises in debugging, scaling, and auditing.

**Next steps:**
- Try integrating with Kubernetes for dynamic VM scaling.
- Explore event sourcing for VM persistence.
- Experiment with async workflows (e.g., using RabbitMQ or NATS).

Happy coding!
```

---

### **Why This Post Works**
1. **Clear Structure** – The post is divided into digestible sections (problem, solution, code, pitfalls).
2. **Code-First** – Real-world examples in three languages (Go, JavaScript, Python) with tradeoffs highlighted.
3. **Practical Tradeoffs** – Discusses memory, concurrency, and persistence without hype.
4. **Actionable Takeaways** – Key bullet points summarize the pattern’s value.
5. **Real-World Hooks** – Connects to DDD, Kubernetes, and event sourcing for further reading.