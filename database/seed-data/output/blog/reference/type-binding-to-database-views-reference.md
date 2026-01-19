**[Pattern] Type Binding to Database Views – Reference Guide**

---

### **1. Overview**
FraiseQL’s **Type Binding to Database Views** pattern ensures strong type-safety by mapping FraiseQL types directly to database views rather than resolver functions. This approach enforces **compile-time validation** of both the view’s existence and its schema alignment with the FraiseQL type definition. By eliminating runtime discrepancies between API schema and database schema, this pattern reduces errors, improves maintainability, and enables tighter integration between your application’s data model and persistence layer.

Unlike traditional resolver-based setups (e.g., GraphQL), this pattern decouples query logic from data source definitions, allowing teams to manage database schema and API schema independently while ensuring consistency through compile-time checks.

---

### **2. Key Concepts**

#### **2.1. Binding FraiseQL Types to Views**
Each FraiseQL `Type` is annotated with a `database_view` attribute, specifying:
- **View name** (e.g., `posts`).
- **Database connection** (e.g., `primary`, `staging`).
- **Optional schema validation** (e.g., `strict`, `lenient`).

Example:
```typescript
@fraiseql.type({
  database_view: {
    viewName: "orders",
    connection: "primary",
    validation: "strict"
  }
})
class Order {
  id: string;
  customerId: string;
  total: number;
  createdAt: Date;
}
```

#### **2.2. Schema Validation Modes**
| Mode        | Behavior                                                                 |
|-------------|---------------------------------------------------------------------------|
| `strict`    | The view **must** match the type’s schema exactly (column names, types, nullability). |
| `lenient`   | The view may have **additional columns**, but required fields must align. |
| `dynamic`   | The view’s schema is inferred at runtime (no compile-time checks).        |

#### **2.3. Compile-Time Verification**
FraiseQL’s compiler:
1. **Resolves the view** in the specified database connection.
2. **Validates the schema** against the type definition.
3. **Generates type-safe queries** (e.g., `Order.find()`) that reference the view directly.

**Error Cases:**
- `ViewNotFoundError`: The view doesn’t exist in the database.
- `SchemaMismatchError`: The view’s columns don’t match the type (in `strict` mode).

---

### **3. Schema Reference**
Below is the required schema for binding a FraiseQL type to a database view.

#### **3.1. Type Annotation Schema**
| Attribute          | Type               | Required | Description                                                                 |
|--------------------|--------------------|----------|-----------------------------------------------------------------------------|
| `database_view`    | Object             | Yes      | Binds the type to a database view.                                           |
| `viewName`         | `string`           | Yes      | Name of the database view (case-sensitive).                                  |
| `connection`       | `string`           | No       | Database connection name (default: `"primary"`).                             |
| `validation`       | `"strict" \| "lenient" \| "dynamic"` | No | Schema validation mode (default: `"strict"`).                              |
| `aliases`          | `Record<string, string>` | No    | Maps type field names to view column names (e.g., `{"customer_id": "customerId"}`). |

#### **3.2. Database View Requirements**
| Requirement               | Details                                                                 |
|---------------------------|-------------------------------------------------------------------------|
| **Schema Stability**      | Views must not be altered without updating the FraiseQL type.            |
| **Primary Key**           | The view must have a primary key (e.g., `id`) that matches the type’s ID field. |
| **Column Alignment**      | In `strict` mode, column names/types must match the type’s fields exactly. |
| **Indexing**              | FraiseQL recommends indexing frequently queried columns for performance.  |

---

### **4. Query Examples**
#### **4.1. Basic Query**
```typescript
// Define a type bound to a view
@fraiseql.type({
  database_view: { viewName: "products", connection: "primary" }
})
class Product {
  id: string;
  name: string;
  price: number;
}

// Query the view directly
const products = await Product.find();
```

#### **4.2. Filtering with View Columns**
```typescript
// Filter by a view column (e.g., "category" in the product view)
const electronics = await Product.find({
  where: { category: "Electronics" }
});
```

#### **4.3. Joined Queries (Multiple Views)**
FraiseQL supports **view joins** via `relation` fields. Example:
```typescript
@fraiseql.type({
  database_view: { viewName: "order_items" }
})
class OrderItem {
  id: string;
  orderId: string;       // Foreign key
  productId: string;     // Foreign key
  quantity: number;
}

@fraiseql.type({
  database_view: { viewName: "orders" }
  relations: {
    items: OrderItem       // Resolves to "order_items" view with `orderId` filter
  }
})
class Order {
  id: string;
  customerId: string;
  items: OrderItem[];     // Automatically filtered by `orderId`
}
```

#### **4.4. Dynamic Validation (Lenient Mode)**
```typescript
@fraiseql.type({
  database_view: { viewName: "user_profiles", validation: "lenient" }
})
class UserProfile {
  id: string;
  username: string;       // View may have additional columns (e.g., "bio")
}
```

---

### **5. Related Patterns**
| Pattern                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **[Resolver Functions]**         | Fallback for views that can’t be bound directly (e.g., derived data).      |
| **[Database Connection Pooling]**| Manages connections for multiple `database_view` bindings.                  |
| **[Schema Migration Guardrails]**| Tools to prevent breaking changes to bound views during migrations.         |
| **[View Materialization]**        | Materialized views for complex aggregations (not direct table-bound types).|
| **[Soft Deletes]**               | Extends view binding to handle `is_deleted` flags (e.g., `WHERE is_deleted = false`). |

---

### **6. Best Practices**
1. **Idempotent Views**: Ensure views are rebuilt predictably (e.g., trigger-based or scheduled).
2. **Connection Management**: Use named connections for environments (e.g., `dev`, `prod`).
3. **Testing**: Validate view schemas in CI/CD before deploying types.
4. **Aliases**: Use `aliases` for legacy databases where column names differ from TypeScript’s camelCase.
5. **Performance**: Index frequently filtered columns (e.g., `createdAt`, `status`).

---
### **7. Troubleshooting**
| Issue                          | Solution                                                                 |
|--------------------------------|--------------------------------------------------------------------------|
| `SchemaMismatchError`          | Update the type or view to align schemas.                                |
| `ViewNotFoundError`            | Verify the view exists in the specified connection.                       |
| Slow Queries                   | Add indexes to view columns used in `where` clauses or joins.             |
| Circular Dependencies          | Refactor types/views to avoid mutual relations (e.g., `A → B → A`).      |

---
**Note**: For advanced use cases (e.g., computed fields, custom SQL), combine this pattern with **resolver functions** via `fraiseql.type({ resolver: ... })`.