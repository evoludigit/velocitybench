```markdown
---
title: "Mutation Execution via Stored Procedures: Putting Logic Where It Belongs"
date: 2023-11-15
tags: ["database", "api design", "graphql", "patterns", "best practices"]
description: "Delegating GraphQL mutations to stored procedures: tradeoffs, practical examples, and implementation guide. Advanced database and API design patterns."
---

# Mutation Execution via Stored Procedures: Putting Logic Where It Belongs

If you've ever found yourself rewriting business logic in both your application code and the database layer, **you're not alone**. Many systems suffer from duplication between application-level mutations and database-level logic. This is where **"Mutation Execution via Stored Procedures"** becomes an appealing pattern. It shifts mutation logic from the application layer into the database, leveraging SQL's transactional guarantees, performance optimizations, and explicit schema enforcement.

This pattern is particularly useful when your business logic requires:
- Strong transactional consistency (e.g., transferring funds between accounts)
- Direct access to database-specific features (e.g., PostgreSQL arrays, JSONB operations)
- Reduced coupling between application code and data model changes

However, like all architectural decisions, this pattern comes with tradeoffs—including tighter coupling, harder debugging, and platform lock-in. In this guide, we'll explore **when and how** to use this pattern effectively, with real-world code examples and pitfalls to avoid.

---

## The Problem: Duplicated Business Logic

Imagine a frontend mutation to update a user's subscription plan:

```javascript
// Application mutation (GraphQL)
const updateSubscription = async (input: { userId: string, planId: string }) => {
  const user = await db.queryUser(userId);
  if (!user.subscription || user.subscription.isActive) {
    throw new Error("Invalid subscription state");
  }

  const plan = await db.queryPlan(planId);
  if (!plan.isEligible(user.subscription.level)) {
    throw new Error("Plan upgrade not allowed");
  }

  const result = await db.updateUserSubscription(userId, planId);
  return { success: true, subscription: result };
};
```

But your database also has constraints and business rules enforced via triggers:

```sql
-- Database trigger (PostgreSQL)
CREATE OR REPLACE FUNCTION validate_subscription_update()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.subscription_level > OLD.subscription_level AND
     OLD.subscription_level = 'premium' THEN
    RAISE EXCEPTION 'Premium users cannot upgrade further';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_subscription_update
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION validate_subscription_update();
```

**Problem:**
- **Duplicate logic**: The same validation happens in both the application and the database.
- **Inconsistency risk**: If the application logic changes but the database trigger doesn’t (or vice versa), edge cases remain unhandled.
- **Performance overhead**: Round-trips between application and database for every mutation.

This is a classic example of **"thin application fat database"** vs. **"thick application thin database"** anti-patterns. The solution? **Shift the mutation logic to the database layer where it belongs.**

---

## The Solution: Stored Procedures for Mutations

The **"Mutation Execution via Stored Procedures"** pattern centralizes mutation logic in the database, treating stored procedures as the primary execution path for GraphQL mutations. Here’s how it works:

1. **GraphQL resolver invokes a stored procedure** instead of writing raw SQL.
2. **Stored procedures handle all business logic**, including validations, transactions, and DDL.
3. **Application code acts as a thin wrapper**, mapping inputs/outputs to the GraphQL layer.

### Benefits:
✅ **Single source of truth**: Business rules exist only in the database.
✅ **Atomicity**: Transactions are managed at the database level.
✅ **Performance**: Reduces round-trips and leverages database optimizations.
✅ **Security**: Encapsulates sensitive logic in the database.

### Tradeoffs:
⚠️ **Debugging complexity**: Stored procedures are harder to debug than application code.
⚠️ **Vendor lock-in**: Platform-specific syntax (e.g., PostgreSQL vs. MySQL).
⚠️ **Version control**: Managing procedure changes requires careful coordination.

---

## Components/Solutions

A complete implementation requires three layers:

1. **GraphQL Layer**: Defines mutations and delegates to stored procedures.
2. **Database Layer**: Contains stored procedures and transaction logic.
3. **Application Wrapper**: Maps GraphQL inputs to procedure calls (and vice versa).

### GraphQL Example (TypeScript with Apollo)
```graphql
# Schema definition
type Mutation {
  updateSubscription(userId: ID!, planId: ID!): SubscriptionUpdateResult!
}

# Resolver
const resolvers = {
  Mutation: {
    updateSubscription: async (_, { userId, planId }, { dataSource }) => {
      // 1. Convert GraphQL input to procedure parameters
      const params = {
        user_id: userId,
        plan_id: planId,
        timestamp: new Date().toISOString()
      };

      // 2. Execute the stored procedure
      const result = await dataSource.query(
        'CALL update_user_subscription($1, $2, $3)',
        params
      );

      // 3. Parse stored procedure output into GraphQL types
      return {
        success: result.rows[0].success === 'true',
        subscription: mapToSubscription(result.rows[0])
      };
    }
  }
};
```

### Stored Procedure Example (PostgreSQL)
```sql
-- update_user_subscription.plpgsql
CREATE OR REPLACE FUNCTION update_user_subscription(
  user_id INT,
  plan_id INT,
  requested_at TIMESTAMP
) RETURNS TABLE (
  success BOOLEAN,
  subscription_plan TEXT,
  error_message TEXT
) AS $$
DECLARE
  old_level TEXT;
  new_level TEXT;
  user_record RECORD;
  plan_record RECORD;
