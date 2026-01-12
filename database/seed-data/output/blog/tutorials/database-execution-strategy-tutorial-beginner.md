```markdown
---
title: "Database Execution Strategy Pattern: Writing SQL That Works Everywhere"
date: 2024-02-15
author: "Jane Doe"
description: "Learn how to handle database differences with the Execution Strategy pattern, ensuring your queries work across PostgreSQL, MySQL, SQL Server, and more."
tags: ["database", "patterns", "SQL", "backend", "database design"]
---

# Database Execution Strategy Pattern: Writing SQL That Works Everywhere

As a backend developer, you’ve probably spent nights staring at your terminal, wondering why your beautifully crafted SQL works in one database but throws errors in another. Maybe PostgreSQL loves your `CURRENT_TIMESTAMP`, but MySQL complains with "Unknown column 'CURRENT_TIMESTAMP' in 'field list'." Or perhaps your ORM-generated query looks perfect, but SQL Server refuses to cooperate with your `LIMIT` clause.

Sound familiar? This inconsistency is a common struggle when writing database-agnostic applications. The **Database Execution Strategy Pattern** helps solve this problem by separating query logic from database-specific implementation details. Instead of writing raw SQL directly, we design our application to generate execution plans that can be adapted to different databases.

In this tutorial, we’ll explore how to structure your code to handle SQL differences gracefully, ensuring your application works consistently across PostgreSQL, MySQL, SQL Server, and other databases. You’ll learn how to abstract SQL generation, leverage vendor-specific features, and avoid unnecessary duplication. By the end, you’ll have a practical approach to writing resilient SQL that adapts to the database you’re targeting.

---

## The Problem: Why Your SQL Doesn’t Work Everywhere

Imagine you’re building a blog platform. Your team uses TypeORM for ORM and PostgreSQL in development, but your production environment runs on MySQL. You write this query to fetch the most recent posts:

```typescript
// In your TypeORM service
export async function getRecentPosts(limit: number) {
  return await this.repository
    .createQueryBuilder("post")
    .where("published = :isPublished", { isPublished: true })
    .orderBy("createdAt", "DESC")
    .limit(limit)
    .getMany();
}
```

This works fine in development. But when you deploy to MySQL production, you get this error:
```
ERROR: LIMIT requires an ORDER BY clause (SQL: SELECT ... ORDER BY "createdAt" DESC LIMIT $1)
```

Even though PostgreSQL allows `LIMIT` without `ORDER BY`, MySQL requires it. This is just one example of how SQL dialects differ. Here are some other pain points:

1. **Syntax variations**: `CURRENT_TIMESTAMP` vs `NOW()`, `UNIX_TIMESTAMP()` vs `EXTRACT(EPOCH FROM ...)`.
2. **Function names**: `COALESCE()` vs `IFNULL()`, `LEFT JOIN` vs `LEFT OUTER JOIN`.
3. **Pagination**: `LIMIT OFFSET` vs `ROW_NUMBER()`-based pagination.
4. **String functions**: `CONCAT()` vs `||` (PostgreSQL), `LENGTH()` vs `CHAR_LENGTH()`.
5. **Aggregate functions**: `GROUP BY ROLLUP` or `CUBE` (PostgreSQL) vs `PIVOT` (SQL Server).

These inconsistencies force you to either:
- Write database-specific SQL (hardcoding dialect-dependent code),
- Use an ORM that abstracts these differences (but may not support all features),
- Or rewrite your queries every time you switch databases.

This leads to messy, unmaintainable code and makes your application less portable. The **Database Execution Strategy Pattern** is a way to avoid these pitfalls by separating the *what* (query logic) from the *how* (database implementation).

---

## The Solution: Database Execution Strategy Pattern

The **Database Execution Strategy Pattern** is a design pattern that abstracts the differences between SQL dialects by separating execution logic into two parts:

1. **The Query Plan**: A database-agnostic representation of what you want to achieve (e.g., "fetch the most recent posts").
2. **The Execution Engine**: A translator that converts the query plan into database-specific SQL.

This approach allows you to:
- Write query logic once,
- Adapt execution to the target database,
- Easily switch databases without rewriting queries,
- Leverage database-specific features when needed.

The pattern has three core components:
1. **Query Builder/Query Plan**: Defines the logic of the query in a way that’s independent of the database.
2. **Execution Strategy**: Maps the query plan to database-specific SQL.
3. **Dialect Adapter**: Handles database-specific syntax and features.

---

## Components/Solutions

Let’s break down how this pattern works with code examples.

### 1. Query Plan: The High-Level "What"
The query plan is a structured representation of your query logic, abstracted from database specifics. This is often implemented as a class or interface that defines the query’s components (e.g., `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `ORDER BY`).

