```markdown
---
title: "Virtual-Machines Standards: Building Scalable Backend Systems with Reusable Logic"
date: 2023-11-15
author: "Alex Carter, Senior Backend Engineer"
tags: ["database design", "api patterns", "backend engineering", "scalability", "domain-driven design"]
description: "Learn how to implement the Virtual Machines Standards pattern to create modular, reusable, and maintainable backend logic that scales effortlessly."
---

# Virtual Machines Standards: Building Scalable Backend Systems with Reusable Logic

Backend systems often suffer from **tight coupling**, **redundant logic**, and **difficulty in maintenance** as they grow. Imagine a system where business rules are scattered across controllers, services, and repositories, making updates painful and scaling a nightmare. This is where the **Virtual Machines Standards (VMS) pattern** shines—it transforms brittle, monolithic code into modular, reusable, and scalable components by abstracting common logic into "virtual machines" (VMs) that can be composited and reused across your application.

The VMS pattern is inspired by **virtual machines in computing**—self-contained environments that encapsulate state and logic while allowing controlled interaction with the outside world. In backend design, it means building **standalone, composable logic units** (VMs) that handle workflows, validation, transformations, or business rules. Think of them as **Lego blocks for your backend**: swap, mix, and extend them as your needs change.

By the end of this post, you’ll understand how to design VMs that reduce duplication, improve testability, and make your system easier to scale. We’ll explore real-world examples in **Python, JavaScript, and SQL**, analyze tradeoffs, and provide a practical implementation guide.

---

## The Problem: Why Your System Might Be Breaking

Without proper virtual-machines standards, backend systems often face these challenges:

### 1. **Duplicated Logic**
   - The same validation, data transformation, or workflow logic exists in multiple places (e.g., API handlers, cron jobs, and CLI tools). Changes require updating every copy, increasing the risk of inconsistencies.
   - *Example*: A discount calculation rule is implemented in:
     - `OrderController.validateDiscount()`
     - `PromotionService.applyDiscount()`
     - `BatchProcessor.reapplyOldDiscounts()`

### 2. **Tight Coupling**
   - Components depend on each other’s implementations (e.g., a service calls a repository directly instead of through a VM). Changing one part breaks others.
   - *Example*: A `UserService` relies on `PostgreSQL` directly for complex queries, making it hard to switch to a caching layer or a different database.

### 3. **Poor Testability**
   - Logic is tightly woven into controllers or services, making unit tests fragile (e.g., mocking a database or external API is error-prone).
   - *Example*: Testing `OrderService.applyShippingRules()` requires spying on a legacy `ShippingCalculator` that has 500+ dependencies.

### 4. **Scalability Nightmares**
   - As traffic grows, scaling becomes harder because workflows are distributed across microservices or monoliths without clear boundaries.
   - *Example*: A "checkout workflow" splits logic between:
     - `CheckoutAPI` (HTTP layer)
     - `PaymentService` (external API calls)
     - `InventoryService` (database queries)
     - `EmailService` (async tasks)
   - Scaling one part requires rearchitecting the whole flow.

### 5. **Maintenance Hell**
   - Business rules evolve (e.g., new discounts, tax laws, or shipping policies), but updating them requires navigating a maze of interconnected code.
   - *Example*: Adding a "first-order discount" requires changes to:
     - Frontend form validation
     - API request/response schemas
     - Backend discount logic
     - Database triggers

---
## The Solution: Virtual Machines Standards

The **Virtual Machines Standards (VMS) pattern** addresses these issues by:
1. **Encapsulating logic** in standalone VMs that are self-contained and reusable.
2. **Defining clear interfaces** to interact with VMs, reducing coupling.
3. **Decoupling concerns** (e.g., validation, business rules, persistence) so they can be modified independently.
4. **Enabling composition**—VMs can be chained or embedded to build complex workflows.

### Core Principles:
- **Single Responsibility**: Each VM does one thing well (e.g., `DiscountCalculator`, `OrderValidator`, `ShippingPlanner`).
- **Local State**: VMs manage their own state to avoid shared mutable data.
- **Explicit Interaction**: VMs expose clear methods (e.g., `calculate()`, `validate()`, `execute()`) to interact with them.
- **Immutability**: Inputs to VMs are immutable to prevent side effects.
- **Composition Over Inheritance**: Build complex workflows by combining simpler VMs.

---

## Components/Solutions: The VMS Toolkit

To implement VMS, you’ll need these components:

### 1. **Virtual Machine (VM) Class**
   A standalone class that encapsulates a specific piece of logic. Example:
   ```python
   from dataclasses import dataclass
   from typing import Optional

   @dataclass
   class Order:
       items: list[dict]
       customer_id: str
       discount_code: Optional[str] = None

   class DiscountCalculatorVM:
       """Calculates discounts for an order."""

       def __init__(self, discount_rules: list[dict]):
           self.rules = discount_rules

       def calculate(self, order: Order) -> float:
           """Apply discount rules to the order."""
           total = sum(item["price"] * item["quantity"] for item in order.items)
           for rule in self.rules:
               if self._matches_rule(order, rule):
                   total *= (1 - rule["percentage"])
           return total

       def _matches_rule(self, order: Order, rule: dict) -> bool:
           """Check if the order matches a discount rule."""
           return (
               (not rule.get("customer_id") or order.customer_id == rule["customer_id"]) and
               (not rule.get("discount_code") or order.discount_code == rule["discount_code"])
           )
   ```

### 2. **Composite VMs**
   Combine simpler VMs to build complex workflows. Example: A `CheckoutWorkflowVM` that uses `DiscountCalculatorVM`, `ShippingPlannerVM`, and `OrderValidatorVM`.
   ```javascript
   class CheckoutWorkflowVM {
       constructor() {
           this.discountCalculator = new DiscountCalculatorVM();
           this.shippingPlanner = new ShippingPlannerVM();
           this.validator = new OrderValidatorVM();
       }

       async execute(orderData) {
           // Step 1: Validate
           const validationErrors = this.validator.validate(orderData);
           if (validationErrors.length > 0) {
               throw new Error(`Validation failed: ${validationErrors.join(", ")}`);
           }

           // Step 2: Calculate discount
           const discountedTotal = this.discountCalculator.calculate(orderData);

           // Step 3: Plan shipping
           const shippingCost = this.shippingPlanner.calculate(orderData);

           // Step 4: Return result
           return {
               total: discountedTotal + shippingCost,
               discountApplied: this.discountCalculator.getAppliedDiscount()
           };
       }
   }
   ```

### 3. **VM Registry**
   Centralize the creation and discovery of VMs. Example in Python:
   ```python
   from abc import ABC, abstractmethod
   from typing import Dict, Type

   class VMRegistry:
       def __init__(self):
           self._vms: Dict[str, Type] = {}

       def register(self, name: str, vm_class: Type):
           self._vms[name] = vm_class

       def create(self, name: str, **kwargs) -> object:
           return self._vms[name](**kwargs)

   # Usage:
   registry = VMRegistry()
   registry.register("discount_calculator", DiscountCalculatorVM)
   vm = registry.create("discount_calculator", discount_rules=[...])
   ```

### 4. **VM Context**
   Provide input/output channels for VMs. Example: A `VMContext` that holds shared state or dependencies.
   ```sql
   -- Example: A SQL-based VM context for persistence
   CREATE TABLE vm_contexts (
       id SERIAL PRIMARY KEY,
       name VARCHAR(50),
       data JSONB NOT NULL
   );

   -- VM could interact with this via a repository:
   INSERT INTO vm_contexts (name, data)
   VALUES ('current_order', '{"customer_id": "123", "items": [...]}')
   ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data;
   ```

### 5. **VM Orchestrator**
   Coordinate the execution of VMs in sequence. Example in TypeScript:
   ```typescript
   interface VMOrchestrator {
       run(workflow: string, input: any): Promise<any>;
   }

   class DiscountWorkflowOrchestrator implements VMOrchestrator {
       async run(workflow: string, input: OrderData): Promise<OrderResult> {
           const vm1 = new DiscountCalculatorVM();
           const vm2 = new ShippingPlannerVM();

           const discount = await vm1.calculate(input);
           const shipping = await vm2.calculate(input);

           return { total: discount + shipping, discount };
       }
   }
   ```

---
## Practical Code Examples

### Example 1: Python – Discount Calculator VM
Let’s build a `DiscountCalculatorVM` that applies rules based on customer tiers and discount codes.

```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class OrderItem:
    product_id: str
    price: float
    quantity: int

