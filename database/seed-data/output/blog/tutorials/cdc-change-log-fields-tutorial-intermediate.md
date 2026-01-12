```markdown
# Mastering CDC Change Log Fields: A Practical Guide to Tracking Data Changes with Precision

![CDC Change Data Capture Diagram](https://miro.medium.com/max/1400/1*XqZkW2pX9wQ5qX5wQ5WQ5Q.png)
*Change Data Capture in action: tracking the lifecycle of your data*

In today’s data-driven world, understanding how your data evolves is as critical as the data itself. Without proper change tracking, you're flying blind when it comes to auditing, compliance, and real-time synchronization. This is where **Change Data Capture (CDC)** shines—but not all CDC implementations are created equal. While CDC tools efficiently capture *what* changed, the **CDC Change Log Fields pattern** ensures you capture *how* and *why* it changed, giving you complete context for every modification.

This pattern is your secret weapon for building robust audit trails, implementing proper soft deletes, and enabling granular rollback capabilities. Whether you're working with databases like PostgreSQL, or message brokers like Kafka, or just want to design your own change tracking system, standardizing your change log fields will save you headaches down the road. Let's dive in and explore why this pattern matters, and how to implement it effectively.

---

## The Problem: When "Something Changed" Isn't Enough

Imagine this scenario: you're building a banking application where account balances are updated in near real-time. Here's what happens without proper change log fields:

```sql
-- Account balance updated... but how?
UPDATE accounts SET balance = 1250.00 WHERE id = 123;
```

Your CDC pipeline captures this change, but now you're left with critical questions that no standard CDC implementation answers:
- **When** exactly did the change happen? (Down to millisecond precision)
- **Who** made the change? (System-generated vs. user action)
- **Why** was the change made? (Was it an automated adjustment, or a user transaction?)
- **How** should this change be rolled back if needed? (Is it safe to revert the entire balance?)
- **Was this change valid**? (Did the user have permission to make this change?)

Without these standardized fields, your systems become brittle:
1. **Audit failures**: Regulators can't reconstruct the history of a critical transaction.
2. **Debugging nightmares**: "Something broke—show me all changes from the last hour."
3. **Poor synchronization**: Replicating systems without proper change context lead to data drift.
4. **No atomicity guarantees**: You can't reliably roll back changes when needed.

The standard CDC implementations capture the *what* of changes, but leave the *how* and *why* as an afterthought. The **CDC Change Log Fields pattern** changes that by defining standard fields that capture all the context you need.

---

## The Solution: Standardized Change Log Fields

The CDC Change Log Fields pattern defines a standardized schema for tracking change events with these essential fields:

| Field | Description | Example Values | Required |
|-------|------------|----------------|----------|
| `event_id` | Unique identifier for this change event | `ca97a0d8-7a1e-4b3b-8e1d-4f63203e8a` | ✅ |
| `event_type` | Type of event (create/modify/delete) | `"account_update"`, `"soft_delete"` | ✅ |
| `entity_type` | The type of entity changed | `"account"`, `"user_profile"` | ✅ |
| `entity_id` | The ID of the changed entity | `123`, `"user_456"` | ✅ |
| `timestamp` | When the change occurred | `2024-03-15T14:30:45.123456Z` | ✅ |
| `user_id` | The user who initiated the change | `null` (system) or `"user_789"` | ⚠️ (often) |
| `action_by` | The system/user performing the change | `"api_user"`, `"admin_panel"` | ⚠️ (often) |
| `old_values` | Before state (for updates/deletes) | `{"balance": 1200.00, "status": "active"}` | ⚠️ (for updates/deletes) |
| `new_values` | After state (for creates/updates) | `{"balance": 1250.00, "status": "verified"}` | ⚠️ (for creates/updates) |
| `change_reason` | Purpose of the change (optional) | `"customer payment"`, `"manual adjustment"` | ❌ |
| `metadata` | Additional context | `{"txn_id": "txn_12345", "validation_rules": [...]}` | ❌ |
| `is_reversible` | Can this change be safely rolled back? | `true`, `false` (e.g., for immutable data) | ⚠️ |

This pattern transforms raw CDC data from:

```json
// Raw CDC event
{
  "table": "accounts",
  "column": "balance",
  "old_value": 1200.00,
  "new_value": 1250.00,
  "timestamp": "2024-03-15T14:30:45Z"
}
```

To:

```json
// Enhanced CDC event with our pattern
{
  "event_id": "ca97a0d8-7a1e-4b3b-8e1d-4f63203e8a",
  "event_type": "update",
  "entity_type": "account",
  "entity_id": "123",
  "timestamp": "2024-03-15T14:30:45.123456Z",
  "user_id": "user_456",
  "action_by": "web_interface",
  "old_values": {"balance": 1200.00, "status": "active"},
  "new_values": {"balance": 1250.00, "status": "verified"},
  "change_reason": "customer payment received",
  "metadata": {
    "txn_id": "txn_12345",
    "validation": {
      "success": true,
      "rules_applied": ["balance_validation"]
    }
  },
  "is_reversible": true
}
```

With these fields, you can now answer all the critical questions from earlier:

- **When?** `timestamp` and `event_id` provide precise timing
- **Who?** `user_id` and `action_by` track responsibility
- **Why?** `change_reason` and `metadata` explain context
- **How?** `is_reversible` flag tells you if rollback is safe
- **Was it valid?** Validation status in metadata ensures data integrity

---

## Components/Solutions for Implementing the Pattern

To implement this pattern, you'll need to integrate several components:

1. **CDC Source**: Your database or application that generates change events
2. **Change Tracking Mechanism**: Database triggers, application logging, or CDC tools
3. **Change Log Storage**: Database table or storage system for change events
4. **Event Enrichment**: Logic to populate metadata fields
5. **Consumers**: Services that use the change events

### Option A: Database-Level CDC with Triggers (Simple Setup)

```sql
-- Example for PostgreSQL
CREATE TABLE change_log (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type VARCHAR(20) NOT NULL,
  entity_type VARCHAR(30) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  user_id VARCHAR(100),
  action_by VARCHAR(50),
  old_values JSONB,
  new_values JSONB,
  change_reason VARCHAR(255),
  metadata JSONB,
  is_reversible BOOLEAN DEFAULT TRUE
);

