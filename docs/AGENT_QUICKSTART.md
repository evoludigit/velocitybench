# Agent Quickstart Guide

## For AI Agents Getting Started with VelocityBench

This guide will help you get productive quickly. Start here, then reference detailed docs as needed.

---

## 60-Second Overview

**VelocityBench**: Benchmarking suite for 35+ frameworks across 10+ languages

**Key Facts**:
- ✅ All frameworks use same **Trinity Pattern database schema**
- ✅ All implement **same REST and GraphQL APIs**
- ✅ Benchmarked against each other in **CI/CD**
- ✅ All tests use **shared fixtures** (`db`, `factory`)
- ✅ **100% cross-framework consistency**

**Structure**:
```
frameworks/          # 35+ implementations (FastAPI, Strawberry, Express, Go, etc.)
database/            # PostgreSQL schema and seed data
tests/               # Shared fixtures + cross-framework QA tests
docs/                # This documentation
```

---

## Essential Concepts

### 1. Trinity Pattern (Database IDs)

```python
# Every entity has THREE identifiers:
user = {
    "pk_user": 1,                          # ← Use for foreign keys (SERIAL int)
    "id": "550e8400-e29b-41d4-a716-...",  # ← Use for public API (UUID)
    "username": "alice"                    # ← Use for humans/URLs (unique string)
}

# When creating related entity:
post = {
    "fk_author": 1  # ← Use pk_user here! NOT id!
}
```

**Golden Rule**: **Use `pk_*` for FKs, `id` for API queries**

### 2. Shared Test Fixtures

```python
# All tests use these fixtures from tests/common/
def test_something(db, factory):
    """Every test gets these fixtures automatically."""
    user = factory.create_user("alice", "alice@example.com")
    # Data auto-cleaned after test (transaction rollback)
```

**Three fixtures**:
- `db` - Database connection with transaction isolation
- `factory` - Single entity creator
- `bulk_factory` - Bulk entity creator

### 3. REST vs GraphQL APIs

**Both implement same operations on same data**:

```python
# REST: /users/{id}
GET /users/550e8400-e29b-41d4-a716-...
→ {"id": "...", "username": "alice", ...}

# GraphQL: query
query { user(id: "550e8400...") { id username } }
→ {"data": {"user": {"id": "...", "username": "alice"}}}
```

**Framework field naming**:
- REST: snake_case (`first_name`, `author_id`)
- GraphQL: camelCase (`firstName`, `authorId`)
- Frameworks handle conversion automatically

---

## First Task: Understanding the Code

### Task 1: Find Where Users Are Created

**Where to look**:
1. **In one framework**: `frameworks/fastapi-rest/main.py` (REST endpoint)
2. **Or GraphQL**: `frameworks/strawberry/main.py` (GraphQL mutation)
3. **Shared**: `frameworks/common/async_db.py` (database connection)
4. **Testing**: `tests/common/factory.py` (test data creation)

**Command**:
```bash
grep -r "def create_user" frameworks/
# Shows create_user in every framework
```

### Task 2: Understand Test Infrastructure

**Key files**:
```
tests/common/
├── conftest.py       # Pytest configuration (loads fixtures)
├── fixtures.py       # db, factory, bulk_factory fixtures
├── factory.py        # TestFactory class implementation
└── bulk_factory.py   # BulkFactory class implementation
```

**Quick read**:
```bash
# Understand fixture injection
cat tests/common/conftest.py | head -50

# See factory methods available
grep "def create_" tests/common/factory.py
```

### Task 3: See How Database Works

**Location**: `database/schema-template.sql`

**Key tables**:
- `tb_user` - Users (pk_user, id, username, email, etc.)
- `tb_post` - Posts (pk_post, id, fk_author, title, content, etc.)
- `tb_comment` - Comments (pk_comment, id, fk_post, fk_author, content, etc.)

**Quick understanding**:
```bash
# See schema
head -100 database/schema-template.sql

# Understand relations
grep "REFERENCES" database/schema-template.sql
```

---

## Common Tasks Quick Reference

### Task: Query Users from Database

```python
from frameworks.common.async_db import AsyncDatabase

async def get_users(db):
    rows = await db.fetch_all(
        "SELECT pk_user, id, username, email FROM tb_user LIMIT 10"
    )
    return rows
```