@dataclass
class Order:
    items: List[OrderItem]
    customer_id: str
    discount_code: Optional[str] = None
    customer_tier: Optional[str] = None  # e.g., "silver", "gold"

class DiscountCalculatorVM:
    def __init__(self, rules: List[Dict]):
        self.rules = rules  # Rules like {"type": "code", "code": "SUMMER20", "percentage": 0.15}

    def calculate(self, order: Order) -> float:
        total = sum(item.price * item.quantity for item in order.items)

        # Apply tier-based discounts first
        tier_discount = self._apply_tier_discount(order, total)
        total *= (1 - tier_discount)

        # Apply code-based discounts
        code_discount = self._apply_code_discount(order, total)
        total *= (1 - code_discount)

        return total

    def _apply_tier_discount(self, order: Order, total: float) -> float:
        if not order.customer_tier:
            return 0.0

        for rule in self.rules:
            if (
                rule.get("type") == "tier" and
                order.customer_tier == rule["tier"] and
                "percentage" in rule
            ):
                return rule["percentage"]
        return 0.0

    def _apply_code_discount(self, order: Order, total: float) -> float:
        for rule in self.rules:
            if (
                rule.get("type") == "code" and
                order.discount_code == rule["code"] and
                "percentage" in rule
            ):
                return rule["percentage"]
        return 0.0