Here’s a simple example in TypeScript:

```typescript
interface QueryPlan {
  select: string[];
  from: string;
  where?: { column: string; operator: string; value: any }[];
  orderBy?: { column: string; direction: "ASC" | "DESC" };
  limit?: number;
  offset?: number;
}

// Example query plan: fetch 5 published posts, ordered by createdAt (descending)
const recentPostsPlan: QueryPlan = {
  select: ["id", "title", "createdAt"],
  from: "posts",
  where: [{ column: "published", operator: "=", value: true }],
  orderBy: { column: "createdAt", direction: "DESC" },
  limit: 5,
};
```

This plan is **completely database-agnostic**. It doesn’t use `LIMIT`, `ORDER BY`, or any specific SQL keywords—just a structured representation of the query’s intent.

---

### 2. Execution Strategy: Translating to SQL
The execution strategy is responsible for converting the query plan into database-specific SQL. This is where you handle dialect differences.

Let’s create a simple `ExecutionStrategy` class that can translate the query plan into SQL for different databases. For simplicity, we’ll implement this as a base class with dialect-specific extensions.

#### Base Execution Strategy:
```typescript
abstract class BaseExecutionStrategy {
  abstract translateToSql(plan: QueryPlan, dialect: string): string;
}

class SimpleExecutionStrategy extends BaseExecutionStrategy {
  translateToSql(plan: QueryPlan, dialect: string): string {
    let sql = `SELECT ${plan.select.join(", ")} FROM ${plan.from}`;
    let params: string[] = [];

    // Handle WHERE clause (database-agnostic logic)
    if (plan.where) {
      sql += " WHERE ";
      plan.where.forEach((clause, index) => {
        const paramName = `$p${index + 1}`;
        params.push(paramName);
        sql += `${clause.column} ${clause.operator} ${paramName}`;
        if (index < plan.where.length - 1) sql += " AND ";
      });
    }

    // Handle ORDER BY (dialect-specific logic)
    if (plan.orderBy) {
      sql += ` ORDER BY ${plan.orderBy.column} ${plan.orderBy.direction}`;
    }

    // Handle LIMIT/OFFSET (dialect-specific logic)
    if (plan.limit || plan.offset) {
      const limitSql = this.getLimitSql(plan.limit, plan.offset, dialect);
      sql += ` ${limitSql}`;
    }

    return [sql, ...params].join(" ");
  }

  private getLimitSql(limit?: number, offset?: number, dialect: string): string {
    if (dialect === "mysql") {
      // MySQL requires ORDER BY before LIMIT and uses OFFSET
      if (!offset) throw new Error("MySQL requires ORDER BY before LIMIT");
      return `LIMIT ${limit} OFFSET ${offset}`;
    } else if (dialect === "postgresql" || dialect === "sqlite") {
      // PostgreSQL and SQLite support LIMIT with or without OFFSET
      if (offset) {
        return `LIMIT ${limit} OFFSET ${offset}`;
      } else {
        return `LIMIT ${limit}`;
      }
    } else if (dialect === "sqlserver") {
      // SQL Server uses TOP for LIMIT and OFFSET via ROW_NUMBER()
      // (More complex; simplified here for clarity)
      return `OFFSET ${offset} ROWS FETCH NEXT ${limit} ROWS ONLY`;
    } else {
      throw new Error(`Unsupported dialect: ${dialect}`);
    }
  }
}
```

#### Dialect-Specific Strategy:
Now, let’s refine the strategy to handle more complex differences, like functions or joins.

```typescript
// Dialect-specific strategy (e.g., PostgreSQL)
class PostgreSQLExecutionStrategy extends SimpleExecutionStrategy {
  translateToSql(plan: QueryPlan): string {
    let sql = super.translateToSql(plan, "postgresql");
    return sql;
  }

  // Override methods for PostgreSQL-specific features
  private getCurrentTimestampSql(): string {
    return "CURRENT_TIMESTAMP";
  }
}

// Dialect-specific strategy (e.g., MySQL)
class MySQLExecutionStrategy extends SimpleExecutionStrategy {
  translateToSql(plan: QueryPlan): string {
    let sql = super.translateToSql(plan, "mysql");
    // Add MySQL-specific optimizations or syntax
    return sql;
  }

  private getCurrentTimestampSql(): string {
    return "NOW()";
  }
}
```

