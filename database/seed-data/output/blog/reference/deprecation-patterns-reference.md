# **[Pattern] Deprecation Patterns – Reference Guide**

---

## **Overview**
The **Deprecation Patterns** reference guide outlines structured ways to mark and phase out deprecated fields, methods, or services in APIs, databases, or codebases. Proper deprecation ensures backward compatibility while guiding users toward modern alternatives. This pattern standardizes deprecation policies, communication, and transition timelines to minimize disruption.

Deprecation should follow clear **notification cycles**, **deprecation warnings**, and **removal deadlines**. This guide covers implementation details, schema references, and query examples for managing deprecated entities.

---

## **Schema Reference**

| **Field/Property** | **Type**       | **Description**                                                                                                                   | **Example Value**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `__deprecated`     | Boolean        | Marks whether an entity is deprecated (`true`/`false`).                                                                           | `true`                                 |
| `deprecation_date` | DateTime       | Date when deprecation was added.                                                                                               | `2023-01-15T00:00:00Z`                |
| `deprecated_since` | String         | Semantic version where deprecation was introduced (e.g., `v1.2.0`).                                                            | `"v3.2.1"`                            |
| `replacement`      | String/Object  | Suggested alternative (method, field, or API version) with a brief description.                                                 | `{"field": "new_field", "description": "Use `new_field` instead."}` |
| `deprecation_warning` | String       | User-facing message explaining why the field is deprecated and urging migration.                                                | `"Warning: `old_field` will be removed in v5.0. Use `new_field`."` |
| `deprecated_until` | DateTime       | Last date when the entity will be supported (if phased out).                                                                      | `2024-06-30T23:59:59Z`                |
| `affected_entities`| Array[Object]  | List of dependent resources (e.g., tables, APIs) impacted by this deprecation.                                                 | `[{"resource": "users", "field": "email"}}` |

---

## **Implementation Details**

### **1. Marking Fields as Deprecated**
Deprecation begins by adding metadata to deprecated entities (e.g., database fields, API endpoints, or class methods). Use annotations, schema comments, or dedicated metadata tables.

#### **Example: Database Table Schema with Deprecation Metadata**
```sql
ALTER TABLE products ADD COLUMN deprecated BOOLEAN DEFAULT false;
ALTER TABLE products ADD COLUMN deprecation_date TIMESTAMP DEFAULT NOW();
ALTER TABLE products ADD COLUMN replacement JSON DEFAULT NULL;
```

#### **Example: Python/Django Model Annotation**
```python
class Product(models.Model):
    deprecated = models.BooleanField(default=False)
    deprecated_since = models.CharField(max_length=20, blank=True, null=True)
    replacement = models.JSONField(default=None, blank=True, null=True)
    deprecation_warning = models.TextField(blank=True, null=True)
```

### **2. Deprecation Stages**
Deprecation follows a **three-phase lifecycle**:
1. **Notification Phase** – Deprecation is announced (e.g., via changelogs, API docs).
2. **Deprecation Warning Phase** – Deprecated entities log warnings (e.g., in API responses).
3. **Removal Phase** – Deprecated entities are deleted (after `deprecated_until`).

#### **Example: Deprecation Warning in an API Response**
```json
{
  "status": "warning",
  "message": "Field `old_field` is deprecated since v1.2.0 and will be removed in v3.0.0. Use `new_field` instead.",
  "deprecated": true,
  "replacement": {
    "field": "new_field",
    "version": "v2.3.0+"
  }
}
```

### **3. Querying Deprecated Entities**
Use queries to filter, log, or migrate deprecated data.

#### **SQL Query to Find Deprecated Products**
```sql
SELECT * FROM products
WHERE deprecated = true
ORDER BY deprecation_date DESC;
```

#### **Python Query with Django ORM**
```python
from django.db.models import Q

deprecated_products = Product.objects.filter(
    Q(deprecated=True) | Q(deprecated_since__isnull=False)
).order_by('-deprecation_date')
```

### **4. Handling Deprecated Entities in Code**
- **Logging Warnings**: Use decorators or middleware to log deprecation warnings.
  ```python
  def deprecated_method(self, *args, **kwargs):
      warnings.warn("Method `old_method` is deprecated. Use `new_method` instead.",
                    DeprecationWarning, stacklevel=2)
      # Fallback logic
  ```
- **Automated Migration Scripts**: Generate migration scripts to replace deprecated fields.
  ```python
  def migrate_old_to_new(user_id):
      user = User.objects.get(id=user_id)
      user.new_field = user.old_field  # Replace deprecated field
      user.deprecated = False
      user.save()
  ```

---

## **Query Examples**

### **1. List All Deprecated API Endpoints**
```sql
SELECT api_id, endpoint, deprecated_since, replacement
FROM api_endpoints
WHERE deprecated = true;
```

### **2. Find Deprecated Database Fields in a Table**
```python
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'products'
        AND column_name LIKE '%_old%'
    """)
    deprecated_columns = cursor.fetchall()
```

### **3. Generate Deprecation Warnings for a Database Schema**
```python
import psycopg2
conn = psycopg2.connect("dbname=test user=postgres")
cursor = conn.cursor()
cursor.execute("""
    SELECT tablename, column_name, description
    FROM pg_description
    WHERE objid = 'product_table'::regclass
    AND description LIKE '%deprecated%';
""")
print("Deprecated fields:", cursor.fetchall())
```

---

## **Requirements and Best Practices**
1. **Clear Communication**:
   - Announce deprecations in changelogs, release notes, and migration guides.
   - Example:
     ```
     BREAKING CHANGE: `old_field` removed in v4.0.0. Migrate to `new_field` by upgrading to v3.5.0.
     ```
2. **Versioned Deprecation**:
   - Use semantic versioning (e.g., `v1.2.0`) to track deprecations.
3. **Grace Periods**:
   - Allow 6–12 months between deprecation notice and removal.
4. **Automated Warnings**:
   - Emit warnings in logs, API responses, and IDEs (e.g., `@deprecated` decorators).
5. **Testing**:
   - Write unit tests to verify deprecated entities still work during the deprecation phase.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **[Versioning](Versioning_Pattern.md)** | Manage parallel API versions while deprecating older ones.                                         |
| **[Migration](Migration_Pattern.md)**   | Guide users on migrating from deprecated to new fields.                                             |
| **[Feature Flags](FeatureFlags_Pattern.md)** | Roll out new features gradually while deprecated ones remain available.                          |
| **[API Deprecation Headers](DeprecationHeaders_Pattern.md)** | Use HTTP headers (e.g., `Deprecation: true`) to signal deprecation in API responses.          |

---

## **Example Workflow**
1. **Announce**: Release v1.2.0 with `deprecated_since="v1.2.0"` for `old_field`.
2. **Warn**: API returns a deprecation warning for `old_field` in v2.0.0.
3. **Migrate**: Write scripts to auto-update `old_field` to `new_field` by v3.0.0.
4. **Remove**: Drop `old_field` in v3.0.0 after `deprecated_until` passes.