```

**Usage:**
```python
rules = [
    {"type": "tier", "tier": "gold", "percentage": 0.20},
    {"type": "code", "code": "SUMMER20", "percentage": 0.15}
]

vm = DiscountCalculatorVM(rules)
order = Order(
    items=[OrderItem("prod-1", 100.0, 2)],
    customer_id="user-456",
    discount_code="SUMMER20",
    customer_tier="gold"
)
print(f"Total: ${vm.calculate(order):.2f}")  # Output: $144.00 (20% + 15% applied)
```

---

### Example 2: JavaScript – Order Validator VM
A VM that validates an order before processing.

```javascript
class OrderValidatorVM {
    constructor(validationRules) {
        this.rules = validationRules; // e.g., [{ field: "items", required: true }]
    }

    validate(orderData) {
        const errors = [];

        this.rules.forEach(rule => {
            const { field, required, minItems, maxItems } = rule;
            if (required && !orderData[field]?.length) {
                errors.push(`Missing required field: ${field}`);
            }

            if (minItems !== undefined && orderData[field]?.length < minItems) {
                errors.push(`${field} must have at least ${minItems} items`);
            }

            if (maxItems !== undefined && orderData[field]?.length > maxItems) {
                errors.push(`${field} cannot exceed ${maxItems} items`);
            }
        });

        return errors;
    }
}

// Usage:
const validator = new OrderValidatorVM([
    { field: "items", required: true, minItems: 1 },
    { field: "customer_id", required: true },
    { field: "items", maxItems: 10 }
]);

const orderData = {
    items: [{ product: "laptop", price: 999.99 }],
    customer_id: "user-123"
};