-- Trigger for account updates
CREATE OR REPLACE FUNCTION log_account_change()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    INSERT INTO change_log (
      event_type, entity_type, entity_id,
      user_id, action_by,
      old_values, new_values,
      change_reason, metadata
    ) VALUES (
      'update', 'account', NEW.id,
      current_setting('app.current_user_id'),
      TG_OP,
      to_jsonb(OLD),
      to_jsonb(NEW),
      current_setting('app.change_reason'),
      to_jsonb(OLD)::jsonb - 'id'::jsonb &
      to_jsonb(NEW)::jsonb - 'id'::jsonb
    );

    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO change_log (
      event_type, entity_type, entity_id,
      user_id, action_by,
      old_values
    ) VALUES (
      'delete', 'account', OLD.id,
      current_setting('app.current_user_id'),
      TG_OP,
      to_jsonb(OLD)
    );

    RETURN OLD;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_account_change
AFTER INSERT OR UPDATE OR DELETE ON accounts
FOR EACH ROW EXECUTE FUNCTION log_account_change();
```

### Option B: Application-Level Logging (More Control)

```python
# Python example using SQLAlchemy
from sqlalchemy import event
from datetime import datetime
import uuid

def log_changes(mapper, connection, target):
    # Get current user from session
    current_user = current_user_id()  # Your auth system
    action_by = "api_endpoint"  # Default

    if mapper.is_class_target and hasattr(target, "original"):
        # Handle updates
        old_values = mapper.column_properties.values(target)
        new_values = mapper.mapped_attributes.values(target)

        metadata = {
            "validation": {"success": True},  # Would include actual validation
            "source": "api_endpoint"
        }

        change_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "update",
            "entity_type": mapper.class_.__name__.lower(),
            "entity_id": target.id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user,
            "action_by": action_by,
            "old_values": {k: str(v) for k, v in old_values},
            "new_values": {k: str(v) for k, v in new_values},
            "change_reason": getattr(target, "_last_change_reason", None),
            "metadata": metadata
        }

        insert_change_log(change_event)

    elif mapper.is_class_target and not hasattr(target, "_is_new"):
        # Handle deletes
        old_values = mapper.mapped_attributes.values(target)
        change_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "delete",
            "entity_type": mapper.class_.__name__.lower(),
            "entity_id": target.id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user,
            "action_by": action_by,
            "old_values": {k: str(v) for k, v in old_values}
        }

        insert_change_log(change_event)

# Attach to all models
@event.listens_for(Account, 'after_update')
def receive_after_update(mapper, connection, target):
    log_changes(mapper, connection, target)

@event.listens_for(Account, 'after_delete')
def receive_after_delete(mapper, connection, target):
    log_changes(mapper, connection, target)
```

### Option C: Using Debezium + Kafka (Enterprise Setups)

For Kafka-based CDC, you'd augment the raw event with metadata:

```json
// Debezium raw event
{
  "before": {"id": "123", "balance": 1200, "status": "active"},
  "after": {"id": "123", "balance": 1250, "status": "verified"},
  "op": "u",
  "ts_ms": 1710482245123
}

