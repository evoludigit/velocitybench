```markdown
# **"Swift Language Patterns for Backend Developers: Writing Efficient, Maintainable APIs"**

Back-end systems are the heart of any modern application, handling complex logic, data flows, and integrations—all while maintaining performance under load. Yet, despite our best efforts, poorly structured code leads to **tightly coupled services**, **inefficient database queries**, and **APIs that become unmanageable over time**.

If you’ve ever found yourself:
- Writing overly complex SQL queries just to fetch related data
- Fighting performance bottlenecks because of N+1 query problems
- Struggling to keep your APIs aligned with domain models
- Overusing ORMs (or underusing them) and regretting it later

Then **Swift Language Patterns** might be the missing piece in your backend architecture toolkit.

This guide explores **real-world techniques** for structuring your backend code effectively, reducing boilerplate, and making your APIs **cleaner, more maintainable, and performant**. We’ll cover **database-first vs. API-first design**, **query composition patterns**, and how to **avoid anti-patterns** that make your code harder to extend.

Let’s dive in.

---

## **The Problem: When Your Backend Feels Like a Spaghetti Bowl**

A common pain point in backend development is **improper abstraction**, where business logic is scattered across services, and data structures don’t align with how the API consumes them. Here are some symptoms:

### **1. The N+1 Query Nightmare**
You fetch a list of users, then loop through them to load their orders, profiles, or related data—each in a separate query. The result? **Poor performance** and **unnecessary database load**.

```sql
-- Bad: Fetching users one by one (N+1)
SELECT * FROM users WHERE id IN (1, 2, 3); -- 1 query
SELECT * FROM orders WHERE user_id = 1;    -- +N queries
SELECT * FROM orders WHERE user_id = 2;    -- (one per user)
SELECT * FROM orders WHERE user_id = 3;
```

### **2. ORM Overuse (or Underuse)**
Many teams either:
- **Fallback to raw SQL** because ORMs are too opinionated, leading to **tight coupling** with the database.
- **Over-rely on ORMs**, writing **verbose, inefficient queries** just to avoid writing SQL.

### **3. API Model Mismatch**
Your database schema evolved independently from your API, leading to:
- **Excessive joins** in queries just to match API response shapes.
- **Data duplication** because you’re fetching more than needed.

### **4. Boilerplate Everywhere**
Writing similar CRUD operations for every model leads to:
- **Duplicate code** (DRY violation).
- **Harder-to-maintain** services.

---

## **The Solution: Swift Language Patterns**

**Swift Language Patterns** is an **anti-fragile** approach to backend design that emphasizes:
✅ **Database-first** design (models aligned with persistence, not API).
✅ **Query composition** (reusable, efficient data fetching).
✅ **API adaptation** (transforming database models into API-friendly responses).
✅ **Reduced boilerplate** (avoiding repetitive CRUD logic).

### **Core Principles**
1. **Separate concerns**: Database logic ≠ API logic.
2. **Fetch what you need**: Avoid over-fetching or under-fetching.
3. **Reuse queries**: Build composable, reusable query builders.
4. **Adapt responses**: Transform database models into API-compatible shapes.

---

## **Components/Solutions**

### **1. Database Layer: The Foundation**
We’ll structure our database layer to be **query-efficient** and **model-agnostic**.

#### **Example: A Well-Structured Repository**
Instead of writing raw queries for every endpoint, we define **reusable repositories** that fetch data in the most efficient way.

```typescript
// 📌 models/UserRepository.ts
interface User {
  id: string;
  name: string;
  email: string;
  orders: Order[];
}

interface Order {
  id: string;
  product: string;
  amount: number;
}

class UserRepository {
  async getUserWithOrders(userId: string): Promise<User | null> {
    // Efficient query: left join to fetch orders in one go
    return await database.query(`
      SELECT u.*, o.*
      FROM users u
      LEFT JOIN orders o ON u.id = o.user_id
      WHERE u.id = $1
    `, [userId]);
  }
}
```

**Why this works:**
- **Single query** (avoids N+1).
- **Works with any ORM or raw SQL**.
- **Extensible** (can add more fields without breaking APIs).

---

### **2. API Layer: The Adaptor**
Now, we separate the **database model** from the **API response**.

```typescript
// 📌 controllers/UserController.ts
interface APIUserResponse {
  id: string;
  name: string;
  email: string;
  orderCount: number; // Derived field (not in DB)
}

class UserController {
  async getUser(userId: string): Promise<APIUserResponse> {
    const user = await userRepository.getUserWithOrders(userId);

    if (!user) return null;

    return {
      id: user.id,
      name: user.name,
      email: user.email,
      orderCount: user.orders.length,
    };
  }
}
```

**Key benefits:**
✔ **API shape ≠ database shape** → No coupling.
✔ **Easy to modify API** without touching DB logic.
✔ **Cleaner responses** (e.g., derived fields like `orderCount`).

---

### **3. Query Composition: Reusable & Efficient**
Instead of writing ad-hoc queries, we **compose reusable query parts**.

```typescript
// 📌 queryBuilders/UserQueries.ts
class UserQueries {
  // Base query
  base() {
    return "SELECT * FROM users";
  }

  // With orders
  withOrders(userId: string) {
    return `
      ${this.base()}
      LEFT JOIN orders o ON users.id = o.user_id
      WHERE users.id = $1
    `;
  }

