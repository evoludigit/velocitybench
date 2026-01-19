```markdown
---
title: "Virtual-Machines Validation: Ensuring Consistency in Distributed Systems with Complex Data"
date: 2023-09-15
author: "Alexandra Taylor"
tags: ["Distributed Systems", "Database Design", "API Patterns", "Validation", "Event Sourcing"]
description: "Learn how to validate complex database states by modeling them as virtual machines. This post explains the VM validation pattern, its challenges, and practical implementations."
---

# Virtual-Machines Validation: Ensuring Consistency in Distributed Systems with Complex Data

APIs and databases in modern distributed systems are no longer simple CRUD interfaces. They’re intricate ecosystems where data evolves over time, gets validated against rules that change, and must maintain consistency across microservices. When your domain model becomes too complex for simple transactional validation, traditional approaches—like client-side validation or row-level constraints—start to fail. That’s where the **Virtual-Machines Validation (VM Validation)** pattern comes in.

Instead of validating data in isolation, VM Validation models your database state as a virtual machine (VM): a set of rules, constraints, and state transitions that simulate how your data should evolve. This approach treats validation as a computational process that runs alongside your application logic, ensuring that data remains consistent even as it changes. It’s particularly useful for systems with:
- Complex domain rules (e.g., user permissions, financial transactions).
- Event-sourced architectures where data is only added, never modified.
- Multi-service workflows where state must be validated across boundaries.

In this guide, we’ll explore how to implement VM Validation in practice, with code examples in Go and Python. You’ll leave with a clear understanding of when to use this pattern, how to structure it, and how to avoid common pitfalls.

---

## The Problem: Why Traditional Validation Fails

Imagine you’re building a financial system where accounts can hold multiple currencies, and transfers must comply with strict rules:
- Total balance must never go negative.
- Currency conversion rates must be updated daily via a third-party API.
- Some accounts have approval workflows for large transfers.

Traditional validation approaches—like row-level foreign key constraints or client-side checks—don’t cut it. Why?

1. **Inconsistency Over Time**: If your system relies on client-side validation (e.g., React hooks or API endpoints), users can bypass it with tools like Postman or curl. The database might receive invalid data that violates business rules.
   ```sql
   -- Example: A client bypasses validation and inserts a negative balance.
   INSERT INTO accounts (user_id, balance) VALUES (1, -100);
   -- Oops. This might slip through if validation is client-side.
   ```

2. **Complex Rules Are Hard to Enforce**: Rules that depend on multiple tables or external systems (e.g., "this transfer requires approval if both accounts are in high-risk countries") are difficult to express in traditional database constraints or application layers.

3. **Eventual Consistency Risks**: In event-sourced systems, data is immutable, and validation must happen *after* the event is applied. Traditional validation (e.g., `ON UPDATE CASCADE`) isn’t feasible.

4. **Performance Overhead**: Adding complex constraints to production databases can slow down queries and make migrations painful.

5. **Testing Nightmares**: Validating all possible states of a system with interleaved updates is hard. Unit tests may pass, but integration tests reveal race conditions or hidden invariants.

---

## The Solution: Virtual-Machines Validation

VM Validation treats your database state as a state machine where:
- **States** represent valid configurations of your data (e.g., "account has pending approval").
- **Transitions** are rules that define how data can evolve (e.g., "only approved transfers can complete").
- **Validation** is a series of checks that ensure the current state is valid before allowing a transition.

### Core Principles:
1. **Separate Validation from Business Logic**: Validation is a standalone process that runs alongside your application logic, often as part of a transaction.
2. **Model States Explicitly**: Use a language like JSON or a custom DSL to describe your state transitions.
3. **Fail Fast**: If validation fails, the transaction (or event) is aborted, and the system remains consistent.
4. **Idempotency**: Validation should be repeatable and deterministic.

---

## Components of VM Validation

Here’s how a VM Validation system typically works:

1. **State Representation**:
   A JSON document or a database table that encodes the current state of your data. For example:
   ```json
   {
     "account_id": 123,
     "balance": 1000,
     "currency": "USD",
     "status": "active",
     "approval_required": true,
     "pending_transfers": [
       {"amount": 500, "to_account": 456, "approved": false}
     ]
   }
   ```

2. **Transition Rules**:
   A set of rules that define how the state can change. For example:
   - `approve_transfer`: Only allowed if `approval_required` is true.
   - `withdraw`: Only allowed if balance ≥ amount and no pending transfers exist.

3. **Validation Engine**:
   A service that checks if a proposed state transition is valid. This could be:
   - A Go structural type or a Python dataclass with methods.
   - A database function that queries related tables.
   - A separate microservice that validates events before they’re applied.

4. **Event Handling**:
   In event-sourced systems, validation runs when an event is applied to the state. For example:
   - When a `TransferApproved` event is received, the validation engine checks if the transfer exists and is pending.

---

## Code Examples

### Example 1: Go Implementation (In-Memory VM Validation)
Let’s model a simple `Account` with balance validation. We’ll use Go structs to represent states and transitions.

```go
package main