// Enriched event after our processor
{
  "event_id": "ca97a0d8-7a1e-4b3b-8e1d-4f63203e8a",
  "event_type": "update",
  "entity_type": "account",
  "entity_id": "123",
  "timestamp": "2024-03-15T14:30:45.123456Z",
  "user_id": "user_456",
  "action_by": "web_interface",
  "old_values": {"balance": 1200, "status": "active"},
  "new_values": {"balance": 1250, "status": "verified"},
  "is_reversible": true,
  "source": {
    "type": "kafka",
    "offset": 123456789,
    "partition": 0
  }
}
```

---

## Implementation Guide

### 1. Choose Your Data Model

Start with a basic change log table:

```sql
CREATE TABLE change_log (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type VARCHAR(20) NOT NULL DEFAULT 'unknown',
  entity_type VARCHAR(30) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  user_id VARCHAR(100),
  action_by VARCHAR(50),
  old_values JSONB,
  new_values JSONB,
  change_reason TEXT,
  metadata JSONB,
  is_reversible BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_change_log_entity ON change_log(entity_type, entity_id);
CREATE INDEX idx_change_log_timestamp ON change_log(timestamp);
CREATE INDEX idx_change_log_user ON change_log(user_id) WHERE user_id IS NOT NULL;
```

### 2. Implement Change Capture

**For Databases:**
- Use triggers (PostgreSQL, MySQL) or CDC tools (Debezium)
- Ensure all CRUD operations are captured

**For Applications:**
- Use ORM event listeners (SQLAlchemy, Hibernate)
- Implement middleware for direct database operations

### 3. Populate Required Fields

Critical fields that must be populated for every change:

```python
# Example field population logic
def create_change_event(entity_type, entity_id, old_values=None, new_values=None,
                       user_id=None, action_by="system"):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": determine_event_type(entity_type, old_values, new_values),
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action_by": action_by,
        "old_values": old_values,
        "new_values": new_values,
        "is_reversible": can_revert(entity_type, new_values)  # Custom logic
    }

def determine_event_type(entity_type, old_values, new_values):
    if not old_values and new_values:
        return "create"
    elif old_values and not new_values:
        return "delete"
    elif old_values and new_values:
        return "update"
    return "unknown"
```

### 4. Handle Special Cases

**Soft Deletes:**
```sql
-- Trigger for soft deletes
CREATE OR REPLACE FUNCTION log_soft_delete()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND OLD.status = 'active' AND NEW.status = 'deleted' THEN
    INSERT INTO change_log (
      event_type, entity_type, entity_id,
      user_id, action_by,
      old_values, new_values,
      change_reason
    ) VALUES (
      'soft_delete', TG_TABLE_NAME, NEW.id,
      current_setting('app.current_user_id'),
      'soft_delete_process',
      to_jsonb(OLD),
      to_jsonb(NEW),
      'User requested account deletion'
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Bulk Operations:**
Add a batch_id field to correlate multiple changes:

```sql
ALTER TABLE change_log ADD COLUMN batch_id UUID;
```

### 5. Version Your Change Log

```sql
ALTER TABLE change_log ADD COLUMN schema_version INT DEFAULT 1;
-- Then implement migrations
```

### 6. Set Up Consumers

Create views for common use cases:

```sql
-- Revertable changes
CREATE VIEW revertable_changes AS
SELECT * FROM change_log WHERE is_reversible = TRUE;

-- Timeline of an account
CREATE VIEW account_timeline AS
SELECT
  cl.*,
  ROW_NUMBER() OVER (PARTITION BY cl.entity_id ORDER BY cl.timestamp DESC) as rn
FROM change_log cl
WHERE cl.entity_type = 'account';
```

---

## Common Mistakes to Avoid

1. **Under-populating fields**: Forgetting to include critical fields like `user_id` or `timestamp`
   - *Solution*: Always validate change logs against a schema

2. **Overusing JSON**: While JSON is flexible, excessive nesting reduces query performance
   - *Solution*: For frequently queried fields, consider separate columns

3. **Ignoring performance**: Change logs can become large quickly
   - *Solution*: Partition your change log table
     ```sql
     CREATE TABLE change_log (
       -- fields
     ) PARTITION BY RANGE (timestamp);
     ```

4. **Not handling concurrent changes**: Race conditions can corrupt your logs
   - *Solution*: Use optimistic concurrency or transactional writes

5. **Treating all changes equally**: Some changes shouldn't be logged
   - *Solution*: Implement exclusion rules (e.g., ignore system-generated updates)

6. **Creating circular dependencies**: Your change log shouldn't reference itself
   - *Solution*: Be careful with metadata references

---

## Key Takeaways

- **Standardization is key**: Define exactly which fields your change logs need
- **Context matters**: Include user, action, and purpose information
- **Flexibility with structure**: Use JSON for optional metadata but keep core fields relational
- **Performance matters**: Index frequently queried fields and consider partitioning
- **Start simple**: Begin with the essential fields and expand as needed
- **Document your schema**: Your future self (and team)