```markdown
---
title: "Multi-Database Execution: Writing SQL Execution Engines That Work Everywhere"
author: "Alex Johnson"
date: "2023-11-15"
tags: ["database", "api design", "backend", "sql", "pattern"]
category: ["database"]
draft: false
---

# Multi-Database Execution: Writing SQL Execution Engines That Work Everywhere

**How to Write SQL Execution Code That Runs on PostgreSQL, MySQL, SQLite, and Oracle Without Breaking**

---

## Introduction

As a backend engineer, you’ve likely faced the challenge of writing SQL code that needs to run across multiple database systems. Whether you're building a serverless function, a microservice, or a legacy application migration tool, the reality is that your code won’t always run against PostgreSQL. Sometimes it’s MySQL, SQLite, Oracle, or even SQL Server.

Every database engine has its own quirks: syntax differences, missing features, and performance nuances. Writing SQL that works consistently across these platforms is harder than it sounds. But it’s not impossible—if you design your execution logic carefully.

This tutorial will walk you through the **Multi-Database Execution** pattern, a practical approach to writing execution engines that adapt to different databases without breaking. We’ll cover:

- Why this problem is harder than you might think.
- How to structure your code to handle differences.
- Practical examples in Python (using `SQLAlchemy` and raw SQL).
- Common pitfalls and how to avoid them.

---

## The Problem: Writing SQL That “Just Works” Everywhere

Let’s start with a concrete example. Imagine you’re building a data migration tool that needs to:

1. Insert records into a target database.
2. Handle transactions (rollbacks if something fails).
3. Use window functions for analytics.
4. Support JSON/JSONB data types.

Here’s a naive approach:

```python
def migrate_data(db_connection):
    # Step 1: Insert records
    db_connection.execute("""
        INSERT INTO users (id, name, email, metadata)
        VALUES
            (1, 'Alice', 'alice@example.com', '{"role": "admin"}'),
            (2, 'Bob', 'bob@example.com', '{"role": "user"}')
    """)

    # Step 2: Compute analytics using window functions
    analytics = db_connection.execute("""
        SELECT
            user_id,
            SUM(amount) OVER (PARTITION BY role) as total_spent_by_role
        FROM transactions
    """).fetchall()

    # Step 3: Commit
    db_connection.commit()
```

This code might work for PostgreSQL or MySQL, but what about SQLite? Let’s see:

- **SQLite** doesn’t support window functions. Your analytics query will fail.
- **Oracle** and **SQL Server** support window functions, but their syntax might differ slightly.
- **MySQL** supports JSON functions, but the syntax for JSONB (`'{"role": "admin"}'`) is only available in MySQL 5.7+.
- **SQLite** doesn’t have a `COMMIT` statement—transactions are implicit.

Even if you could fix these issues, the problem scales. Every new feature or query you add introduces more database-specific logic. You end up with a spaghetti mess of `if database == 'PostgreSQL'` checks or complex feature flags.

---

## The Solution: The Multi-Database Execution Pattern

The key idea behind the Multi-Database Execution pattern is to **decouple the logic of “what to do” from “how to do it.”** Instead of writing monolithic SQL code, you break your queries into smaller, reusable components and assemble them dynamically based on the target database.

Here’s how it works:

1. **Standardize your data model** (e.g., use an ORM or SQLAlchemy Core).
2. **Identify database-specific features** (window functions, JSON types, transactions).
3. **Write a mixin or adapter** that translates your high-level commands into database-specific SQL.
4. **Use a query builder** or **parameterized templates** to handle differences.

---

## Components of the Solution

### 1. Database-Agnostic Core Logic
Write your business logic using a library that abstracts database differences, like SQLAlchemy Core or Django ORM. This lets you focus on *what* you need to do, not *how*.

**Example (SQLAlchemy Core):**
```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON
from sqlalchemy.sql import select, insert

def create_users_table(metadata):
    users = Table(
        'users',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('email', String),
        Column('metadata', JSON)  # Works in PostgreSQL, MySQL, SQLite
    )
    return users
