# API Exposure Security: Trinity Pattern Implementation for PostGraphile

## Problem Statement

The Trinity Pattern separates database concerns into three layers:
- **Internal Integer PKs** (`pk_*`): Used for fast database operations (indexes, joins)
- **Public UUID IDs** (`id`): Exposed through GraphQL API for distributed systems
- **Internal Integer FKs** (`fk_*`): Used for fast foreign key relationships

**Critical Issue**: By default, PostGraphile exposes **ALL database columns** in the GraphQL schema, including the internal `pk_*` and `fk_*` integer columns. This breaks the Trinity Pattern abstraction because clients could:
1. Discover and directly use internal integer identifiers
2. Bypass the UUID abstraction
3. Potentially interfere with internal database optimizations

## Solution: PostgreSQL Smart Tags

PostGraphile respects PostgreSQL smart tag comments to control column visibility in the GraphQL schema.

### Implementation

Add `@omit` smart tag comments to hide internal columns:

```sql
-- Hide internal primary key (never exposed)
COMMENT ON COLUMN tb_user.pk_user IS E'@omit all\nInternal primary key for performance.';

-- Hide internal foreign keys (never exposed to clients)
COMMENT ON COLUMN tb_post.fk_user IS E'@omit all\nInternal foreign key (use author relation instead).';

-- Hide timestamps from mutations (read-only, server-managed)
COMMENT ON COLUMN tb_user.created_at IS E'@omit create,update\nTimestamp when user was created.';
COMMENT ON COLUMN tb_user.updated_at IS E'@omit create,update\nTimestamp when user was last updated.';
```

### Applied to All Tables

**tb_user:**
- Hidden: `pk_user` (internal PK)
- Hidden from mutations: `created_at`, `updated_at` (read-only)
- Exposed: `id` (UUID), `username`, `email`, `first_name`, `last_name`, `bio`, `avatar_url`, `is_active`

**tb_post:**
- Hidden: `pk_post` (internal PK), `fk_user` (internal FK)
- Hidden from mutations: `created_at`, `updated_at` (read-only)
- Exposed: `id` (UUID), `title`, `content`, `excerpt`, `status`, `published_at`
- Relations: `author` (to User via hidden `fk_user`)

**tb_comment:**
- Hidden: `pk_comment` (internal PK), `fk_post`, `fk_user`, `fk_parent` (internal FKs)
- Hidden from mutations: `created_at`, `updated_at` (read-only)
- Exposed: `id` (UUID), `content`, `is_approved`
- Relations: `post`, `author`, `parentComment` (via hidden FKs)

## Enforcement: How Clients Can Use the API

✅ **Correct Usage** (UUID identifiers):
```graphql
query {
  userById(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    username
    email
  }
}
```

❌ **Prevented** (Integer identifiers):
```graphql
# These will fail - pk_user and fk_* are hidden from GraphQL schema
query {
  userById(id: 123) { # Integer, not UUID
    pkUser # Field doesn't exist in GraphQL
    id
  }
}
```

## Verification

When the GraphQL schema is introspected, the `__type` query will show:
- User type has: `id`, `username`, `email`, `firstName`, `lastName`, `bio`, `avatarUrl`, `isActive`
- User type does NOT have: `pkUser`, `created_at`, `updated_at`

This is enforced at the GraphQL schema level, not at runtime - clients cannot even request these fields.

## PostGraphile Configuration

The smart tags are applied via SQL comments in `database/02-schema.sql`. PostGraphile automatically:
1. Parses the `@omit` tags from column comments
2. Excludes these columns from the generated GraphQL schema
3. Removes them from query types, mutation input types, and filter types

No additional configuration is needed in `src/middleware.ts` - the smart tags are the primary mechanism PostGraphile uses for schema customization.

## Best Practices

1. **Always use UUIDs for external APIs**: Never expose integer PKs to clients
2. **Hide server-managed fields**: Mark `created_at`, `updated_at`, and similar as `@omit create,update`
3. **Use FK relations, not FK columns**: Clients should use GraphQL relations (e.g., `post { author { id } }`) rather than integer FK values
4. **Document the Trinity Pattern**: Ensure new tables follow the `pk_*` + `id` + `fk_*` pattern consistently

## References

- [PostGraphile Smart Tags Documentation](https://www.graphile.org/postgraphile/smart-tags/)
- [PostGraphile PostgreSQL Schema Design](https://www.graphile.org/postgraphile/postgresql-schema-design/)
- VelocityBench Trinity Pattern Implementation
