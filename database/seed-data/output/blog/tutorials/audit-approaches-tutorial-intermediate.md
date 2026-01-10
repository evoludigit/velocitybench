```markdown
---
title: "Audit Approaches Pattern: Tracking Changes Like a Pro"
date: 2023-11-15
author: "Alex Carter"
tags: ["database design", "backend patterns", "audit logging", "SQL", "API design"]
category: "Design Patterns"
---

# Audit Approaches Pattern: Tracking Changes Like a Pro

![Audit Logging](https://via.placeholder.com/1000x400/2c3e50/ffffff?text=Tracking+Data+Changes+with+Audit+Approaches)

As backend engineers, we often find ourselves grappling with questions like: *How do I ensure data integrity?* *How can I track who made changes and when?* *How do I build a compliance-friendly system?* The **Audit Approaches Pattern** is a well-tested solution to these challenges. This pattern addresses the need for maintaining a complete history of data changes—who made them, when, and why—while keeping performance and scalability in mind.

In this guide, we’ll explore the core ideas behind audit approaches, dive into practical implementation strategies, and discuss tradeoffs. Whether you're working on a financial system, a healthcare application, or an internal tool, understanding audit approaches will make your systems more robust, traceable, and compliant. Let's get started!

---

## The Problem: Why Audits Matter

Modern applications handle sensitive data, require compliance, and need accountability. Without proper auditing, you risk:
- **Data corruption**: Typos, unintended changes, or bugs can go unnoticed.
- **Regulatory violations**: Industries like finance (PCI-DSS, SOX), healthcare (HIPAA), and legal (GDPR) mandate audit trails.
- **Debugging headaches**: Without a history of changes, troubleshooting becomes a guessing game.
- **Security breaches**: If someone alters critical data, you won’t know it until it’s too late.

### Real-World Scenarios
Consider these examples:
1. **E-commerce Inventory System**: An admin mistakenly deleted a popular product. Without an audit trail, you can't recover it or prove the mistake.
2. **Healthcare Patient Records**: A doctor updates a prescription but adds an incorrect dose. An audit log ensures corrective action can be taken immediately.
3. **Banking Transactions**: A fraudulent transfer slips through. Without logs, the fraudster might go unnoticed for hours.

Without a structured way to track changes, these scenarios spiral into costly mistakes or legal trouble.

---

## The Solution: Audit Approaches Pattern

The **Audit Approaches Pattern** provides systematic ways to capture and persist data change history. There are three primary strategies, each with tradeoffs:
1. **Audit Tables**: Simple sidecar tables storing changes.
2. **Database Triggers**: Automatically log changes via stored procedures.
3. **Application-Level Logging**: Centralized logging via your API layer.

We’ll explore each approach with code examples, pros, and cons.

---

## Components of the Audit Approaches Pattern

### 1. Audit Tables
An **audit table** is a dedicated table that stores a history of changes to your core data. It typically includes:
- A unique ID for the record.
- The primary key of the modified record.
- Timestamps for when the change occurred.
- The user who made the change (if applicable).
- The old and new values (or a JSON diff).

#### Example: Audit Table for Users
```sql
-- Core users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit table for users
CREATE TABLE user_audit (
    audit_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB, -- Stores old values (empty on INSERT)
    new_data JSONB, -- Stores new values (empty on DELETE)
    changed_by VARCHAR(50), -- Username or system if automated
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### Example: Inserting an Audit Record
```python
# Pseudocode for logging a user update
def update_user(user_id, updates):
    old_data = fetch_user(user_id)  # Get current state
    new_data = apply_updates(user_id, updates)  # Apply updates
    update_core_table(user_id, new_data)  # Save to primary table

    # Log the change
    insert_into_audit(
        user_id=user_id,
        action="UPDATE",
        old_data=serialize(old_data),
        new_data=serialize(new_data),
        changed_by=request.user.username
    )
```

**Pros:**
✅ Simple to implement.
✅ Full control over what’s logged.
✅ Scalable with proper indexing.

**Cons:**
❌ Requires manual logic to keep in sync.
❌ Can bloat database size if not optimized.

---

### 2. Database Triggers
Triggers automate audit logging by executing stored procedures on `INSERT`, `UPDATE`, or `DELETE`. PostgreSQL, MySQL, and SQL Server all support triggers.

#### Example: Trigger for User Updates
```sql
-- Function to compare old and new values
CREATE OR REPLACE FUNCTION log_user_update()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO user_audit (
            user_id, action, old_data, new_data, changed_at, changed_by
        ) VALUES (
            NEW.user_id, 'UPDATE',
            to_jsonb(OLD), to_jsonb(NEW),
            CURRENT_TIMESTAMP,
            current_setting('app.current_user')
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER trg_user_update_audit
AFTER UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION log_user_update();
```

**Pros:**
✅ Fully automatic; no app code needed.
✅ Ensures audits are never missed.

**Cons:**
❌ Harder to debug (logic in SQL).
❌ Can impact performance for high-volume tables.

---

### 3. Application-Level Logging
Instead of database-side tracking, you log changes via your API layer. This works well for distributed systems or when you need richer metadata.

#### Example: REST API with Audit Logging
```python
# FastAPI example
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    updates: UserUpdate,
    db_session: Session = Depends(get_db)
):
    user = db_session.query(User).get(user_id)
    if not user:
        return {"error": "User not found"}

    # Store old data
    old_data = user.model_dump()

    # Apply updates
    for key, value in updates.dict().items():
        setattr(user, key, value)

    # Save to DB and log
    db_session.commit()

    # Log the change
    audit_record = AuditRecord(
        user_id=user_id,
        action="UPDATE",
        old_data=old_data,
        new_data=user.model_dump(),
        changed_by=request.state.user.username
    )
    db_session.add(audit_record)
    db_session.commit()

    return {"message": "User updated successfully"}
```

**Pros:**
✅ Flexible; can log additional context (e.g., IP, request headers).
✅ Works well for microservices.

**Cons:**
❌ Requires manual implementation.
❌ Risk of missed logs if not handled everywhere.

---

## Implementation Guide

### Step 1: Choose Your Approach
- **For simplicity**: Use **audit tables** with app-side logic.
- **For automation**: Use **database triggers**.
- **For distributed systems**: Use **application-level logging**.

### Step 2: Design Your Audit Table
- Include a `user_id` (or equivalent) for referential integrity.
- Use `JSONB` (PostgreSQL) or `TEXT` for flexible old/new values.
- Add indexes on frequently queried columns (e.g., `user_id`, `changed_at`).

### Step 3: Implement Logging
- **For audit tables**: Write helper functions to log changes.
- **For triggers**: Define functions and triggers in your schema.
- **For API-level**: Add logging middleware or wrap DB operations.

### Step 4: Test Thoroughly
- Verify all `INSERT`, `UPDATE`, and `DELETE` operations log changes.
- Test edge cases (e.g., concurrent updates).
- Check performance impact under load.

### Step 5: Optimize
- **Partition audit tables** by date for large datasets.
- **Use async logging** if performance is critical.
- **Consider read replicas** for audit queries.

---

## Common Mistakes to Avoid

1. **Logging Everything**: Avoid logging sensitive fields (passwords, PII) unless required by law.
2. **Ignoring Performance**: Audit tables can bloat; index them properly.
3. **Over-Reliance on Triggers**: Triggers can be hard to debug; test thoroughly.
4. **Inconsistent Logging**: Ensure all layers (DB, app, APIs) log changes uniformly.
5. **No Retention Policy**: Audit data can grow indefinitely; set TTL or archiving rules.

---

## Key Takeaways
- **Audit approaches** are essential for data integrity, compliance, and debugging.
- **Three main strategies**: Audit tables (flexible), triggers (automatic), and app-level logging (distributed).
- **Tradeoffs exist**: Simplicity vs. automation, performance vs. flexibility.
- **Design carefully**: Optimize for your workload (e.g., partitioning, indexing).
- **Test rigorously**: Ensure no logs are missed or corrupted.
- **Comply with regulations**: Audit logs may be legally required in your industry.

---

## Conclusion
Auditing isn’t just a nice-to-have—it’s critical for modern applications. Whether you’re building a financial system, a healthcare app, or an internal tool, implementing the **Audit Approaches Pattern** will make your system more robust, traceable, and compliant.

Start small (e.g., audit tables), then refine as your needs grow. Remember: there’s no one-size-fits-all solution. Experiment, measure, and optimize based on your specific requirements.

Happy coding—and happy auditing!
```

---
**Further Reading:**
- [PostgreSQL Triggers Documentation](https://www.postgresql.org/docs/current/plpgsql-trigger.html)
- [GDPR Compliance Guide](https://gdpr-info.eu/)
- ["Designing Data-Intensive Applications" (Book)](https://dataintensive.net/) (Chapter on Reliability)