```

### 2. Database-Specific SQL Adaptors
For queries that require database-specific features, create small SQL fragments that adapt to the target database. Use a **query builder** like `sqlalchemy.engine.url.Url` or a simple dictionary lookup.

**Example: Window Functions**
```python
from sqlalchemy import func

def get_window_function(dialect):
    if dialect.name in ['postgresql', 'mysql', 'sqlite']:
        return func.sum(func.col('amount')).over(partition_by='role').label('total_spent_by_role')
    elif dialect.name in ['oracle', 'mssql']:
        return func.sum('amount').over(partition_by='role').label('total_spent_by_role')
    else:
        raise NotImplementedError(f"Window functions not supported for {dialect.name}")
```

### 3. Transaction Management
Transactions behave differently across databases. Use a higher-level API (like SQLAlchemy’s `session.begin()`) to handle this.

**Example:**
```python
from sqlalchemy.orm import Session

def migrate_data_in_transaction(session):
    try:
        # Insert records
        stmt = insert(users_table).values(
            [{"id": 1, "name": "Alice", "email": "alice@example.com", "metadata": {"role": "admin"}}],
            [{"id": 2, "name": "Bob", "email": "bob@example.com", "metadata": {"role": "user"}}]
        )
        session.execute(stmt)

        # Compute analytics
        query = select([
            users_table.c.role,
            get_window_function(session.bind.engine.dialect).label('total_spent_by_role')
        ])
        analytics = session.execute(query).fetchall()

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
```

### 4. Dynamic SQL Generation
For complex queries, use a template engine (like Jinja2) or a query builder (like SQLAlchemy’s `compiler`) to generate database-specific SQL.

**Example with Jinja2:**
```python
from jinja2 import Template

def generate_window_query(role_column, amount_column, dialect):
    if dialect in ['postgresql', 'mysql']:
        query_template = """
            SELECT
                user_id,
                SUM(amount) OVER (PARTITION BY role) as total_spent_by_role
            FROM {table}
        """
    elif dialect in ['oracle', 'mssql']:
        query_template = """
            SELECT
                user_id,
                SUM(amount) OVER (PARTITION BY {role_column}) as total_spent_by_role
            FROM {table}
        """
    else:
        raise NotImplementedError(f"Unsupported dialect: {dialect}")

    return Template(query_template).render(
        table=users_table.name,
        role_column=role_column,
        amount_column=amount_column
    )
```

---

## Implementation Guide: Step-by-Step

### Step 1: Choose Your Database Agnostic Tool
Use SQLAlchemy Core or Django ORM to write your data model. Avoid raw SQL unless necessary.

**Example:**
```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON

metadata = MetaData()

users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('email', String),
    Column('metadata', JSON)
)
```

### Step 2: Create a Dialect-aware Query Builder
Write a helper class that generates SQL based on the database dialect.

**Example:**
```python
from sqlalchemy import MetaData, Table, Column, Integer, String, JSON, select, insert
from sqlalchemy.engine import Engine
from typing import Dict, Any

class DialectAwareQueryBuilder:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()

    def insert_users(self, users_data: list[Dict[str, Any]]) -> insert:
        users_table = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('email', String),
            Column('metadata', JSON)
        )
        return insert(users_table).values(users_data)

    def get_window_function(self, role_column: str, amount_column: str) -> Any:
        dialect = self.engine.dialect.name
        if dialect in ['postgresql', 'mysql', 'sqlite']:
            return select([
                JSONColumn('metadata').key('role').label('role'),
                func.sum(amount_column).over(partition_by=role_column).label('total_spent_by_role')
            ])
        elif dialect in ['oracle', 'mssql']:
            return select([
                JSONColumn('metadata').key('role').label('role'),
                func.sum(amount_column).over(PARTITION BY role_column).label('total_spent_by_role')
            ])
        else:
            raise NotImplementedError(f"Unsupported dialect: {dialect}")