const errors = validator.validate(orderData);
if (errors.length > 0) {
    console.error("Validation failed:", errors);
} else {
    console.log("Order is valid!");
}
```

---

### Example 3: SQL – VM for Database Operations
A VM that handles complex database operations (e.g., bulk updates with transactions).

```sql
-- Step 1: Create a VM-like function to update orders with discounts
CREATE OR REPLACE FUNCTION apply_discount_to_orders(
    p_discount_percentage NUMERIC,
    p_customer_ids VARCHAR[]
) RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- Start a transaction
    BEGIN
        -- Update orders for specific customers
        UPDATE orders
        SET total = total * (1 - p_discount_percentage),
            last_updated = NOW()
        WHERE customer_id = ANY(p_customer_ids)
        RETURNING COUNT(*) INTO updated_count;

        -- Log the operation
        INSERT INTO vm_audit_logs (
            vm_name, action, params, timestamp
        )
        VALUES (
            'discount_updater',
            'apply_discount',
            to_jsonb(ARRAY[
                to_jsonb('discount_percentage'::NUMERIC, p_discount_percentage),
                to_jsonb('customer_ids'::VARCHAR[], p_customer_ids)
            ]),
            NOW()
        );

        COMMIT;
        RETURN updated_count;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE NOTICE 'VM failed: %', SQLERRM;
            RETURN 0;
    END;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Call the VM from application code (e.g., Python)
import psycopg2

def apply_discount_to_customers(discount: float, customer_ids: list[str]):
    conn = psycopg2.connect("dbname=orders user=postgres")
    try:
        with conn.cursor() as cur:
            cur.callproc("apply_discount_to_orders", [discount, customer_ids])
        conn.commit()
        print(f"Updated {cur.fetchone()[0]} orders.")
    except Exception as e:
        conn.rollback()
        print(f"VM failed: {e}")
    finally:
        conn.close()
```

---

## Implementation Guide: Steps to Adopt VMS

### Step 1: Identify VM Candidates
   - Look for **repeated logic** (e.g., discount calculations, validations).
   - Target **complex workflows** (e.g., checkout, payment processing).
   - Avoid overusing VMs for **trivial logic** (e.g., simple Get/Set operations).

### Step 2: Define VM Interfaces
   - Each VM should have:
     - A clear **input type** (e.g., `Order`, `UserProfile`).
     - Explicit **methods** (e.g., `calculate()`, `validate()`).
     - A **single responsibility**.

   *Example interface for a `ShippingPlannerVM`:*
   ```python
   class ShippingPlannerVM:
       def calculate(self, order: Order) -> dict:
           """Returns { 'cost': float, 'estimated_delivery': str }"""
       def apply_discount(self, order: Order, discount_code: str) -> float:
           """Applies shipping discount if eligible."""
   ```

### Step 3: Implement VMs Independently
   - Write VMs **without dependencies** on other services or databases.
   - Use **dependency injection** (e.g., pass a repository to a VM rather than hardcoding it).

   *Example: Pass a `DiscountRepository` to `DiscountCalculatorVM`:*
   ```python
   class DiscountCalculatorVM:
       def __init__(self, repository: DiscountRepository):
           self.repository = repository

       def calculate(self, order: Order) -> float:
           active_discounts = self.repository.fetch_active_discounts()
           # ... apply discounts ...
   ```

### Step 4: Compose VMs into Workflows
   - Chain VMs together for complex workflows.
   - Use a **VM orchestrator** to manage sequencing and error handling.

   *Example workflow in JavaScript:*
   ```javascript
   class CheckoutWorkflowVM {
       constructor() {
           this.steps = [
               new OrderValidatorVM(),
               new DiscountCalculatorVM(),
               new ShippingPlannerVM(),
               new PaymentProcessorVM()
           ];
       }

       async run(orderData) {
           try {
               for (const step of this.steps) {
                   await step.validate(orderData);
               }
               const result = await this.steps.reduce(async (acc, step) => {
                   const data = await acc;
                   return step.execute(data);
               }, orderData);
               return result;
           } catch (error) {
               console.error("Workflow failed:", error);
               throw error;
           }
       }
   }
   ```

### Step 5: Integrate VMs with Your System
   - **API Layer**: Expose VMs as endpoints (e.g., `/api/v1/orders/calculate-discount`).
   - **Background Jobs**: Run VMs asynchronously (e.g., with Celery or BullMQ).
   - **Database**: Use VMs to define stored procedures or complex queries.

   *Example API endpoint:*
   ```python
   from fastapi import API