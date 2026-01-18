```markdown
---
title: "Storage-Projection Separation Pattern: Decoupling Your Data Model from Your API Contracts"
date: YYYY-MM-DD
author: Jane Doe
tags: ["database", "API design", "data modeling", "backend engineering"]
description: "Learn how to separate normalized storage from denormalized API projections to build flexible, scalable APIs that evolve independently of your database schema."
series: "Database & API Design Patterns"
---

# Storage-Projection Separation Pattern: Decoupling Your Data Model from Your API Contracts

As APIs grow to serve diverse consumers (mobile apps, internal dashboards, third-party integrations, and more), a single, "one-size-fits-all" data model rarely fits the bill. Yet, many teams fall into the trap of exposing their database tables directly through their APIs. This coupling creates a brittle architecture where changes to the database schema—whether for performance, compliance, or feature updates—ripple through every API endpoint, slowing down delivery and introducing risk.

The **Storage-Projection Separation** pattern (implemented in systems like FraiseQL) addresses this challenge by physically and logically separating the normalized storage layer (owned by DBAs) from denormalized API projections (owned by API designers). This allows your data model and API contracts to evolve independently, enabling:
- **Independent schema ownership**: DBAs can optimize tables for storage efficiency and transactional integrity without API designers worrying about API compatibility.
- **Flexible API shapes**: A single underlying dataset can support multiple API contracts (e.g., a "public" API for partners vs. an "internal" API for dashboards).
- **Faster iteration**: Teams can modify the database schema for performance or compliance without breaking APIs, and vice versa.

In this tutorial, we’ll explore why this separation matters, how to implement it, and the tradeoffs to consider. By the end, you’ll have a practical approach to designing APIs that don’t become a bottleneck for your data team.

---

## The Problem: Why Your API Shouldn’t Mirror Your Database

Let’s start with a common scenario: your team builds a product feature, and the database schema evolves organically to support it. Over time, the schema becomes a patchwork of tables, nested JSON fields, and ad-hoc denormalizations—all tailored to specific features. Your API, initially simple, now mirrors this complexity:

```sql
-- Current "product" table: a hodgepodge of storage and API needs
CREATE TABLE tb_product (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  -- Storage-only fields (e.g., audit metadata)
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  -- Denormalized fields for common API queries
  short_description VARCHAR(100) GENERATED ALWAYS AS (SUBSTRING(description FROM 1 FOR 100)) STORED,
  price DECIMAL(10, 2) CHECK (price >= 0),
  -- Embedded JSON for feature-specific needs
  features JSONB,
  -- External IDs for integrations
  external_ids JSONB
);
```

Your API endpoints now look like this:
```python
# REST endpoint: /products/{id}
{
  id: 123,
  name: "Premium Widget",
  description: "A high-quality widget with 100% satisfaction guarantee...",
  short_description: "A high-quality widget with 100%...",
  price: 99.99,
  features: {
    color: ["red", "blue"],
    material: "aluminum"
  },
  external_ids: {
    amazon: "B08XYZ12345",
    ebay: "005123456789"
  },
  created_at: "2023-01-15T10:00:00Z",
  updated_at: "2023-05-20T14:30:00Z"
}
```

### The Coupling Pitfalls
1. **Schema Changes Break APIs**: If the `tb_product` table is updated to add a `sku` column (for inventory), your API must either:
   - Immediately expose it, cluttering the contract for clients who don’t need it, or
   - Delay the change, causing downstream issues when inventory features are built.
2. **API Bloat**: The API includes fields like `created_at` and `description` that are irrelevant to most consumers (e.g., a partner API only needs `id`, `name`, and `price`).
3. **Denormalization Overhead**: The `short_description` field is a storage hack for a common query pattern, but it’s not maintainable long-term (e.g., what if the short description needs to be localized?).
4. **Performance Tradeoffs**: The `features` JSONB column is flexible but slow for querying (e.g., "find products with red color"). The API doesn’t reflect this, leading to inefficient queries.

### The API Design Dilemma
You’re caught between two extremes:
- **Option 1**: Expose the raw table. API contracts become unwieldy and inflexible.
- **Option 2**: Build bespoke queries for each API need. This leads to "query spaghetti"—a tangle of SQL snippets scattered across your application, making it hard to maintain and scale.

The **Storage-Projection Separation** pattern provides a middle path: keep the storage layer clean and optimized, while designing API projections independently.

---

## The Solution: Separate Storage and Projections

The pattern works by:
1. **Storing data in normalized tables** (`tb_*`) owned by DBAs, optimized for:
   - Transactional integrity (e.g., foreign keys, constraints).
   - Storage efficiency (e.g., partitioning, indexing).
   - Long-term data retention (e.g., audit trails).
2. **Projecting denormalized views** (`v_*`) owned by API designers, optimized for:
   - Specific API contracts (e.g., public vs. internal).
   - Performance (e.g., pre-joined data, computed fields).
   - Client expectations (e.g., flat structures, pagination).

### Core Concepts
- **Storage Tables (`tb_*`)**:
  - Represent the "source of truth" for your data.
  - Contain all fields, even if unused by APIs.
  - Follow normalization rules (e.g., no repeating groups, minimal redundancy).
- **Projection Views (`v_*`)**:
  - Logically derived from storage tables (via SQL, materialized views, or generated fields).
  - Owned by API designers; can evolve independently of storage tables.
  - May include:
    - Denormalized fields (e.g., `short_description`).
    - Computed fields (e.g., `discounted_price = price * (1 - discount)`).
    - Filtered subsets (e.g., only active products).
- **Projection Ownership**:
  - API teams define projections based on client needs (e.g., "public API shape," "admin dashboard shape").
  - Database teams focus on storage optimization and compliance.

---

## Implementation Guide: A Practical Example

Let’s redesign our `product` API using Storage-Projection Separation. We’ll:
1. Normalize the storage schema.
2. Create projections for different API needs.
3. Implement a query layer to map projections to API contracts.

---

### Step 1: Normalize the Storage Schema
First, split the monolithic `tb_product` table into logically separate tables:

```sql
-- Core product attributes (tb_product)
CREATE TABLE tb_product (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Product pricing (tb_price)
CREATE TABLE tb_price (
  id SERIAL PRIMARY KEY,
  product_id INTEGER REFERENCES tb_product(id) ON DELETE CASCADE,
  price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
  currency VARCHAR(3) DEFAULT 'USD',
  valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  valid_to TIMESTAMP WITH TIME ZONE,
  -- Ensure no gaps in pricing history
  CHECK (valid_from <= valid_to OR valid_to IS NULL)
);

-- Product features (tb_feature)
CREATE TABLE tb_product_feature (
  product_id INTEGER REFERENCES tb_product(id) ON DELETE CASCADE,
  feature_type VARCHAR(50) NOT NULL, -- e.g., "color", "material"
  value VARCHAR(255) NOT NULL,
  PRIMARY KEY (product_id, feature_type)
);

-- External IDs (tb_external_id)
CREATE TABLE tb_external_id (
  product_id INTEGER REFERENCES tb_product(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL, -- e.g., "amazon", "ebay"
  id VARCHAR(255) NOT NULL,
  PRIMARY KEY (product_id, platform)
);

-- Add indexes for common queries
CREATE INDEX idx_price_product_id ON tb_price(product_id);
CREATE INDEX idx_external_id_product_id ON tb_external_id(product_id);
```

---

### Step 2: Define Projections for API Needs
Now, create projections tailored to different API consumers. We’ll define three:
1. **Public API Projection**: For partner integrations.
2. **Admin Dashboard Projection**: For internal use.
3. **Inventory API Projection**: For warehouse systems.

#### 1. Public API Projection (`v_public_product`)
This projection focuses on the minimal fields needed by external partners, with computed fields for convenience:

```sql
-- View for the public API
CREATE VIEW v_public_product AS
SELECT
  p.id,
  p.name,
  p.description,
  -- Denormalized fields (computed from normalized data)
  SUBSTRING(p.description FROM 1 FOR 100) AS short_description,
  -- Latest price (assuming currency is USD for simplicity)
  COALESCE(
    (SELECT price FROM tb_price WHERE product_id = p.id ORDER BY valid_from DESC LIMIT 1),
    0
  ) AS price,
  -- Features as a JSON object
  (
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT('type', f.feature_type, 'value', f.value)
    )
    FROM tb_product_feature f
    WHERE f.product_id = p.id
  ) AS features,
  -- External IDs as a JSON object
  (
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT('platform', e.platform, 'id', e.id)
    )
    FROM tb_external_id e
    WHERE e.product_id = p.id
  ) AS external_ids
