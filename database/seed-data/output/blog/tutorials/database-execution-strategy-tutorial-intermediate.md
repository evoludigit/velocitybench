```markdown
# **Database Execution Strategy: Writing Cross-DB Query Engines That Don’t Break**

Your application writes to PostgreSQL, but your staging environment runs on Amazon Aurora MySQL. Or worse—your Kubernetes cluster auto-scales between SQL Server and CockroachDB based on workload. You’ve seen firsthand how one tiny syntax difference can turn a 30-second query into a 30-hour nightmare.

This isn’t just a theoretical problem. When you write raw SQL directly in your code or rely on a single SQL generation library, you’re one database upgrade away from a production outage. That’s where the **Database Execution Strategy pattern** comes in.

This pattern separates query logic from database-specific execution details, letting you build a query engine that *adapts* to different databases—without rewriting your entire API layer. In this tutorial, we’ll break down how to implement it, cover common pitfalls, and show you practical examples in TypeScript (Node.js) with TypeORM, Prisma, and raw Knex.js.

---

## **The Problem: Why Your Query Engine Fails Across Databases**

Imagine your team is using PostgreSQL in production but testing against SQLite locally. When you deploy, this query:

```sql
SELECT
    u.id,
    ARRAY_AGG(DISTINCT r.role) AS roles
FROM users u
LEFT JOIN user_roles r ON u.id = r.user_id
WHERE u.status = 'active'
GROUP BY u.id
HAVING COUNT(DISTINCT r.role) > 1
```

…suddenly starts failing because SQLite doesn’t support `ARRAY_AGG`. Or maybe your analytics query uses `WITH` clauses, which MySQL 5.6 doesn’t implement. These aren’t edge cases—they’re real-world 101 problems that break your applications.

Worse yet, **query optimizers differ wildly** between databases. A well-indexed PostgreSQL query that runs in 50ms can become a 2-minute nightmare in Oracle. Even the same `JOIN` strategy (hash vs. merge) can behave unpredictably.

---

## **The Solution: Separate Strategy from Execution**

The **Database Execution Strategy** pattern solves this by:

1. **Decoupling query logic** from database-specific syntax.
2. **Using a strategy interface** to let different database engines implement the same logic.
3. **Leveraging query rewriting** to generate database-compatible SQL.

### **Core Idea: A Query Engine That Adapts**
Instead of writing raw SQL or relying on a single ORM, we define a query structure that can be "executed" by multiple database backends. Each backend implements its own strategy for translating that structure into SQL.

Here’s the high-level flow:

1. **Abstract Query Model**: Define the query in a neutral format (e.g., `SELECT {columns} FROM {table} WHERE {conditions}`).
2. **Strategy Interface**: Each database provider implements `QueryExecutor.execute(query)`.
3. **Rewriting Pipeline**: Convert the abstract query into database-specific syntax (e.g., `ARRAY_AGG` → `GROUP_CONCAT` in MySQL).

---

## **Components of the Database Execution Strategy**

### **1. The Abstract Query Model**
This is your "neutral" representation of a query. It should avoid database-specific features like:
- Window functions (`OVER()` in PostgreSQL, `LAG()` in SQL Server)
- Aggregation tricks (`ARRAY_AGG` in PostgreSQL, `JSON_ARRAYAGG` in MySQL)
- Dialect-specific syntax (`CROSS JOIN LATERAL` in PostgreSQL)

**Example (TypeORM-inspired):**
```typescript
interface AbstractQuery {
  select: string[];
  from: { table: string; alias?: string };
  joins: Array<{ table: string; alias: string; condition: string }>;
  where: { field: string; operator: '=' | '>' | '<'; value: string | number };
  groupBy: string[];
  having: string;
  orderBy?: { field: string; direction: 'ASC' | 'DESC' };
}
```

---

### **2. Database-Specific Strategies**
Each database provider implements a strategy that converts the abstract query into its dialect.

#### **Strategy Interface**
```typescript
interface QueryExecutor {
  execute(query: AbstractQuery): Promise<any[]>;
}
```

#### **PostgreSQL Strategy Implementation**
```typescript
class PostgreSQLQueryExecutor implements QueryExecutor {
  async execute(query: AbstractQuery): Promise<any[]> {
    const { select, from, joins, where, groupBy, having, orderBy } = query;

    const selectClause = select.join(', ');
    const whereClause = this.buildWhereClause(where);
    const groupByClause = groupBy.join(', ');
    const orderByClause = orderBy ? `ORDER BY ${orderBy.field} ${orderBy.direction}` : '';

    const queryString = `
      SELECT ${selectClause}
      FROM ${from.table} ${from.alias || ''}
      ${this.buildJoins(joins)}
      WHERE ${whereClause}
      ${groupByClause ? `GROUP BY ${groupByClause}` : ''}
      ${having ? `HAVING ${having}` : ''}
      ${orderByClause}
    `;

    return this.postgresClient.query(queryString);
  }

  private buildWhereClause(where: AbstractQuery['where']): string {
    return `${where.field} ${where.operator} '${where.value}'`;
  }

  private buildJoins(joins: AbstractQuery['joins']): string {
    return joins.map(j => `LEFT JOIN ${j.table} ${j.alias} ON ${j.condition}`).join('\n');
  }
}
```

#### **MySQL Strategy Implementation**
```typescript
class MySQLQueryExecutor implements QueryExecutor {
  async execute(query: AbstractQuery): Promise<any[]> {
    // Similar to PostgreSQL, but handles MySQL-specific syntax
    const { select, from, joins, where, groupBy, having } = query;

    // Replace PostgreSQL ARRAY_AGG with MySQL GROUP_CONCAT
    const mysqlSelectClause = select.map(col =>
      col.includes('ARRAY_AGG') ? col.replace('ARRAY_AGG', 'GROUP_CONCAT') : col
    ).join(', ');

    const queryString = `
      SELECT ${mysqlSelectClause}
      FROM ${from.table} ${from.alias || ''}
      ${this.buildJoins(joins)}
      WHERE ${this.buildWhereClause(where)}
      ${groupBy ? `GROUP BY ${groupBy.join(', ')}` : ''}
      ${having ? `HAVING ${this.rewriteHaving(having)}` : ''}
    `;

    return this.mysqlClient.query(queryString);
  }