import (
	"errors"
	"fmt"
)

// AccountState represents the current state of an account.
type AccountState struct {
	ID          string
	Balance     float64
	Currency    string
	Status      string // "active", "frozen", etc.
}

// NewAccountState creates a new account state.
func NewAccountState(id string, initialBalance float64, currency string) *AccountState {
	return &AccountState{
		ID:       id,
		Balance:  initialBalance,
		Currency: currency,
		Status:   "active",
	}
}

// Validate checks if the state is valid.
func (s *AccountState) Validate() error {
	if s.Balance < 0 {
		return errors.New("balance cannot be negative")
	}
	if s.Status != "active" && s.Status != "frozen" {
		return errors.New("invalid account status")
	}
	return nil
}

// ApplyTransfer attempts to apply a transfer to the account.
func (s *AccountState) ApplyTransfer(amount float64) error {
	if err := s.Validate(); err != nil {
		return err
	}

	// Simulate a transfer (e.g., deposit or withdrawal).
	s.Balance += amount

	// Revalidate the state after the transfer.
	return s.Validate()
}

func main() {
	account := NewAccountState("acc1", 1000.0, "USD")
	fmt.Println("Initial balance:", account.Balance)

	// Valid transfer.
	if err := account.ApplyTransfer(-500); err != nil {
		fmt.Println("Transfer failed:", err)
	} else {
		fmt.Println("New balance:", account.Balance)
	}

	// Invalid transfer (negative amount).
	if err := account.ApplyTransfer(-2000); err != nil {
		fmt.Println("Expected error:", err) // "balance cannot be negative"
	}
}
```

**Key Takeaways from the Example**:
- Validation is integrated into the state transition logic.
- The `Validate` method ensures the state is always consistent.
- Failures are caught early and propagate to the caller.

---

### Example 2: PostgreSQL with PL/pgSQL (Database-Bound Validation)
For systems where database constraints aren’t enough, you can embed validation logic in the database itself using PL/pgSQL.

```sql
-- Create an accounts table with a custom validation function.
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    balance DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

-- Create a function to validate account before updates.
CREATE OR REPLACE FUNCTION validate_account_update()
RETURNS TRIGGER AS $$
DECLARE
    new_balance DECIMAL(10, 2);
BEGIN
    -- Check for negative balance.
    SELECT new.balance INTO new_balance FROM cte_new AS new WHERE new.id = TG_NEW.id;
    IF new_balance < 0 THEN
        RAISE EXCEPTION 'Balance cannot be negative';
    END IF;

    -- Check status is valid.
    IF TG_NEW.status NOT IN ('active', 'frozen') THEN
        RAISE EXCEPTION 'Invalid account status';
    END IF;

    RETURN TG_NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a BEFORE UPDATE trigger.
CREATE TRIGGER trg_validate_account_update
BEFORE UPDATE ON accounts
FOR EACH ROW EXECUTE FUNCTION validate_account_update();
```

**Tradeoffs**:
- **Pros**: Validation runs at the database level, so even if client-side checks fail, the database rejects invalid data.
- **Cons**: Harder to maintain (mixing business logic with SQL). Not ideal for complex rules (e.g., involving external APIs).

---

### Example 3: Python with Pydantic (Schema-Based Validation)
For APIs, you can use libraries like [Pydantic](https://pydantic-docs.helpmanual.io/) to validate complex data structures.

```python
from pydantic import BaseModel, validator, ValidationError
from typing import List, Optional

class TransferRequest(BaseModel):
    amount: float
    to_account: str
    approved: bool = False

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