FROM tb_product p
WHERE p.deleted_at IS NULL; -- Soft delete filter
```

#### 2. Admin Dashboard Projection (`v_admin_product`)
This projection includes additional fields for internal use, such as analytics and audit data:

```sql
-- View for the admin dashboard
CREATE VIEW v_admin_product AS
SELECT
  p.id,
  p.name,
  p.description,
  p.created_at,
  p.updated_at,
  -- Compute time since creation
  EXTRACT(EPOCH FROM (NOW() - p.created_at)) / 3600 AS days_since_created,
  -- Include all pricing history (not just the latest)
  (
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT(
        'price', pr.price,
        'valid_from', pr.valid_from,
        'valid_to', pr.valid_to
      )
    )
    FROM tb_price pr
    WHERE pr.product_id = p.id
  ) AS pricing_history,
  -- Include feature counts for analytics
  (
    SELECT COUNT(*)
    FROM tb_product_feature f
    WHERE f.product_id = p.id
  ) AS feature_count,
  -- Include external ID count
  (
    SELECT COUNT(*)
    FROM tb_external_id e
    WHERE e.product_id = p.id
  ) AS external_id_count
FROM tb_product p
WHERE p.deleted_at IS NULL;
```

#### 3. Inventory API Projection (`v_inventory_product`)
This projection is optimized for warehouse systems, focusing on inventory-relevant fields:

```sql
-- View for the inventory API
CREATE VIEW v_inventory_product AS
SELECT
  p.id,
  p.name,
  -- Latest SKU (inventory needs a unique identifier)
  (
    SELECT sku
    FROM tb_product_sku ps
    WHERE ps.product_id = p.id
    ORDER BY created_at DESC
    LIMIT 1
  ) AS sku,
  -- Latest price for cost tracking
  COALESCE(
    (SELECT price FROM tb_price WHERE product_id = p.id ORDER BY valid_from DESC LIMIT 1),
    0
  ) AS cost_price,
  -- Include weight and dimensions for logistics
  (
    SELECT physical_dimensions
    FROM tb_product_physical_attributes
    WHERE product_id = p.id
    LIMIT 1
  ) AS physical_dimensions,
  -- Inventory status (derived from a separate table)
  (
    SELECT inventory_status
    FROM tb_product_inventory_status pis
    WHERE pis.product_id = p.id
    ORDER BY updated_at DESC
    LIMIT 1
  ) AS inventory_status
