```markdown
---
title: "The Virtual-Machines Validation Pattern: Preserving Data Integrity Across Complex APIs"
author: "Alex Carter"
date: "2023-11-15"
tags: ["database design", "API patterns", "validation", "backend engineering"]
description: >
  Learn how to validate domain objects (like virtual machines) before database updates or API responses. This pattern ensures consistency across your microservices,
  reducing data corruption and improving API reliability.
---

# The Virtual-Machines Validation Pattern: Preserving Data Integrity Across Complex APIs

**Table of contents**
- [Introduction](#introduction)
- [The Problem: When Validation Goes Wrong](#the-problem)
- [The Solution: Virtual-Machines Validation Pattern](#the-solution)
- [Components of the Pattern](#components-of-the-pattern)
- [Implementation Guide](#implementation-guide)
- [Code Examples](#code-examples)
- [Common Mistakes to Avoid](#common-mistakes-to-avoid)
- [Key Takeaways](#key-takeaways)
- [Conclusion](#conclusion)

---

## Introduction

Backend systems often struggle with inconsistent data when business rules span multiple services or domain objects. For example, consider an API managing virtual machines (VMs). Users request VM creation, scaling, or snapshots—each operation involving multiple state changes. If a VM’s desired state (`running`) conflicts with its current state (`stopped`), the system might silently fail or corrupt data.

The **Virtual-Machines Validation Pattern** (also called *pre-validation* or *invariant validation*) ensures that VM state transitions adhere to business rules before touching the database. Think of it as a "safety net" around your data model—preventing invalid states from ever reaching persistence layers.

This pattern works beyond VMs (e.g., order processing, inventory management) and complements classic validation (e.g., field-level constraints). It’s especially valuable in distributed systems where eventual consistency is unavoidable.

---

## The Problem: When Validation Goes Wrong

Validation failures often manifest silently, causing:
- **Lost transactions**: A user requests a VM snapshot while it’s being resized. Without validation, concurrent operations may leave the VM in a broken state.
- **API gaps**: A frontend assumes a VM can be stopped directly, but the backend requires a grace period.
- **Debugging nightmares**: Logs show `state=invalid` after hours of operation, with no clear root cause (e.g., a misconfigured cron job).

### Common Flaws in Validation
1. **Late Validation**: Validating after database writes (e.g., in `after_commit` hooks) risks leaving intermediate invalid states.
   ```python
   # Bad: Validation happens too late
   def scale_vm(vm_id, new_size):
       vm = VM.objects.get(id=vm_id)
       vm.size = new_size
       vm.save()  # ❌ Invalid state written first
       validate_vm(vm)  # Too late; data may be corrupted
   ```
2. **Client-Side Only**: Frontends can’t guarantee validation (e.g., due to network errors).
3. **No Cascading Checks**: Validation often checks fields independently, ignoring dependencies (e.g., a VM can’t be archived if snapshots exist).

---

## The Solution: Virtual-Machines Validation Pattern

The pattern enforces these principles:
1. **Pre-write Validation**: Validate **before** any database changes happen.
2. **Invariant Rules**: Define *invariants*—rules that must always hold (e.g., `snapshots_exist → state != "archived"`).
3. **Idempotent Operations**: Reject invalid states outright (don’t retry with "best-effort" logic).

### How It Works
- **Layer 1 (API Layer)**: Validate inputs (e.g., `request.body.state` matches business rules).
- **Layer 2 (Domain Layer)**: Validate against current state in the database.
- **Layer 3 (Repository Layer)**: Ensure invariants are preserved (e.g., no `DELETE` if snapshots exist).

---

## Components of the Pattern

| Component               | Role                                                                 | Example                                                                 |
|-------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Invariant Definitions** | Rules that must always be true (e.g., "VMs can’t be deleted if snapshots exist"). | `class VMInvariants: <br>   @staticmethod <br>   def snapshots_block_deletion(vm): <br>       return vm.snapshots.count() > 0` |
| **Validator Service**     | Checks invariants before state transitions.                          | `class VMValidator: <br>   def validate_state_change(vm: VM, new_state: str):` |
| **Domain Event Batching** | Group validation failures (e.g., list all violated rules).           | Returns `[{ "rule": "snapshot_exists", "details": "..." }]`               |
| **Idempotency Hooks**     | Ensure retries don’t compound errors.                               | Reject with HTTP `400 Bad Request` if state is invalid.                  |

---

## Implementation Guide

### Step 1: Define Invariants
Start by documenting business rules. For VMs:
- A VM cannot be stopped if snapshots exist.
- Only running VMs can be scaled (no "warm" state).
- Archiving requires explicit confirmation.

```python
# invariants.py
class VMInvariants:
    @staticmethod
    def cannot_stop_with_snapshots(vm):
        return vm.state == "stopped" and vm.snapshots.exists()

    @staticmethod
    def scaling_requires_running(vm):
        return vm.state != "running" and vm.desired_size != vm.size
