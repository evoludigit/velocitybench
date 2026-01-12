```markdown
---
title: "Mastering CDC Change Log Fields: The Backbone of Scalable Event-Driven Systems"
date: 2023-11-15
tags: ["database", "event-driven", "cdc", "database design", "api design"]
description: "Learn how CDC change log fields transform raw database changes into actionable events. Practical code examples and common pitfalls explained."
---

# **Mastering CDC Change Log Fields: The Backbone of Scalable Event-Driven Systems**

Modern applications rely on **Change Data Capture (CDC)** to react to database changes in real time. Whether you're building an e-commerce platform, financial system, or analytics pipeline, CDC lets you keep data synchronized across services and trigger downstream actions without polling. But raw CDC data—just a `SELECT * FROM changes`—isn’t enough. To make CDC useful, you need **standardized change log fields**.

In this guide, we’ll explore why these fields are essential, how they solve real-world problems, and how to implement them effectively. By the end, you’ll know how to design CDC logs that are **machine-readable, debuggable, and interoperable**—no matter which database you’re using.

---

## **The Problem: Raw CDC Data is Useless Without Structure**

Imagine your database emits this CDC log for every update to a `users` table:

```json
{
  "db": "app_db",
  "table": "users",
  "old": { "id": 1, "name": "Alice", "email": "alice@example.com" },
  "new": { "id": 1, "name": "Alice Smith", "email": "alice.smith@example.com" }
}
```

At first glance, this seems fine. But what happens when:

1. **Your team uses multiple databases** (PostgreSQL, MySQL, MongoDB) and the CDC logs format differs?
2. **You need to debug a failed transaction** in production, but the log lacks timestamps?
3. **A downstream service expects a consistent schema**, but the CDC payload is dynamic?
4. **You’re integrating with an external API**, and it requires metadata like `operation_type` and `transaction_id`?

Without standardized fields, you’re forced to:
- Write custom parsers for every database.
- Add hacks (e.g., `"operation": "update"` inferred from `old` vs. `new`).
- Losing critical metadata (e.g., when the change happened, who caused it).

This leads to **fragile, hard-to-maintain systems**.

---

## **The Solution: Standardized CDC Change Log Fields**

The **CDC Change Log Fields** pattern defines a **universal schema** for CDC logs that:
✅ Works across databases (PostgreSQL, MongoDB, etc.).
✅ Includes metadata for debugging (timestamps, IDs).
✅ Enables downstream services to process changes reliably.
✅ Is backward-compatible with raw CDC output.

Here’s the **minimal required structure** for a CDC log entry:

```json
{
  "metadata": {
    "source_database": "app_db",
    "source_table": "users",
    "source_schema": "public",
    "event_id": "e1234567-890a-1234-5678-90abcdef1234",
    "operation_type": "update", // insert, update, delete, etc.
    "transaction_id": "tx_abc123",
    "event_timestamp": "2023-11-15T12:34:56Z",
    "captured_timestamp": "2023-11-15T12:34:57.123Z",
    "user_ident": "user_456" // Who triggered the change (if applicable)
  },
  "payload": {
    "old": { "id": 1, "name": "Alice", "email": "alice@example.com" },
    "new": { "id": 1, "name": "Alice Smith", "email": "alice.smith@example.com" }
  }
}
```

### **Core Fields Explained**
| Field               | Purpose                                                                 | Example                          |
|---------------------|-------------------------------------------------------------------------|----------------------------------|
| `source_database`   | Which DB was changed?                                                  | `"app_db"`                       |
| `source_table`      | Which table was affected?                                              | `"users"`                        |
| `operation_type`    | `insert`, `update`, `delete`, or `truncate`?                          | `"update"`                       |
| `event_id`          | Unique ID for this event (UUID recommended).                           | `"e1234567-890a-..."`            |
| `event_timestamp`   | When the change was **applied** to the database.                       | `"2023-11-15T12:34:56Z"`        |
| `captured_timestamp`| When the CDC system **recorded** the change (useful for lag analysis).  | `"2023-11-15T12:34:57.123Z"`    |
| `user_ident`        | Who caused the change (if tracked).                                    | `"user_456"`                     |

*(Optional but useful fields: `schema_version`, `source_schema`, `transaction_id`.)*

---

## **Implementation Guide: Adding CDC Fields to Your System**

### **1. Choose a CDC Tool**
Most databases provide CDC natively or via extensions. Here’s how to add our fields:

| Database       | Method                                                                 |
|----------------|------------------------------------------------------------------------|
| **PostgreSQL** | Use [`wal2json`](https://github.com/eulerto/wal2json) + custom filter. |
| **MySQL**      | Use [`Debezium`](https://debezium.io/) with a custom connector.        |
| **MongoDB**    | Use [`MongoDB Change Streams`](https://www.mongodb.com/docs/manual/changeStreams/) + middleware. |
| **Custom App** | Hook into ORM (e.g., SQLAlchemy) or raw SQL triggers.                |

---

### **2. Example: Adding Fields with Debezium (MySQL)**
Debezium is a popular CDC tool for MySQL. To inject our fields, we’ll:

1. **Configure Debezium to include metadata** in the payload.
2. **Post-process events** with a custom connector.

#### **Step 1: Basic Debezium Setup (Confluent Schema Registry)**
```yaml
# connector.properties
name=mysql-source
connector.class=io.debezium.connector.mysql.MySqlConnector
database.hostname=localhost
database.port=3306
database.user=debezium
database.password=dbz
database.server.id=184054
database.server.name=app_db
table.include.list=users
```

#### **Step 2: Add Custom Fields with a Kafka Connect Sink**
We’ll use a **Kafka Connect transformer** (e.g., [`kafka-connect-transforms`](https://github.com/confluentinc/kafka-connect-transforms)) to inject metadata:

```yaml
# transforms.config
transforms=route
route.type=route
route.topic.regex=.*\.users\..*
route.key.pattern=$(string-concat,source_database,.-,source_table,.-,operation_type)
transforms=add_metadata
add_metadata.type=add-field
add_metadata.fields=event_id:uuid,operation_type:route.topic.regex,event_timestamp:source_timestamp
```

Now, Debezium emits logs like:
```json
{
  "source_database": "app_db",
  "source_table": "users",
  "operation_type": "update",
  "event_id": "e1234567-890a-...",
  "event_timestamp": "2023-11-15T12:34:56Z",
  "payload": { "old": { ... }, "new": { ... } }
}
```

---

### **3. Example: Adding Fields in PostgreSQL with `wal2json`**
If you’re using PostgreSQL, [`wal2json`](https://github.com/eulerto/wal2json) is a simple way to capture row changes. We’ll **post-process its output** to add metadata.

#### **Step 1: Install and Configure `wal2json`**
```sh
# Install (Ubuntu/Debian)
sudo apt-get install wal2json
```

#### **Step 2: Write a Custom Filter (Python Example)**
```python
import json
import uuid
from datetime import datetime

