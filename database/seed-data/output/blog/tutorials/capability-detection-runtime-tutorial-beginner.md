```markdown
# **Capability Detection Runtime: Building Databases That Adapt to Your Data**

Building a backend system that works seamlessly across different databases is no simple task. Many developers hit walls when their feature-rich application meets a database that doesn’t support the exact syntax, version, or extension they assumed. Hardcoding database capabilities leads to brittle systems that break under real-world conditions—or worse: silently behave incorrectly.

At **FraiseQL**, we’ve built a pattern we call **Capability Detection Runtime**—a way to dynamically probe database features during compilation (or at runtime) to adjust behavior gracefully. Instead of failing or forcing downgrades, your application can detect what works and what doesn’t, then adapt accordingly. This pattern is especially powerful for ORMs, query builders, or any system that generates dynamic SQL.

In this tutorial, we’ll explore the problems caused by static database assumptions, how **Capability Detection Runtime** solves them, and practical ways to implement this pattern in your own systems. By the end, you’ll have a toolbox for building resilient database interactions that scale across environments.

---

## **The Problem: Hardcoded Assumptions Break**

Most database-aware applications make assumptions about their environment upfront. For example:

- *"This database supports `JSONB`; I’ll use it for complex queries."*
- *"PostgreSQL 12+ has `WITH RECURSIVE`; I’ll use it for hierarchical data."*
- *"MySQL 8.x supports window functions; I’ll use them for analytics."*

But in reality, your users might run on:
- An older PostgreSQL version that lacks `WITH RECURSIVE`.
- A MySQL 5.x server with limited CTE support.
- A SQLite database with even more restrictions.

When these assumptions fail, two common (and bad) outcomes occur:

1. **Hard Failures**: Your app crashes with cryptic errors when a feature isn’t available.
2. **Silent Misdirections**: Your app *seems* to work but produces incorrect results or inefficient queries.

Worse still, you might force a "downgrade" path that makes your application slower or less expressive. **Why should your database dictate your app’s capabilities?**

---

## **The Solution: Runtime Capability Detection**

Instead of hardcoding database features, **Capability Detection Runtime** probes the database at runtime (or during compilation) to determine what’s actually available. The system then adjusts behavior dynamically:

- **Feature Probing**: Query the database version, supported extensions, and capabilities.
- **Fallbacks**: If a feature isn’t available, switch to a slower or more basic implementation.
- **Graceful Degradation**: The app continues working without crashing.

This pattern is already used in ORMs like **Django ORM** (for SQLite vs. PostgreSQL) and **Spring Data JPA** (for dialect-specific optimizations). However, we’ll refine it for **dynamic query builders** like FraiseQL.

---

## **Key Components of Capability Detection Runtime**

Here’s how the pattern works under the hood:

| Component          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Probes**         | Lightweight queries that detect a feature’s presence (e.g., `SELECT version()`). |
| **Feature Flags**  | A runtime registry that maps detected features to supported modes.          |
| **Query Builder**  | A component that uses the feature registry to rewrite or avoid unsupported SQL. |
| **Fallbacks**      | Alternative query structures for unsupported features (e.g., `JOIN` instead of `WITH RECURSIVE`). |

---

## **Practical Example: Detecting Database Features**

Let’s build a simple capability detector in **Python** to illustrate the pattern. We’ll create a `DatabaseCapabilityDetector` that checks for common PostgreSQL features.

### **Step 1: Define a Prober Class**

```python
from typing import Dict, Optional, List

class DatabaseCapabilityDetector:
    def __init__(self, connection_string: str):
        self.connection = create_connection(connection_string)  # Assume this exists
        self.capabilities: Dict[str, bool] = {}

    def probe(self) -> None:
        """Detect all supported features."""
        self._probe_version()
        self._probe_jsonb()
        self._probe_ctes()

    def _probe_version(self) -> None:
        """Check database version."""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            self.capabilities["version"] = bool(db_version)
            # Example: PostgreSQL >= 12 has WITH RECURSIVE
            self.capabilities["with_recursive"] = self._is_postgres_ge_12()

    def _probe_jsonb(self) -> None:
        """Check for JSONB support."""
        try:
            self.connection.execute("SELECT 'test'::jsonb")
            self.capabilities["jsonb"] = True
        except Exception:
            self.capabilities["jsonb"] = False

    def _probe_ctes(self) -> None:
        """Check for Common Table Expression support."""
        try:
            self.connection.execute("WITH RECURSIVE test AS (...) SELECT * FROM test")
            self.capabilities["ctes"] = True
        except Exception:
            self.capabilities["ctes"] = False

    def _is_postgres_ge_12(self) -> bool:
        """Check if PostgreSQL version >= 12."""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version_str = cursor.fetchone()[0]
            return version_str.split()[2].startswith("12")