```

### Step 3: Integrate with ORM Sessions
Use SQLAlchemy’s `Session` to manage transactions and execute queries.

**Example:**
```python
from sqlalchemy.orm import Session

def migrate_data(db_url: str):
    engine = create_engine(db_url)
    query_builder = DialectAwareQueryBuilder(engine)
    session = Session(engine)

    try:
        # Insert users
        session.execute(
            query_builder.insert_users([
                {"id": 1, "name": "Alice", "email": "alice@example.com", "metadata": {"role": "admin"}},
                {"id": 2, "name": "Bob", "email": "bob@example.com", "metadata": {"role": "user"}}
            ])
        )

        # Fetch analytics
        analytics = session.execute(query_builder.get_window_function('role', 'amount')).fetchall()
        print(analytics)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

### Step 4: Test Across Databases
Write tests for different database backends using tools like `pytest` and `pytest-sqlalchemy`.

**Example Test:**
```python
import pytest
from sqlalchemy import create_engine

def test_migrate_data_postgres():
    engine = create_engine("postgresql://user:pass@localhost/test_db")
    migrate_data(engine.url)

def test_migrate_data_sqlite():
    engine = create_engine("sqlite:///:memory:")
    migrate_data(engine.url)
```

---

## Common Mistakes to Avoid

### 1. Ignoring Transaction Behavior
Not all databases handle transactions the same way:
- SQLite uses autocommit by default.
- PostgreSQL/MySQL require explicit `BEGIN`/`COMMIT`.
- Oracle uses `BEGIN TRANSACTION` and `COMMIT WORK`.

**Solution:** Use a high-level ORM or session-based transactions.

### 2. Assuming JSON Support Everywhere
- MySQL: JSON functions work in MySQL 5.7+.
- SQLite: Supports JSON, but no JSONB or advanced functions.
- PostgreSQL: Supports JSONB natively.

**Solution:** Use a lightweight JSON library (like Python’s `json`) for serialization.

### 3. Writing Monolithic SQL Queries
Avoid giant queries that are hard to adapt. Break them into smaller, reusable parts.

**Bad:**
```python
query = """
    -- 500 lines of SQL
"""
```

**Good:**
```python
def build_user_query():
    base = select([users_table.c.id, users_table.c.name])
    if window_functions_needed:
        base = base.with_window_function(...)
    return base
```

### 4. Not Testing Cross-Database Compatibility
Always test against different databases. A query that works in PostgreSQL might fail in SQLite.

**Solution:** Use tools like `pytest` with multiple database backends.

---

## Key Takeaways

- **Decouple logic from implementation.** Write business logic independently of database specifics.
- **Use a query builder or ORM.** SQLAlchemy, Django ORM, or even raw parameterized templates help.
- **Handle differences explicitly.** For unsupported features, either:
  - Find a workaround (e.g., use `JSON` instead of `JSONB`).
  - Raise an error gracefully.
- **Test against multiple databases.** Don’t assume your code works everywhere.
- **Leverage transactions carefully.** Use ORM sessions to avoid database-specific pitfalls.

---

## Conclusion

Writing SQL that works across multiple databases is challenging, but the Multi-Database Execution pattern makes it manageable. By standardizing your data model, using adaptable query builders, and testing rigorously, you can build robust applications that run on PostgreSQL, MySQL, SQLite, and beyond.

The key is to **design for adaptability**—not to write perfect SQL for every database, but to write code that can be adapted. This approach gives you flexibility when you need to support new databases or features.

Try the pattern in your next project, and let me know how it works for you!

---

**Further Reading:**
- [SQLAlchemy Core Documentation](https://docs.sqlalchemy.org/en/14/core/)
- [PostgreSQL vs. MySQL JSON Differences](https://www.postgresql.org/docs/current/datatype-json.html)
- [SQLite Transactions](https://www.sqlite.org/lang_transaction.html)
```

This blog post is designed to be practical, code-first, and honest about tradeoffs—exactly what your audience needs as intermediate backend engineers.