def enhance_cdc_log(raw_log):
    """Adds standardized fields to wal2json logs."""
    log = raw_log.copy()

    # Generate an event ID
    log["metadata"] = {
        "event_id": str(uuid.uuid4()),
        "operation_type": log.get("type", "unknown"),
        "event_timestamp": datetime.now().isoformat() + "Z",
        "source_database": log["dbname"],
        "source_table": log["table"],
        "captured_timestamp": datetime.now().isoformat() + "Z"
    }

    # Clean up old keys (wal2json uses "data.nold" vs. our "old")
    if "data" in log:
        log["payload"] = {
            "old": log["data"].get("nold", {}),
            "new": log["data"].get("nnew", {}),
        }
        del log["data"]

    return log

# Example usage:
raw = {
    "dbname": "app_db",
    "table": "users",
    "type": "update",
    "data": {
        "nold": {"id": 1, "name": "Alice"},
        "nnew": {"id": 1, "name": "Alice Smith"}
    }
}

enhanced = enhance_cdc_log(raw)
print(json.dumps(enhanced, indent=2))
```
**Output:**
```json
{
  "metadata": {
    "event_id": "e1234567-890a-1234-5678-90abcdef1234",
    "operation_type": "update",
    "event_timestamp": "2023-11-15T12:34:56Z",
    "source_database": "app_db",
    "source_table": "users",
    "captured_timestamp": "2023-11-15T12:34:56.123Z"
  },
  "payload": {
    "old": {"id": 1, "name": "Alice"},
    "new": {"id": 1, "name": "Alice Smith"}
  }
}
```

---

### **4. Example: Adding Fields in a Custom Application (SQLAlchemy)**
If you’re using an ORM like SQLAlchemy, you can **intercept database operations** and log changes manually.

```python
from sqlalchemy import event
import uuid
from datetime import datetime