```

### **Step 2: Use the Detector in a Query Builder**

Now, let’s modify a query builder to use these capabilities:

```python
from typing import Optional

class DynamicQueryBuilder:
    def __init__(self, detector: DatabaseCapabilityDetector):
        self.detector = detector
        self.detector.probe()  # Run probes on initialization

    def build_hierarchical_query(self, table: str) -> str:
        """Build a query that uses WITH RECURSIVE if available, falls back to JOIN."""
        if self.detector.capabilities["with_recursive"]:
            return f"""
                WITH RECURSIVE hierarchy AS (
                    -- Your recursive CTE logic
                )
                SELECT * FROM hierarchy
            """
        else:
            return f"""
                SELECT * FROM {table} t1
                -- Join-based fallback
            """
```

### **Step 3: Detect JSONB and Adjust Queries**

```python
    def build_json_query(self, table: str) -> str:
        """Use JSONB if available, fall back to string parsing."""
        if self.detector.capabilities["jsonb"]:
            return f"""
                SELECT data->>'field' FROM {table}
            """
        else:
            return f"""
                SELECT cast(data AS TEXT)::JSON->>'field' FROM {table}
            """
```

---

## **Implementation Guide: When and How to Apply This Pattern**

### **When to Use Capability Detection Runtime**
✅ **Dynamic Query Builders**: Like FraiseQL or SQLAlchemy, where SQL is generated based on runtime input.
✅ **Multi-Database Apps**: Serving users with different database backends (e.g., PostgreSQL, MySQL, SQLite).
✅ **Feature-Rich ORMs**: Where advanced SQL features (e.g., window functions) should degrade gracefully.
✅ **Legacy Systems**: When migrating off an old database but maintaining compatibility.

### **When *Not* to Use It**
❌ **Static SQL**: If your queries are hardcoded and don’t need adaptation.
❌ **Performance-Critical Paths**: Probing adds overhead; avoid if this isn’t a bottleneck.
❌ **Trivial Apps**: Overkill for a simple CRUD app with no complex features.

---

## **Common Mistakes to Avoid**

1. **Probing Too Aggressively**
   - **Problem**: Probing every feature on every query is slow.
   - **Fix**: Cache results and only re-probe when the database changes (e.g., versions).

2. **Silent Fallbacks**
   - **Problem**: If `WITH RECURSIVE` fails, silently use `JOIN` but don’t log the downgrade.
   - **Fix**: Log or warn when falling back (e.g., `DEBUG: Falling back from CTE to JOIN`).

3. **Over-Reliance on Probes**
   - **Problem**: Assuming all features can be probed safely (e.g., some databases don’t support `EXPLAIN ANALYZE`).
   - **Fix**: Have a fallback strategy for unprobed features.

4. **Vendor Lock-in in Fallbacks**
   - **Problem**: A "downgrade" path only works for one database.
   - **Fix**: Design fallbacks to be database-agnostic where possible.

---

## **Key Takeaways**

- **Capability Detection Runtime** lets your app adapt to database limitations without breaking.
- **Probes** are lightweight checks to detect features at runtime.
- **Fallbacks** ensure graceful degradation when features are missing.
- **Tradeoffs**: Probing adds complexity but saves crashes and poor performance on mismatched environments.
- **Best for**: Dynamic query builders, multi-database apps, and feature-rich ORMs.

---

## **Conclusion**

Hardcoding database features into your application is like assuming all users have Wi-Fi—it doesn’t always hold true. **Capability Detection Runtime** gives you the flexibility to write expressive SQL that adapts to the database at hand.

By probing for features and falling back intelligently, you build systems that:
✔ Work correctly on every database.
✔ Maintain performance even with limitations.
✔ Scale without brittle assumptions.

In future posts, we’ll dive deeper into **optimizing probes**, **caching results**, and **testing capability detection** in CI/CD. For now, try implementing this pattern in your next project—your users (and database admins) will thank you.

---
**Try It Out**: [GitHub repo with FraiseQL-like capability detector](https://github.com/fraise-io/database-capability-prober)

---
**Questions?** Hit me up on [Twitter](https://twitter.com/yourhandle) or [Discord](https://discord.gg/fraise). Happy querying!
```