# VelocityBench Schema Architecture

## Overview

The VelocityBench benchmark suite uses a **layered schema architecture** to support multiple framework implementations with a single shared database schema, while allowing framework-specific optimizations.

## Layer 1: Shared Benchmark Schema

**Location**: `database/02-schema.sql`

**Purpose**: Single source of truth for all framework implementations

**Contents**:
- Pure Trinity Pattern implementation
- Core tables: `tb_user`, `tb_post`, `tb_comment`
- All 9+ frameworks use this schema unchanged
- No framework-specific configuration

**Trinity Pattern Structure**:
```sql
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,                    -- Internal PK (fast)
    id UUID UNIQUE NOT NULL,                       -- Public API identifier
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    -- ... other columns ...
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,                    -- Internal PK (fast)
    id UUID UNIQUE NOT NULL,                       -- Public API identifier
    fk_user INTEGER NOT NULL REFERENCES tb_user(pk_user),  -- Internal FK (fast)
    -- ... other columns ...
);

CREATE TABLE tb_comment (
    pk_comment SERIAL PRIMARY KEY,                 -- Internal PK (fast)
    id UUID UNIQUE NOT NULL,                       -- Public API identifier
    fk_post INTEGER NOT NULL REFERENCES tb_post(pk_post),  -- Internal FK (fast)
    fk_user INTEGER NOT NULL REFERENCES tb_user(pk_user),  -- Internal FK (fast)
    fk_parent INTEGER REFERENCES tb_comment(pk_comment),   -- Internal FK (fast)
    -- ... other columns ...
);
```

**Key Features**:
- ✅ Framework-agnostic (no framework-specific code)
- ✅ Shared across all implementations
- ✅ Performance-optimized with integer PKs/FKs
- ✅ API-ready with UUID identifiers
- ✅ Supports all query patterns (joins, filters, pagination)

## Layer 2: Framework-Specific Schema Extensions

Each framework creates its own schema configuration file that extends the shared schema with framework-specific smart tags, comments, and optimizations.

### PostGraphile Schema Extension

**Location**: `frameworks/postgraphile/database/schema.sql`

**Purpose**: Add PostGraphile-specific metadata and configuration

**Contents**:
- PostGraphile smart tags (`@omit`, `@name`, etc.)
- Column visibility configuration for GraphQL schema
- Table and column descriptions for introspection
- Query pattern indexes
- API documentation

**Key Smart Tags**:

```sql
-- Hide internal columns from GraphQL
COMMENT ON COLUMN tb_user.pk_user IS E'@omit all\nInternal primary key.';
COMMENT ON COLUMN tb_post.fk_user IS E'@omit all\nInternal foreign key.';

-- Make timestamps read-only
COMMENT ON COLUMN tb_user.created_at IS E'@omit create,update\nServer-managed timestamp.';
COMMENT ON COLUMN tb_user.updated_at IS E'@omit create,update\nServer-managed timestamp.';

-- Document public fields
COMMENT ON COLUMN tb_user.id IS 'Unique public identifier (UUID).';
COMMENT ON COLUMN tb_user.username IS 'Unique username for authentication.';
```

**Applied at Runtime**:

```typescript
// frameworks/postgraphile/src/db.ts
async function applyPostGraphileSchema(client: any) {
  const smartTags = `
    COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\\n...';
    -- ... other smart tags ...
  `;
  await client.query(smartTags);
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                 VelocityBench Benchmark Suite                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼────────┐ ┌───▼──────────┐ ┌─▼────────────────┐
        │  PostGraphile  │ │    Ruby      │ │      Other       │
        │   Framework    │ │ Rails ORM    │ │   Frameworks     │
        │   (test-a)     │ │ (test-b)     │ │   (test-c, ...)  │
        └────────────────┘ └──────────────┘ └──────────────────┘
                │               │                   │
                ▼               ▼                   ▼
        ┌─────────────────────────────────────────────────────────┐
        │  LAYER 2: Framework-Specific Schema Extensions          │
        ├─────────────────────────────────────────────────────────┤
        │ PostGraphile:              Ruby Rails:     Other:       │
        │ - Smart tags (@omit)       - Associations  - (future)   │
        │ - API documentation        - Validations                │
        │ - Query patterns           - Scopes                     │
        │ - Index optimization                                    │
        └─────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
        ┌────────────────────────┐    ┌───────────────────────────┐
        │ database/02-schema.sql │◄───┤ Shared Configuration      │
        └────────────────────────┘    │ (Trinity Pattern)         │
                │                     └───────────────────────────┘
                │
        ┌───────▼─────────────────────────────────────────────────┐
        │  LAYER 1: Shared Benchmark Schema (Trinity Pattern)     │
        ├──────────────────────────────────────────────────────────┤
        │ tb_user:     pk_user (INT) + id (UUID) + columns         │
        │ tb_post:     pk_post (INT) + id (UUID) + fk_user (INT)   │
        │ tb_comment:  pk_comment (INT) + id (UUID) + fk_* (INT)   │
        │                                                          │
        │ All frameworks share this schema unchanged              │
        │ No framework-specific code                             │
        └──────────────────────────────────────────────────────────┘
                │
                ▼
        ┌──────────────────────────┐
        │   PostgreSQL Database    │
        │   (velocitybench_test)   │
        └──────────────────────────┘
```

