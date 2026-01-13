# PostGraphile Test Architecture - Transaction-Based Isolation

**Date**: 2026-01-10
**Approach**: Database transaction-based test isolation
**Status**: ✅ Production-Ready Pattern

## Overview

PostGraphile tests now use **transaction-based isolation** instead of manual table cleanup. This approach:

1. **Respects PostGraphile's Schema Design** - Leverages PostGraphile's native schema configuration (smart tags)
2. **Automatic Cleanup** - Database transactions handle cleanup automatically via rollback
3. **Better Isolation** - ACID-compliant transaction boundaries
4. **No Schema Pollution** - PostGraphile's smart tags and configuration remain pristine
5. **Follows PostgreSQL Best Practices** - Uses standard transaction isolation levels

## Architecture

### How It Works

```
┌─────────────────────────────────────────┐
│ PostGraphile Application (db.ts)        │
│ - Smart tags apply on server startup    │
│ - Schema configuration remains static   │
│ - No manual cleanup needed              │
└─────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────┐
│ Test Suite (mutations.test.ts)          │
│                                         │
│ beforeEach:                             │
│   ├─ factory.startTransaction()         │
│   └─ BEGIN; (READ COMMITTED isolation) │
│                                         │
│ Test: Create, Query, Assert             │
│                                         │
│ afterEach:                              │
│   ├─ factory.cleanup()                  │
│   └─ ROLLBACK; (all data disappears)    │
└─────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────┐
│ Database Schema (benchmark schema)      │
│ - tb_user, tb_post, tb_comment tables   │
│ - v_* and tv_* views (if FraiseQL)      │
│ - Smart tags (if PostGraphile)          │
│ - No temporary truncation needed        │
└─────────────────────────────────────────┘
```

## Implementation Details

### TestFactory Changes

**Before**: Manual cleanup via `TRUNCATE TABLE` commands
```typescript
async cleanup() {
  const client = await this.pool.connect();
  try {
    await client.query('TRUNCATE TABLE benchmark.tb_comment CASCADE');
    await client.query('TRUNCATE TABLE benchmark.tb_post CASCADE');
    await client.query('TRUNCATE TABLE benchmark.tb_user CASCADE');
  } finally {
    client.release();
  }
}
```

**After**: Transaction-based cleanup
```typescript
async startTransaction() {
  this.testClient = await this.pool.connect();
  await this.testClient.query('BEGIN ISOLATION LEVEL READ COMMITTED');
}

async cleanup() {
  await this.rollbackTransaction(); // Automatic cleanup!
}
```

### Test Usage

```typescript
describe('PostGraphile Tests', () => {
  let factory: TestFactory;

  beforeEach(async () => {
    await factory.startTransaction();  // Start test transaction
  });

  afterEach(async () => {
    await factory.cleanup();  // Auto-cleanup via rollback
  });

  test('creates and queries user', async () => {
    const user = await factory.createUser({ username: 'test' });

    const response = await request(server)
      .post('/graphql')
      .send({ query: `{ userById(id: "${user.id}") { username } }` });

    expect(response.body.data.userById.username).toBe('test');
    // Test ends → afterEach → ROLLBACK → user data disappears
  });
});
```

## Why This Approach is Better

### 1. **Respects PostGraphile Architecture**
PostGraphile applies smart tags to the database schema during startup:
```sql
COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\nInternal FK';
```

Manual truncation bypasses this - transactions don't.

### 2. **Zero Schema Pollution**
- No temporary views or functions
- No sync triggers for temporary tables
- Schema stays exactly as designed

### 3. **Automatic Isolation**
- PostgreSQL handles transaction rollback atomically
- No cleanup code needed
- Guaranteed isolation between tests

### 4. **Compatible with All Frameworks**
Works with:
- ✅ PostGraphile (this pattern)
- ✅ FraiseQL (views work in transactions)
- ✅ Other frameworks using the same schema

## Performance Characteristics

| Aspect | Benefit |
|--------|---------|
| **Setup Time** | One transaction per test (fast) |
| **Cleanup Time** | ROLLBACK only (very fast) |
| **Isolation Cost** | Minimal (READ COMMITTED level) |
| **Memory** | Test data freed on rollback |
| **Concurrency** | Better than truncation (non-blocking) |

## Comparison: Before vs After

### Before (Manual Truncation)
```
Test: ✅
├─ CREATE user
├─ Query GraphQL
├─ Assert
└─ TRUNCATE TABLE (can lock other tests!)
   ├─ Check foreign keys
   ├─ Cascade delete related rows
   └─ Reset sequences

Issues:
❌ Truncation can wait for other locks
❌ Schema metadata might be affected
❌ Slow with large datasets
```

### After (Transaction Rollback)
```
Test: ✅
├─ BEGIN TRANSACTION
├─ CREATE user
├─ Query GraphQL
├─ Assert
└─ ROLLBACK (instant!)
   └─ All changes undo atomically

Benefits:
✅ Instant cleanup
✅ No locks
✅ ACID-compliant
✅ Works with schema views
```

## Database Compatibility

**Isolation Level**: `READ COMMITTED` (default PostgreSQL)

Works with:
- PostgreSQL 12+ ✅
- PostgreSQL 13+ ✅
- PostgreSQL 14+ ✅
- PostgreSQL 15+ ✅

## Related Files

- **Test Factory**: `frameworks/postgraphile/tests/test-factory.ts`
- **Test Suite**: `frameworks/postgraphile/tests/mutations.test.ts`
- **Schema Config**: `frameworks/postgraphile/src/db.ts`
- **Shared Schema**: `database/02-schema.sql`

## Integration with PostGraphile Smart Tags

PostGraphile smart tags are applied by `db.ts:applyPostGraphileSchema()`:

```typescript
const smartTags = `
  COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\n...';
  COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\n...';
`;
```

These tags are:
- Applied during server startup ✅
- Persistent in database metadata ✅
- Unaffected by transaction rollbacks ✅
- Visible to all tests automatically ✅

## Future Framework Extensions

This transaction-based approach is the recommended pattern for all 26 frameworks:

1. Each framework gets its own test file (or suite)
2. Each test suite uses `startTransaction()` in `beforeEach`
3. Each test suite uses `rollbackTransaction()` in `afterEach`
4. All share the same `TestFactory` base class
5. Framework-specific schema config (smart tags, views, etc.) stays pristine

## Summary

Transaction-based test isolation is:
- ✅ **Cleaner** - No manual cleanup code
- ✅ **Faster** - Instant rollback
- ✅ **Safer** - ACID-compliant isolation
- ✅ **Simpler** - Less test infrastructure
- ✅ **Better** - Aligns with database best practices
- ✅ **Framework-agnostic** - Works for all 26 frameworks

This is the production-ready pattern for VelocityBench's test suite.