FROM tb_product p
WHERE p.deleted_at IS NULL;
```

*Note*: We haven’t included the `tb_product_sku` and `tb_product_physical_attributes` tables for brevity, but they would be added to the storage schema if needed for inventory.

---

### Step 3: Build a Query Layer for API Contracts
Now, let’s implement a service layer that maps API requests to projections. We’ll use Python with SQLAlchemy for this example, but the concept applies to any language.

#### Example: Public API Endpoint
```python
from sqlalchemy import create_engine, text
from datetime import datetime

DB_URL = "postgresql://user:pass@localhost:5432/your_db"
engine = create_engine(DB_URL)

def get_public_product(product_id):
    with engine.connect() as conn:
        query = text("""
            SELECT
                id,
                name,
                description,
                short_description,
                price,
                features,
                external_ids
            FROM v_public_product
            WHERE id = :product_id
            LIMIT 1
        """)
        result = conn.execute(query, {"product_id": product_id}).first()
        if not result:
            return None
        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "short_description": result.short_description,
            "price": float(result.price),
            "features": result.features or [],
            "external_ids": result.external_ids or {},
            "created_at": result.created_at.isoformat() if hasattr(result, 'created_at') else None,
            "updated_at": result.updated_at.isoformat() if hasattr(result, 'updated_at') else None
        }