BEGIN
  -- 1. Fetch user and plan data
  SELECT subscription_level INTO old_level
  FROM users
  WHERE id = user_id
  FOR UPDATE;

  SELECT level INTO new_level
  FROM plans
  WHERE id = plan_id;

  -- 2. Validate business rules
  IF old_level > new_level THEN
    RETURN QUERY
    SELECT false, NULL, 'Cannot downgrade subscription' AS error_message;
  END IF;

  IF old_level = 'premium' AND new_level > old_level THEN
    RAISE EXCEPTION 'Premium users cannot upgrade';
  END IF;

  -- 3. Update subscription
  UPDATE users
  SET
    subscription_plan = plan_id,
    last_updated = requested_at
  WHERE id = user_id
  RETURNING subscription_plan;

  -- 4. Log and return success
  RETURN QUERY
  SELECT
    true AS success,
    (SELECT level FROM plans WHERE id = plan_id) AS subscription_plan,
    NULL AS error_message;
END;
$$ LANGUAGE plpgsql;
```

---

## Implementation Guide

### Step 1: Design Your Stored Procedures
- **Single Responsibility**: Each procedure should handle one mutation.
- **Input/Output Types**: Define clear parameters and return types.
- **Transactions**: Use explicit `BEGIN/COMMIT` or `RETURN QUERY` for atomicity.

### Step 2: Map GraphQL Types to Procedures
Use a type mapping layer (e.g., a `dataSource` class) to:
- Convert GraphQL input to procedure parameters.
- Parse stored procedure output into GraphQL types.

```typescript
// Example mapping layer
interface SubscriptionUpdateResult {
  success: boolean;
  subscription: Subscription;
}

function mapToSubscription(procedureResult: any): Subscription {
  return {
    id: procedureResult.plan_id,
    level: procedureResult.subscription_plan,
    price: procedureResult.price,
  };
}
```

### Step 3: Handle Errors Gracefully
Stored procedures can throw exceptions. Catch them in the application layer and return meaningful GraphQL errors.

```graphql
type Mutation {
  updateSubscription(userId: ID!, planId: ID!): SubscriptionUpdateResult!
}

# Resolver with error handling
const resolvers = {
  Mutation: {
    updateSubscription: async (_, args, context) => {
      try {
        const { userId, planId } = args;
        const result = await context.dataSource.query(
          'CALL update_user_subscription($1, $2)',
          [userId, planId]
        );
        return { success: true, subscription: mapResult(result) };
      } catch (error) {
        const { message } = error;
        return { success: false, errorMessage: message };
      }
    }
  }
};
```

### Step 4: Test Thoroughly
- **Unit tests**: Test procedures with `psql` or a testing framework like `pg-mocha`.
- **Integration tests**: Verify GraphQL mutations trigger procedures correctly.
- **Edge cases**: Test invalid inputs, permission issues, and concurrent updates.

---

## Common Mistakes to Avoid

### ❌ **Overusing Stored Procedures**
- If your mutation is simple (e.g., `CREATE USER`), a raw SQL query may suffice.
- Avoid "fat procedures" that do everything—modularize logic.

### ❌ **Ignoring Error Handling**
- Stored procedures can fail silently or throw generic errors. Map them to GraphQL errors explicitly.

### ❌ **Locking the Database**
- Use `FOR UPDATE` sparingly—overlocking causes contention. Design procedures to minimize locks.

### ❌ **Not Versioning Procedures**
- Procedures are part of your API contract. Use database migrations (e.g., Flyway, Liquibase) to manage changes.

### ❌ **Assuming SQL is Faster**
- Stored procedures can be slower if they do too much work. Offload complex computations to the application layer.

---

## Key Takeaways

- **Use this pattern when**:
  - Your mutations require complex transactional logic.
  - Business rules are tightly coupled to your data model.
  - You need to leverage database-specific features (e.g., JSONB, arrays).

- **Avoid when**:
  - Your mutations are simple CRUD operations.
  - Your team lacks familiarity with SQL procedures.
  - You need loose coupling between application and database.

- **Best practices**:
  - Keep procedures small and focused.
  - Map GraphQL types carefully to avoid data mismatches.
  - Test procedures in isolation and with the GraphQL layer.

---

## Conclusion

The **"Mutation Execution via Stored Procedures"** pattern is a powerful tool for reducing duplication and ensuring atomicity in your API mutations. By shifting logic to the database, you gain consistency, performance, and leverage platform-specific optimizations. However, it requires discipline—procedures must be modular, well-tested, and versioned carefully.

**When to use it?**
- For critical financial or inventory operations where consistency is paramount.
- When your business rules are inherently database-centric.

**When to avoid it?**
- For simple mutations where the overhead isn’t justified.
- In polyglot architectures where multiple databases are used.

As with any pattern, success depends on **context**. Start small—migrate only the most complex mutations first—and iterate based on feedback. If done right, this approach can make your application more robust and maintainable.

---
# Further Reading
- [PostgreSQL Stored Procedures Docs](https://www.postgresql.org/docs/current/plpgsql.html)
- [GraphQL Resolvers with Raw SQL](https://graphql.org/docs/tutorials/how-to-use-raw-sql/)
- [Database vs. Application Logic](https://martinfowler.com/bliki/ThinApplicationThinDatabase.html)
```