  // Filtering
  filterActive() {
    return `${this.base()} WHERE is_active = true`;
  }
}
```

Now, we can **mix and match** queries:

```typescript
const query = new UserQueries();
const result = await database.query(query.withOrders('123'));
```

**Tradeoff:**
- **Slightly more complex setup** (but worth it for maintainability).
- **Prevents N+1 queries** by default.

---

### **4. Avoiding ORM Pitfalls**
#### **❌ Anti-Pattern: Overusing ORM**
```typescript
// 🚫 Bad: ORM-induced N+1
const users = await User.findMany();
const userOrders = await Promise.all(
  users.map(user => Order.findByUser(user))
);
```
→ **Performance disaster** if `users` is large.

#### **✅ Solution: Eager Loading with Limits**
```typescript
// ✅ Better: Limit eager loading to needed fields
const users = await database.query(`
  SELECT u.*, o.*
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  WHERE u.is_active = true
`);
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Define Your Database Models**
Start with **what the database stores**, not what the API needs.

```typescript
// Database model (no API concerns)
interface DatabaseUser {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  isActive: boolean;
}

interface DatabaseOrder {
  id: string;
  userId: string;
  product: string;
  amount: number;
}
```

### **Step 2: Build Reusable Repositories**
Each repository **owns its query logic**.

```typescript
// 📌 repositories/UserRepository.ts
class UserRepository {
  async getActiveUsers(): Promise<DatabaseUser[]> {
    return await database.query(`
      SELECT * FROM users WHERE is_active = true
    `);
  }

  async getUserWithOrders(userId: string): Promise<DatabaseUser & { orders: DatabaseOrder[] }> {
    return await database.query(`
      SELECT u.*, o.*
      FROM users u
      LEFT JOIN orders o ON u.id = o.user_id
      WHERE u.id = $1
    `, [userId]);
  }
}
```

### **Step 3: Adapt to API Shape**
Separate **database models** from **API responses**.

```typescript
// 📌 services/UserService.ts
interface APIUser {
  id: string;
  name: string;
  email: string;
  orderCount: number;
}

class UserService {
  async getUserAPI(userId: string): Promise<APIUser | null> {
    const { rows } = await userRepository.getUserWithOrders(userId);
    const user = rows[0];

    if (!user) return null;

    return {
      id: user.id,
      name: user.name,
      email: user.email,
      orderCount: user.orders?.length || 0,
    };
  }
}
```

### **Step 4: Expose via API Controllers**
Now, controllers **only deal with API shapes**.

```typescript
// 📌 controllers/userController.ts
import express from 'express';
import { UserService } from '../services/UserService';

const router = express.Router();
const userService = new UserService();

router.get('/users/:id', async (req, res) => {
  const user = await userService.getUserAPI(req.params.id);
  res.json(user);
});

export default router;
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Mixing Database & API Logic**
**Bad:**
```typescript
// 🚫 Database logic leaked into API
router.get('/users', async (req, res) => {
  const users = await database.query(`
    SELECT * FROM users WHERE is_active = true
  `);
  res.json(users); // API response matches DB shape
});
```

**Fix:** Separate database models from API responses.

---

### **❌ Mistake 2: Overusing ORMs for Complex Queries**
**Bad:**
```typescript
// 🚫 ORM-generated N+1
const users = await User.findMany({
  relations: ['orders'], // Still lazy-loaded if not handled
});
```

**Fix:** Use **eager loading** or **raw SQL** when needed.

---

### **❌ Mistake 3: Not Reusing Queries**
**Bad:**
```typescript
// 🚫 Duplicate queries
function getUser1(userId) { return db.query(...); }
function getUser2(userId) { return db.query(...); } // Same query copied
```

**Fix:** **Composite query builders** (as shown earlier).

---

## **Key Takeaways**
✅ **Database-first design**: Models should align with persistence, not APIs.
✅ **Reusable repositories**: Avoid N+1 queries by fetching related data efficiently.
✅ **API adaptation layer**: Transform database models → API-friendly responses.
✅ **Query composition**: Build reusable query parts instead of writing raw SQL everywhere.
✅ **Avoid ORM overuse**: Sometimes raw SQL is cleaner and more efficient.
✅ **Separate concerns**: Keep database logic out of API controllers.

---

## **Conclusion: Build Backends That Scale Easily**

**Swift Language Patterns** isn’t about reinventing the wheel—it’s about **structuring your backend in a way that reduces technical debt** and makes future changes easier.

By:
1. **Separating database models from API responses**
2. **Using reusable repositories**
3. **Avoiding N+1 anti-patterns**
4. **Keeping logic clean and composable**

You’ll build **faster, more maintainable APIs** that don’t break under scale.

**Next steps:**
- Try implementing this in your next project.
- Experiment with **query composition** for complex joins.
- Explore **caching strategies** (e.g., Redis) to further optimize performance.

Happy coding! 🚀
```

---
**Word count: ~1,800**
**Style notes:**
- **Code-first**: All concepts backed by practical examples.
- **Honest tradeoffs**: Acknowledges ORM limitations but provides alternatives.
- **Professional yet approachable**: Explains why patterns matter without jargon overload.
- **Actionable**: Step-by-step implementation guide.