**See also**: `docs/QUERY_PATTERNS.md` - Full query pattern library

---

### Task: Add REST Endpoint to FastAPI

```python
# Location: frameworks/fastapi-rest/main.py

from fastapi import FastAPI

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    """Get post by UUID."""
    row = await db.fetch_one(
        "SELECT * FROM tb_post WHERE id = $1",
        post_id
    )
    return row
```

**See also**: `docs/MODIFICATION_GUIDE.md` - Step-by-step endpoint guide

---

### Task: Create Test for New Feature

```python
# Location: tests/qa/test_features.py

def test_post_creation_succeeds(db, factory):
    """User can create a post."""
    author = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(
        fk_author=author['pk_user'],
        title="My Post"
    )
    assert post['title'] == "My Post"
    assert post['fk_author'] == author['pk_user']
```

**See also**: `docs/TESTING_README.md` - Full testing guide

---

### Task: Debug a Failing Test

```bash
# Run with verbose output
pytest tests/qa/test_features.py::test_name -vv

# Run with print statements visible
pytest tests/qa/test_features.py::test_name -s

# Run with debugger on failure
pytest tests/qa/test_features.py::test_name --pdb

# Run single test (isolation)
pytest tests/qa/test_features.py::test_name -v
```

**Common issues**: See `docs/ERROR_CATALOG.md` - Error solutions

---

### Task: Check Database State

```bash
# Connect to running PostgreSQL
docker exec postgres psql -U benchmark -d velocitybench_test

# Common queries
SELECT * FROM tb_user LIMIT 5;
SELECT * FROM tb_post WHERE status = 'published';
SELECT COUNT(*) FROM tb_comment;
```

---

### Task: Run Tests Across All Frameworks

```bash
# Cross-framework QA tests
cd tests/qa
pytest test_*.py -v

# Python frameworks only
cd frameworks/fastapi-rest && pytest tests/
cd frameworks/strawberry && pytest tests/

# Single test across frameworks
pytest tests/qa/test_users.py::test_user_creation -v
```

---

## Navigation Guide

### When You Need To...

| Need | File(s) | Command |
|------|---------|---------|
| Understand database structure | `docs/DATABASE_SCHEMA.md` | `cat docs/DATABASE_SCHEMA.md \| head -200` |
| See API operations | `docs/API_SCHEMAS.md` | Search for endpoint/query |
| Find code in codebase | `docs/CODEBASE_NAVIGATION.md` | See file/module map |
| Write/modify code | `docs/MODIFICATION_GUIDE.md` | Follow step-by-step |
| Use efficient queries | `docs/QUERY_PATTERNS.md` | Copy/adapt pattern |
| Debug error | `docs/ERROR_CATALOG.md` | Search error message |
| Run tests | `docs/TESTING_README.md` | See test commands |
| Add test data | `docs/FIXTURE_FACTORY_GUIDE.md` | See factory methods |

---

## The 5-Minute Productivity Path

### Minute 1: Clone and Setup
```bash
git clone https://github.com/evoludigit/velocitybench.git
cd velocitybench
docker-compose up -d postgres  # Start database
```

### Minute 2: Run First Test
```bash
cd frameworks/fastapi-rest
pytest tests/test_users.py -v
```

### Minute 3: Understand Structure
```bash
# Quick tour
ls -la
cat Makefile | head -20
grep -r "def test_" tests/ | head -5
```

### Minute 4: Read One Doc
```bash
# Start with this file
cat docs/CODEBASE_NAVIGATION.md | head -100
```

### Minute 5: Try a Query
```bash
# Start Python REPL in framework
python

from frameworks.common.async_db import AsyncDatabase
db = AsyncDatabase()
# (would need full setup, but shows the concept)
```

---

## Key Files to Bookmark