---

### 3. Key Components in Practice
To make this work end-to-end, you’d typically implement it like this:

#### Query Builder (Creates the Query Plan)
```typescript
class QueryBuilder {
  private plan: Partial<QueryPlan> = {
    select: ["*"],
    from: "",
  };

  select(columns: string[]): this {
    this.plan.select = columns;
    return this;
  }

  from(table: string): this {
    this.plan.from = table;
    return this;
  }

  where(column: string, operator: string, value: any): this {
    if (!this.plan.where) this.plan.where = [];
    this.plan.where.push({ column, operator, value });
    return this;
  }

  orderBy(column: string, direction: "ASC" | "DESC"): this {
    this.plan.orderBy = { column, direction };
    return this;
  }

  limit(limit: number): this {
    this.plan.limit = limit;
    return this;
  }

  offset(offset: number): this {
    this.plan.offset = offset;
    return this;
  }

  getPlan(): QueryPlan {
    return this.plan as QueryPlan;
  }

  // Execute with a specific strategy
  exec(strategy: BaseExecutionStrategy): Promise<any[]> {
    const plan = this.getPlan();
    const sql = strategy.translateToSql(plan);
    // Execute SQL against the database (e.g., using a connection pool)
    return db.query(sql); // Assume db.query() handles parameter binding
  }
}
```

#### Usage Example:
```typescript
// Build a query plan
const query = new QueryBuilder()
  .select(["id", "title", "createdAt"])
  .from("posts")
  .where("published", "=", true)
  .orderBy("createdAt", "DESC")
  .limit(5);

// Execute with PostgreSQL strategy
const postgreSQLStrategy = new PostgreSQLExecutionStrategy();
const posts = await query.exec(postgreSQLStrategy);
// Returns: "SELECT id, title, createdAt FROM posts WHERE published = $p1 ORDER BY createdAt DESC LIMIT 5"

// Execute with MySQL strategy
const mysqlStrategy = new MySQLExecutionStrategy();
const mysqlPosts = await query.exec(mysqlStrategy);
// Returns: "SELECT id, title, createdAt FROM posts WHERE published = $p1 ORDER BY createdAt DESC LIMIT 5 OFFSET 0"
// (Note: MySQL requires ORDER BY even if LIMIT is used)
```

---

## Implementation Guide

### Step 1: Define Your Query Plan
Start by defining a structured representation of your queries. This is often an interface or a class with properties like `select`, `from`, `where`, etc. This acts as your "contract" for queries.

```typescript
interface QueryPlan {
  select: string[];
  from: string;
  joins?: { table: string; condition: string }[];
  where?: { column: string; operator: string; value: any }[];
  groupBy?: string[];
  having?: { column: string; operator: string; value: any }[];
  orderBy?: { column: string; direction: "ASC" | "DESC" };
  limit?: number;
  offset?: number;
  // Add more as needed (e.g., unions, subqueries)
}
```

### Step 2: Create a Base Execution Strategy
Implement a base class that handles common logic (e.g., SELECT, WHERE, ORDER BY). Extend this class for dialect-specific strategies.

```typescript
abstract class BaseExecutionStrategy {
  abstract translateToSql(plan: QueryPlan): string;

  protected buildSelectClause(plan: QueryPlan): string {
    return plan.select.map(col => this.formatColumn(col)).join(", ");
  }

  protected buildFromClause(plan: QueryPlan): string {
    return plan.from;
  }

  protected buildWhereClause(plan: QueryPlan): string {
    if (!plan.where?.length) return "";
    return plan.where
      .map((clause, index) => `${clause.column} ${clause.operator} $p${index + 1}`)
      .join(" AND ");
  }

  // ... other helper methods for JOINs, GROUP BY, etc.
}

abstract class DialectStrategy extends BaseExecutionStrategy {
  // Dialect-specific implementations
}
```

### Step 3: Implement Dialect Strategies
For each database you support, create a strategy class that extends the base class and overrides methods for dialect-specific features.