## Data Flow: From Database to API

### Example: PostGraphile User Query

**1. Database Layer** (Shared Schema):
```sql
SELECT pk_user, id, username, email, created_at, updated_at
FROM benchmark.tb_user
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

**2. PostGraphile Smart Tags** (Framework Extension):
```sql
COMMENT ON COLUMN tb_user.pk_user IS E'@omit all';
COMMENT ON COLUMN tb_user.created_at IS E'@omit create,update';
COMMENT ON COLUMN tb_user.updated_at IS E'@omit create,update';
```

**3. GraphQL Schema** (Generated by PostGraphile):
```graphql
type User {
  id: UUID!           # Exposed (public identifier)
  username: String!   # Exposed (public data)
  email: String!      # Exposed (public data)
  # pk_user NOT exposed (@omit all)
  # created_at NOT exposed in mutations (@omit create,update)
  # updated_at NOT exposed in mutations (@omit create,update)
}
```

**4. API Response** (What clients see):
```graphql
query {
  userById(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    username
    email
  }
}
```

## Benefits of This Architecture

### For Shared Schema
- ✅ Single source of truth
- ✅ All frameworks use identical data structure
- ✅ Performance-optimized (integer PKs/FKs)
- ✅ Framework-agnostic
- ✅ Easy to maintain and update

### For Framework Extensions
- ✅ Framework-specific optimizations isolated
- ✅ Easy to add new frameworks without modifying shared schema
- ✅ Framework teams can independently customize behavior
- ✅ Comments don't affect other frameworks
- ✅ Clear separation of concerns

### For API Security
- ✅ Internal implementation details hidden
- ✅ API surface clearly defined in schema
- ✅ Framework enforces visibility rules
- ✅ Clients can't bypass abstraction

### For Testing
- ✅ All frameworks test same schema
- ✅ Fair performance comparisons
- ✅ Consistent test data structure
- ✅ Easy to verify Trinity Pattern

## Adding New Framework

To add a new framework to VelocityBench:

1. **Create framework directory**:
   ```
   frameworks/my-framework/
   ├── database/
   │   └── schema.sql          # Framework-specific extensions
   ├── src/
   │   ├── db.ts               # Database connection + initialization
   │   ├── middleware.ts        # Framework setup
   │   └── index.ts             # Server startup
   └── tests/
       ├── test-factory.ts      # Test data creation
       └── *.test.ts            # Test suites
   ```

2. **Create `schema.sql`** with framework-specific smart tags:
   ```sql
   -- YOUR-FRAMEWORK specific comments and configurations
   COMMENT ON COLUMN tb_user.pk_user IS E'@your-tag value\nDescription.';
   ```

3. **Initialize schema in `db.ts`**:
   ```typescript
   export async function connectDatabase() {
     const client = await pool.connect();
     await applyFrameworkSchema(client);  // Apply framework-specific config
     client.release();
   }
   ```

4. **Use shared `TestFactory`** or create framework-specific variant

5. **Run benchmarks** - all frameworks use same data structure for fair comparison

## Trinity Pattern: Design Rationale

| Layer | Type | Reason |
|-------|------|--------|
| **Database** | `pk_*` SERIAL | Fastest for internal joins/indexes |
| **Database** | `fk_*` INTEGER | Fastest for foreign key constraints |
| **Database** | `id` UUID | Distributed systems, API stability |
| **API** | UUID identifiers | External contracts, stability |
| **API** | Relations | Framework-specific navigation |
| **API** | `pk_*`, `fk_*` hidden | Prevent client bypass of abstraction |

## Performance Implications

- **Integer PKs**: ~5-10x faster than UUIDs for joins
- **UUID API**: Distributed system compatibility, cache stability
- **Hidden `fk_*`**: Forces use of relations, prevents N+1 queries in GraphQL

## Framework Configuration Checklist

When implementing a new framework:

- [ ] Create `frameworks/{name}/database/schema.sql`
- [ ] Add framework-specific smart tags or metadata
- [ ] Implement `applyFrameworkSchema()` function
- [ ] Document Trinity Pattern usage in framework
- [ ] Create test factory for benchmark data
- [ ] Verify all tests pass with shared schema
- [ ] Benchmark against baseline metrics

---

## Related Documentation

- **API Security**: See `API_EXPOSURE_SECURITY.md`
- **PostGraphile Implementation**: See `frameworks/postgraphile/README.md`
- **Trinity Pattern Details**: See implementation in Ruby Rails framework