# Example for a 'users' table
@event.listens_for(User, "after_update")
def log_user_update(target, context, **kw):
    log_entry = {
        "metadata": {
            "event_id": str(uuid.uuid4()),
            "operation_type": "update",
            "event_timestamp": datetime.now().isoformat() + "Z",
            "source_database": "app_db",
            "source_table": "users",
            "user_ident": current_user.id  # Assuming current_user is logged in
        },
        "payload": {
            "old": {k: getattr(target, k) for k in target.__table__.columns.keys()},
            "new": {k: getattr(target, k) for k in target.__table__.columns.keys()}
        }
    }
    # Send to a message broker (e.g., RabbitMQ, Kafka) or store in an ELT system
    print(f"Logging CDC event: {json.dumps(log_entry)}")
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Ignoring `event_timestamp` vs. `captured_timestamp`**
- **Problem**: Confusing when the change happened (`event_timestamp`) with when it was recorded (`captured_timestamp`) leads to miscalculations in lag analysis.
- **Fix**: Always log both. Use `event_timestamp` for downstream processing and `captured_timestamp` for monitoring.

### **❌ Mistake 2: Not Handling `delete` Operations Properly**
- **Problem**: Some CDC tools omit the `old` payload for `delete` operations, making it hard to reconstruct full history.
- **Fix**: Ensure `delete` events include the `old` payload (e.g., from database tombstones).

```json
{
  "metadata": { ... },
  "payload": {
    "old": { "id": 1, "name": "Alice" },
    "new": null
  }
}
```

### **❌ Mistake 3: Overloading `payload` with Metafields**
- **Problem**: Storing `user_ident` or `transaction_id` inside `payload` breaks consistency if the table schema changes.
- **Fix**: Keep metadata in `metadata` and payload as raw table data.

### **❌ Mistake 4: Not Versioning Your CDC Schema**
- **Problem**: If you change the CDC log format, old consumers break.
- **Fix**: Use a `schema_version` field and document backward/forward compatibility.

```json
{
  "metadata": {
    "schema_version": "1.0",
    "event_id": "...",
    ...
  }
}
```

---

## **Key Takeaways**
✔ **Standardized CDC logs** make your system more maintainable and interoperable.
✔ **Core fields** (`event_id`, `operation_type`, `event_timestamp`) are non-negotiable.
✔ **Database-specific tools** (Debezium, `wal2json`) can be extended with middleware.
✔ **Avoid reinventing the wheel**: Use existing CDC tools but add your fields in a layer above.
✔ **Document your schema**: Future you (and your team) will thank you.

---

## **Conclusion: Build Scalable Systems with CDC Change Log Fields**

Raw CDC data is a **data swamp**—without structure, it’s useless. By adopting the **CDC Change Log Fields** pattern, you:
- **Reduce debugging complexity** (no more guessing what `old`/`new` mean).
- **Enable seamless integrations** (APIs, microservices, analytics).
- **Future-proof your system** (easy to add new metadata fields).

Start small: Add just `event_id`, `operation_type`, and `event_timestamp` to your first CDC pipeline. Then expand. Your future self (and your team) will thank you.

### **Next Steps**
1. **Pick a database** and try adding fields using the examples above.
2. **Experiment with tools**: Debezium for MySQL, `wal2json` for PostgreSQL, or custom ORM hooks.
3. **Share your schema**: Publish your CDC log format so collaborators know what to expect.

Happy coding!
```

---
**Want to dive deeper?** Check out:
- [Debezium Connector Docs](https://debezium.io/documentation/reference/stable/connectors/mysql.html)
- [PostgreSQL wal2json](https://github.com/eulerto/wal2json)
- [MongoDB Change Streams](https://www.mongodb.com/docs/manual/changeStreams/)