**Example: PostgreSQL Strategy**
```typescript
class PostgreSQLStrategy extends DialectStrategy {
  translateToSql(plan: QueryPlan): string {
    const select = this.buildSelectClause(plan);
    const from = this.buildFromClause(plan);
    const where = this.buildWhereClause(plan);
    const orderBy = plan.orderBy
      ? ` ORDER BY ${plan.orderBy.column} ${plan.orderBy.direction}`
      : "";
    const limit = plan.limit
      ? ` LIMIT ${plan.limit}${plan.offset ? ` OFFSET ${plan.offset}` : ""}`
      : "";
    const joins = plan.joins
      ? plan.joins.map(j => `INNER JOIN ${j.table} ON ${j.condition}`).join("\n")
      : "";

    return `SELECT ${select} FROM ${from}\n${joins}\n${where}${orderBy}${limit}`;
  }

  protected formatColumn(column: string): string {
    return `"${column}"`; // PostgreSQL quoting
  }
}
```

**Example: MySQL Strategy**
```typescript
class MySQLStrategy extends DialectStrategy {
  translateToSql(plan: QueryPlan): string {
    if (!plan.orderBy && plan.limit) {
      throw new Error("MySQL requires ORDER BY before LIMIT");
    }
    // ... rest of the implementation
  }

  protected formatColumn(column: string): string {
    return column; // No quoting in MySQL for simple cases
  }
}
```

### Step 4: Integrate with Your Application
Use a factory or dependency injection to resolve the correct strategy based on the database dialect.

```typescript
class DatabaseFactory {
  static getStrategy(dialect: string): BaseExecutionStrategy {
    switch (dialect.toLowerCase()) {
      case "postgresql": return new PostgreSQLStrategy();
      case "mysql": return new MySQLStrategy();
      case "sqlserver": return new SQLServerStrategy();
      default: throw new Error(`Unsupported dialect: ${dialect}`);
    }
  }
}
```

### Step 5: Use the Pattern in Your Code
Now, your queries can be written once and executed across databases:

```typescript
async function getRecentPosts(limit: number) {
  const query = new QueryBuilder()
    .select(["id", "title", "createdAt"])
    .from("posts")
    .where("published", "=", true)
    .orderBy("createdAt", "DESC")
    .limit(limit);

  const strategy = DatabaseFactory.getStrategy("postgresql");
  const results = await query.exec(strategy);

  return results;
}
```

---

## Common Mistakes to Avoid

1. **Over-engineering for simplicity**:
   - Don’t use the Execution Strategy Pattern for trivial queries or when switching databases rarely. For small projects, raw SQL or an ORM might suffice.

2. **Ignoring performance implications**:
   - Abstracting SQL can sometimes lead to less efficient queries. For example, `LIMIT OFFSET` is inefficient in PostgreSQL. Always test performance with your chosen strategy.

3. **Hardcoding dialect logic in the plan**:
   - Ensure your query plan remains database-agnostic. Never include dialect-specific syntax (e.g., `NOW()` vs `CURRENT_TIMESTAMP`) in the plan itself.

4. **Not handling parameter binding**:
   - Always use parameter binding (`$p1`, `@param`) to avoid SQL injection and handle type conversion properly.

5. **Overcomplicating joins**:
   - Joins can quickly become complex to abstract. Start with simple queries and refactor as needed.

6. **Missing error handling**:
   - Dialect strategies should validate the query plan before translation. For example, MySQL requires `ORDER BY` before `LIMIT`, so throw an error if that’s missing.

7. **Not testing across dialects**:
   - Always test your query plans with multiple dialects. Some edge cases (e.g., advanced functions) may not translate cleanly.

---

## Key Takeaways

Here’s what you should remember from this tutorial:

- **Problem**: SQL dialects differ, leading to inconsistent queries across databases.
- **Solution**: Separate query logic (plan) from execution (strategy) to handle dialect differences gracefully.
- **Components**:
  - **Query Plan**: A structured, database-agnostic representation of the query.
  - **Execution Strategy**: Translates the plan into database-specific SQL.
  - **Dialect Adapter**: Handles syntax and feature differences (e.g., `LIMIT` vs `TOP`).
- **Benefits**:
  - Write queries once, execute them anywhere.
  - Easily switch databases without rewriting SQL.
  - Leverage database-specific features where beneficial.
- **Tradeoffs**:
  - Initial setup requires more code.
  - Overhead for simple queries may not be worth it.
  - Testing across dialects is essential.
- **When to use**:
  - Multi-database applications.
  - Complex queries with dialect-specific syntax.
  - Need for query portability.

---

## Conclusion

The Database Execution Strategy Pattern is a powerful way to handle SQL dialect differences in your backend applications. By separating query logic from execution, you can write queries once and execute them consistently across PostgreSQL