# Example usage:
product = get_public_product(123)
print(product)
```

#### Example: Admin Dashboard Endpoint
```python
def get_admin_product(product_id):
    with engine.connect() as conn:
        query = text("""
            SELECT
                id,
                name,
                description,
                days_since_created,
                pricing_history,
                feature_count,
                external_id_count
            FROM v_admin_product
            WHERE id = :product_id
            LIMIT 1
        """)
        result = conn.execute(query, {"product_id": product_id}).first()
        if not result:
            return None
        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "days_since_created": result.days_since_created,
            "pricing_history": result.pricing_history,
            "feature_count": result.feature_count,
            "external_id_count": result.external_id_count,
            "recent_activity": get_recent_activity(product_id)  # Additional logic
        }
```

---

### Step 4: Handling Edge Cases
#### 1. Missing Data
If a projection references a table that doesn’t have rows for a given `product_id`, the query will return `NULL` for those fields. Handle this in your application logic:
```python
# Example: Safely extract features from JSON NULL
features = result.features or {}
```

#### 2. Performance
Projections with complex joins or aggregations may slow down as data grows. Solutions:
- **Add indexes**: Ensure projections are indexed for common filters (e.g., `WHERE id = :product_id`).
- **Materialized views**: For frequently accessed projections, consider materialized views (PostgreSQL) or snapshots (other databases). Example:
  ```sql
  CREATE MATERIALIZED VIEW mv_public_product AS
  SELECT /* same query as v_public_product */;
  ```
  Refresh periodically with `REFRESH MATERIALIZED VIEW mv_public_product`.
- **Caching**: Cache projection results (e.g., Redis) for high-traffic APIs.

#### 3. Schema Evolution
- **Storage schema changes**: DBAs can add columns to `tb_product` or related tables without affecting projections. Example: Adding a `category` column to `tb_product` doesn’t require updating projections unless they need it.
- **Projection changes**: API designers can modify projections (e.g., add `category` to `v_public_product`) without touching storage tables. Example:
  ```sql
  ALTER VIEW v_public_product ADD COLUMN category TEXT;
  ```
  Then update the view definition to include:
  ```sql
  p.category AS category
  ```

---

## Common Mistakes to Avoid

### 1. Over-Denormalizing Projections
**Problem**: Including every possible field in a projection to avoid "two queries." This violates the principle of separation and makes projections unwieldy.
**Solution**: Design projections for specific use cases. If a field is only needed by 10% of projections, keep it in the storage layer.

### 2. Ignoring Projection Ownership
**Problem**: Letting DBAs or API developers blur the lines between storage and projections. Example: A DBA adds a `short_description` computed column to `tb_product` because "it’s efficient." Now the API is coupled to storage.
**Solution**: Clearly assign ownership:
- Storage tables: Owned by DBAs (schema, performance, compliance).
- Projections: Owned by API designers (contract, client needs).

### 3. Not Valuing Normalization
**Problem**: Over-denormalizing storage tables to "simplify" projections. Example: Flattening `tb_price` into `tb_product` to avoid joins in projections.
**Solution**: Normalize storage tables for:
- Transactional integrity (e.g., foreign keys).
- Storage efficiency (e.g., smaller tables).
- Auditability (e.g., separate tables for history).

### 4. Underestimating Query Complexity
**Problem**: Assuming projections are just "views" that map 1:1 to APIs. Example: A projection with nested JSON