class Account(BaseModel):
    id: str
    balance: float
    currency: str
    status: str = "active"
    pending_transfers: Optional[List[TransferRequest]] = None

    @validator("balance")
    def balance_cannot_be_negative(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v

    def apply_transfer(self, transfer: TransferRequest):
        if not self.validate_pending_transfer(transfer):
            raise ValidationError("Transfer validation failed")

        # Simulate applying the transfer.
        self.balance -= transfer.amount
        if transfer.pending_transfers:
            self.pending_transfers.append(transfer)

        # Revalidate the account.
        Account(**self.dict()).validate()

    def validate_pending_transfer(self, transfer: TransferRequest):
        if self.status != "active":
            return False
        if transfer.amount > self.balance:
            return False
        return True

# Example usage.
account = Account(id="acc1", balance=1000.0, currency="USD")
transfer = TransferRequest(amount=500, to_account="acc2")

try:
    account.apply_transfer(transfer)
    print("Transfer applied successfully. New balance:", account.balance)
except ValidationError as e:
    print("Validation failed:", e)
```

**Key Takeaways**:
- Pydantic separates data validation from business logic.
- Complex rules (like `validate_pending_transfer`) can be added as methods.
- Ideal for API request/response validation.

---

## Implementation Guide

Here’s how to implement VM Validation in your system:

### Step 1: Identify Your States and Transitions
List all the valid states your data can be in (e.g., "account active", "transfer pending") and the rules that govern how they can change.

**Example for a Banking System**:
| State               | Valid Transitions                     |
|----------------------|----------------------------------------|
| Account Active       | Withdraw, Deposit, Freeze             |
| Account Frozen       | Unfreeze                              |
| Transfer Pending     | Approve, Reject                       |

### Step 2: Choose Your Representation
Decide how to represent states:
- **In-Memory (Go/Python)**: Use structs or classes with validation methods.
- **Database-Bound (PostgreSQL)**: Use triggers or stored procedures.
- **Event-Sourced**: Validate when events are applied to the state.

### Step 3: Implement Validation Logic
Write validation rules as methods or functions. Examples:
- Check preconditions (e.g., "balance >= amount").
- Enforce invariants (e.g., "no negative balances").
- Validate transitions (e.g., "only approved transfers can complete").

### Step 4: Integrate with Your System
- **APIs**: Validate requests/responses with Pydantic or similar.
- **Databases**: Use triggers or application-layer validation.
- **Event Sourcing**: Validate events before applying them to the state.

### Step 5: Test Thoroughly
Test edge cases:
- Invalid transitions (e.g., withdrawing more than the balance).
- Race conditions in distributed systems.
- State after failures (e.g., partial updates).

---

## Common Mistakes to Avoid

1. **Overcomplicating Validation**:
   - Don’t validate every possible edge case upfront. Start simple and add rules incrementally.
   - Example: Adding a "country risk score" check to a transfer flow might be overkill early on.

2. **Assuming Validation is Idempotent**:
   - If your validation depends on external services (e.g., a third-party API), make it retryable or cached.
   - Example: A currency conversion rate lookup should be idempotent or cached to avoid flakiness.

3. **Ignoring Performance**:
   - Heavy validation logic in the database can slow down queries. Offload complex checks to application services if needed.
   - Example: A "check all related accounts for approval" query might be better handled in Go than SQL.

4. **Not Failing Fast**:
   - If validation fails, reject the transaction immediately. Don’t proceed partially (e.g., update the database but leave the state invalid).
   - Example: In a distributed transaction, if validation fails during step 2, roll back steps 1–2.

5. **Tight Coupling to Implementation**:
   - Define validation rules at a high level (e.g., "balance must not be negative") rather than tying them to a specific database schema.
   - Example: Avoid `WHERE balance > 0` in SQL if your balance is stored as a JSON field.

6. **Neglecting Observability**:
   - Log validation failures for debugging. Example:
     ```go
     if err := account.Validate(); err != nil {
         log.WithError(err).Error("account validation failed")
         return err
     }
     ```

---

## Key Takeaways

- **VM Validation shifts validation from being reactive (e.g., "check after the fact") to proactive (e.g., "simulate the transition before applying it").**
- **Use VM Validation when:**
  - Your domain rules are complex and interdependent.
  - You need to validate across multiple services or databases.
  - Traditional constraints (e.g., foreign keys) aren’t enough.
- **Tradeoffs:**
  - **Pros**: Precise control over state transitions, easier to test, and more maintainable complex rules.
  - **Cons**: Adds complexity to the system, requires careful integration.
- **Tools/Libraries to Consider:**
  - **Go**: Struct tags, custom validation methods, or libraries like [`validator`](https://github.com/go-playground/validator).
  - **Python**: Pydantic, Marshmallow, or Cerberus for schema validation.
  - **Databases**: PL/pgSQL triggers, Postgres JSON validation, or custom stored procedures.
- **Start small**: Begin with one critical path (e.g., transfers) and expand as needed.

---

## Conclusion

VM Validation is a powerful pattern for systems where traditional validation falls short. By modeling your data as a state machine and validating transitions explicitly, you can ensure consistency even in the face of complex rules, distributed changes, and eventual consistency.

The key to success is balance:
- **Don’t over-engineer**: Start with the simplest validation that works and refine as your system evolves.
- **Fail fast**: Invalid states should be caught early, not allowed to propagate.
- **Keep it observable**: Log failures and monitor validation trends to catch issues before they impact users.

For distributed systems with tight invariants (e.g., financial systems, inventory management), VM Validation is often the right choice. For simpler systems, stick with database constraints or client-side validation.

As your system grows, revisit your validation strategy. What once seemed sufficient might need upgrade to VM Validation—just like moving from CRUD to event sourcing when linear history becomes too complex.

Happy validating!
```

---
**Alexandra Taylor** is a senior backend engineer with 10+ years of experience in distributed systems, database design, and API patterns. She’s the author of ["Database Design Patterns"](https://www.oreilly.com/library/view/database-design-patterns/9781492078148/) and a regular speaker at conferences like QCon and O’Reilly Fluent. She currently works on fintech infrastructure at a unicorn startup.