```
docs/
  CODEBASE_NAVIGATION.md        # START HERE - overview + navigation
  DATABASE_SCHEMA.md             # Database structure reference
  API_SCHEMAS.md                 # REST/GraphQL API specs
  QUERY_PATTERNS.md              # Common SQL queries
  MODIFICATION_GUIDE.md          # How to modify code
  ERROR_CATALOG.md               # Error solutions
  TESTING_README.md              # Test infrastructure
  FIXTURE_FACTORY_GUIDE.md       # Test data creation

frameworks/
  common/                        # Python shared code
    async_db.py                  # Database connection pool
    config.py                    # Configuration management
    health_check.py              # Health endpoint

tests/
  common/
    conftest.py                  # Pytest configuration
    fixtures.py                  # db, factory fixtures
    factory.py                   # TestFactory class

database/
  schema-template.sql            # Core database schema
```

---

## Debugging Checklist

**Test fails?** → `docs/ERROR_CATALOG.md`
**Don't know how to query?** → `docs/QUERY_PATTERNS.md`
**Need to add feature?** → `docs/MODIFICATION_GUIDE.md`
**Lost in codebase?** → `docs/CODEBASE_NAVIGATION.md`
**Need test example?** → `docs/TESTING_README.md` or `docs/FIXTURE_FACTORY_GUIDE.md`

---

## Common Patterns to Remember

### Pattern 1: Use pk_* for Foreign Keys
```python
# ✅ CORRECT
db.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
          user['pk_user'],  # Use pk_user!
          "Title")

# ❌ WRONG
db.execute("INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
          user['id'],       # Don't use UUID!
          "Title")
```

### Pattern 2: Use Fixtures for Tests
```python
# ✅ CORRECT - Automatic transaction isolation
def test_create_user(db, factory):
    user = factory.create_user("alice", "alice@example.com")
    assert user is not None

# ❌ WRONG - Manual connection, no isolation
import psycopg
conn = psycopg.connect(...)
```

### Pattern 3: Join for Related Data
```python
# ✅ FAST - Single query
rows = db.fetch_all("""
    SELECT p.*, u.username FROM tb_post p
    JOIN tb_user u ON p.fk_author = u.pk_user
""")

# ❌ SLOW - N+1 queries
posts = db.fetch_all("SELECT * FROM tb_post")
for post in posts:
    author = db.fetch_one("SELECT * FROM tb_user WHERE pk_user = %s",
                         post['fk_author'])  # Repeated!
```

---

## What's Next?

### After Mastering This Guide:

1. **Read CODEBASE_NAVIGATION.md** (10 min) - Understand structure
2. **Pick a Task** - Try adding an endpoint or test
3. **Follow MODIFICATION_GUIDE.md** (15 min) - Step-by-step instructions
4. **Reference as Needed** - Use ERROR_CATALOG when stuck

### Recommended Learning Path:

**Level 1** (Today):
- [ ] Read this quickstart
- [ ] Read CODEBASE_NAVIGATION.md
- [ ] Run one test successfully

**Level 2** (Next Session):
- [ ] Write a simple test
- [ ] Query database manually
- [ ] Read one query pattern

**Level 3** (Advanced):
- [ ] Add an endpoint (REST or GraphQL)
- [ ] Optimize a query
- [ ] Add database field

---

## Getting Help

**Error occurred?** → Search `docs/ERROR_CATALOG.md`
**Can't find code?** → Check `docs/CODEBASE_NAVIGATION.md`
**Need pattern?** → Look in `docs/QUERY_PATTERNS.md` or `docs/MODIFICATION_GUIDE.md`
**Test questions?** → Read `docs/TESTING_README.md`

**All documentation is cross-referenced** - follow links to related docs

---

## Pro Tips

1. **Bookmark these 3 files**:
   - `docs/CODEBASE_NAVIGATION.md` - Quick reference
   - `docs/ERROR_CATALOG.md` - Debugging
   - `docs/QUERY_PATTERNS.md` - Copy/paste queries

2. **Use grep to find code**:
   ```bash
   grep -r "def create_user" frameworks/
   grep -r "fk_author" database/
   grep -r "published_at" --include="*.sql"
   ```

3. **Test locally before pushing**:
   ```bash
   pytest tests/qa/test_*.py -v
   ```

4. **Check error catalog first** when stuck - likely solved already

---

## Ready?

**Next step**: Open `docs/CODEBASE_NAVIGATION.md` and follow along.

**Questions?** All answers are in one of these 8 documentation files.

**Happy coding!** 🚀