```

### Step 2: Create a Validator Class
Implement a validator that checks invariants before any operation.

```python
# vm_validator.py
from invariants import VMInvariants

class VMValidator:
    def __init__(self, vm_repo):
        self.vm_repo = vm_repo

    def validate_stop(self, vm_id):
        vm = self.vm_repo.get(vm_id)
        if VMInvariants.cannot_stop_with_snapshots(vm):
            raise ValidationError("Cannot stop VM with snapshots")

    def validate_scale(self, vm_id, new_size):
        vm = self.vm_repo.get(vm_id)
        if VMInvariants.scaling_requires_running(vm):
            raise ValidationError("VM must be running to scale")
```

### Step 3: Integrate with API Endpoints
Wrap database operations in validation.

```python
# api.py
from fastapi import APIRouter, HTTPException
from vm_validator import VMValidator
from vm_repo import VMRepository

router = APIRouter()
vm_repo = VMRepository()
vm_validator = VMValidator(vm_repo)

@router.post("/vms/{vm_id}/stop")
def stop_vm(vm_id: int):
    try:
        vm_validator.validate_stop(vm_id)
        vm_repo.stop(vm_id)  # Safe because validator passed
        return {"status": "stopped"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Step 4: Enforce Invariants in Database (Optional)
For critical invariants, use database constraints. Example with PostgreSQL:

```sql
-- Ensure VMs can't be archived if snapshots exist
ALTER TABLE vms
ADD CONSTRAINT no_archive_with_snapshots
CHECK (
    state != 'archived' OR
    NOT EXISTS (
        SELECT 1 FROM snapshots WHERE snapshots.vm_id = vms.id
    )
);
```

---

## Code Examples

### Example 1: Validating VM State Transitions
```python
# vm_repo.py (simplified)
class VMRepository:
    def stop(self, vm_id):
        vm = self.get(vm_id)
        vm.state = "stopped"
        self._save(vm)

    def archive(self, vm_id):
        vm = self.get(vm_id)
        vm.state = "archived"
        self._save(vm)
```

```python
# api.py (with validation)
from fastapi import FastAPI, HTTPException

app = FastAPI()
validator = VMValidator(VMRepository())

@app.post("/vms/{vm_id}/archive")
def archive_vm(vm_id: int):
    try:
        validator.validate_no_snapshots(vm_id)  # New check
        validator.validate_state_change(vm_id, "archived")
        repo.archive(vm_id)
        return {"status": "archived"}
    except ValidationError as e:
        raise HTTPException(400, detail=str(e))
```

### Example 2: Cascading Validation Failures
Return all violated rules at once:

```python
class VMValidator:
    def validate_state(self, vm_id, new_state):
        vm = self.repo.get(vm_id)
        violations = []

        if VMInvariants.cannot_stop_with_snapshots(vm):
            violations.append("VM cannot be stopped if snapshots exist")
        if vm.state == "archived" and new_state == "running":
            violations.append("Archived VMs cannot be started")

        if violations:
            raise ValidationError("\n".join(violations))
```

---

## Common Mistakes to Avoid

1. **Assuming Input Validation Suffices**
   - *Mistake*: Only validate `state=stopped` but ignore `snapshots` count.
   - *Fix*: Always re-validate against the database.

2. **Tight Coupling to Database Queries**
   - *Mistake*: Validator fetches all VMs to check invariants globally.
   - *Fix*: Pass only the relevant VM to the validator.

3. **Retry Logic on 400 Errors**
   - *Mistake*: Retrying a `400 Bad Request` (e.g., scaling a stopped VM).
   - *Fix*: Treat validation failures as permanent client-side issues.

4. **Ignoring Time Decays**
   - *Mistake*: Assuming `snapshots_exist` is static (e.g., after deletion).
   - *Fix*: Use event sourcing or timestamps to track stale invariants.

---

## Key Takeaways

- **Pre-write validation** is non-negotiable for complex state machines.
- **Define invariants** as business rules, not just technical constraints.
- **Fail fast**—reject invalid operations with clear error messages.
- **Combine layers**: Use API validation + domain validation + database constraints.
- **Test invariants**: Write unit tests for every invariant (e.g., mock invalid states).
- **Document thresholds**: Clearly state why a validation fails (e.g., "snapshots must be deleted first").

---

## Conclusion

The Virtual-Machines Validation Pattern ensures your backend never accepts invalid states, reducing bugs and debugging time. While it adds complexity, the cost of silent failures (e.g., data corruption) is far higher.

For APIs with complex state transitions (VMs, orders, IoT devices), this pattern is invaluable. Start with invariants for critical rules, then expand to edge cases. Pair it with tools like:
- **Postman/Newman** for API contract testing.
- **Property-based testing** (e.g., Hypothesis) to catch invariant violations.

Pro Tip: Use **event sourcing** for auditability. Log every state change, so you can replay and debug failures.

By enforcing invariants at every layer, you build a system where data integrity isn’t an afterthought—it’s the foundation.

---
```