  private rewriteHaving(having: string): string {
    // MySQL doesn’t support HAVING with non-aggregated columns
    return having.replace(/HAVING (.*)/, 'HAVING COUNT(*) > 0'); // Fallback
  }
}
```

---

### **3. Query Rewriting & Optimization**
This is where you handle database-specific quirks like:
- Rewriting `ARRAY_AGG` → `GROUP_CONCAT` in MySQL.
- Converting `WITH` clauses to temporary tables in older MySQL versions.
- Adding missing `GROUP BY` clauses in SQL Server.

#### **Example Rewriter**
```typescript
function rewriteForMySQL(query: AbstractQuery): AbstractQuery {
  const rewrittenQuery = { ...query };

  if (query.select.some(col => col.includes('ARRAY_AGG'))) {
    rewrittenQuery.select = rewrittenQuery.select.map(col =>
      col.replace('ARRAY_AGG', 'GROUP_CONCAT')
    );
  }

  return rewrittenQuery;
}
```

---

## **Implementation Guide: Step-by-Step**

### **1. Define Your Abstract Query Model**
Start with a simple model that covers common query patterns:
```typescript
type AbstractQuery = {
  type: 'select' | 'insert' | 'update' | 'delete';
  select?: string[];
  from: { table: string; alias?: string };
  joins?: Array<{ table: string; alias: string; condition: string }>;
  where?: { field: string; operator: string; value: any };
  // ... more fields
};
```

### **2. Create Database Strategies**
For each database, implement a `QueryExecutor`. Start with one provider (e.g., PostgreSQL) to validate your approach.

### **3. Use a Query Registry**
Map database names to strategies at runtime:
```typescript
const strategyRegistry: Record<string, QueryExecutorConstructor> = {
  postgres: PostgreSQLQueryExecutor,
  mysql: MySQLQueryExecutor,
  sqlite: SQLiteQueryExecutor,
};

function getExecutor(dialect: string): QueryExecutor {
  const Strategy = strategyRegistry[dialect];
  if (!Strategy) throw new Error(`Unsupported database: ${dialect}`);
  return new Strategy({ client: /* your DB client */ });
}
```

### **4. Implement Query Rewriting**
Add a pipeline to transform queries before execution:
```typescript
function executeQuery(dialect: string, query: AbstractQuery): Promise<any[]> {
  const executor = getExecutor(dialect);
  const rewrittenQuery = rewriteForMySQL(query); // or rewriteForPostgres()
  return executor.execute(rewrittenQuery);
}
```

### **5. Testing**
Write tests for:
- Query rewriting.
- Edge cases (e.g., `NULL` handling in MySQL).
- Performance (query length shouldn’t explode on any DB).

---

## **Common Mistakes to Avoid**

### **1. Over-Reliance on a Single ORM**
Using TypeORM or Prisma without understanding their query plans can mask database issues. **Always test across databases.**

### **2. Ignoring Query Performance**
A rewrite that works in PostgreSQL might cause a full-table scan in MySQL. Use `EXPLAIN` in all environments.

### **3. Not Handling Transactions Properly**
Some databases (e.g., SQLite) don’t support nested transactions. Your strategy must handle this gracefully.

### **4. Assuming `SELECT *` is Safe**
Never use `SELECT *` in your abstract model. Explicitly define columns to avoid surprises in different databases.

### **5. Skipping Error Handling**
Database-specific errors (e.g., `"Unknown column 'foo' in 'field list'"`) must be caught and handled in the strategy layer.

---

## **Key Takeaways**

✅ **Decouple query logic** from database syntax—write once, execute anywhere.
✅ **Use strategies** to adapt abstract queries to each database’s needs.
✅ **Rewrite aggressively**—handle `ARRAY_AGG` → `GROUP_CONCAT`, `OVER()` → temporary tables, etc.
✅ **Test across databases**—don’t assume SQLite behaves like PostgreSQL.
✅ **Optimize for all databases**—a fast query in one may be slow in another.
✅ **Handle errors gracefully**—wrap database errors in meaningful exceptions.

---

## **Conclusion: Build Once, Deploy Anywhere**

The Database Execution Strategy pattern may seem complex at first, but it’s the only reliable way to future-proof your application when you’re deployed across multiple databases.

Start small: implement it for a single query type (e.g., `SELECT` with `JOIN`s), then expand. Over time, you’ll build a query engine that’s **less fragile, more maintainable, and more scalable** than raw SQL or ORM-only approaches.

As you grow, consider:
- Adding a **query cache** to avoid rewriting the same query repeatedly.
- Implementing **query profiling** to compare performance across databases.
- Exploring **query plan sharing** (e.g., generate a plan in PostgreSQL, reuse it in MySQL).

The goal isn’t perfection—it’s **avoiding midnight production fires** when your SQL works in dev but crashes in staging. With this pattern, you’ll sleep better knowing your queries are ready for any database.

---
**Next Steps**
- Try implementing this for a simple CRUD operation in your app.
- Compare performance between a raw ORM query and your strategy-based approach.
- Share your learnings—what worked, what didn’t, and how you adapted.

Happy querying!
```