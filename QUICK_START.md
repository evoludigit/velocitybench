# VelocityBench Multi-Database Architecture - Quick Start

## TL;DR

```bash
# Setup isolated databases for all frameworks
python database/setup.py

# Run tests sequentially
python scripts/run-benchmarks.py

# View results
cat benchmark-results.json
open benchmark-results.html
```

## What's New

✅ **schema-template.sql** - Universal Trinity Pattern schema (shared foundation)
✅ **database/setup.py** - Automated per-framework database setup
✅ **frameworks/{framework}/database/extensions.sql** - Framework-specific features
✅ **scripts/run-benchmarks.py** - Sequential test harness
✅ **POSTGRAPHILE_TEST_ARCHITECTURE.md** - Transaction isolation details
✅ **DATABASE_ARCHITECTURE.md** - Full architecture design
✅ **IMPLEMENTATION_GUIDE.md** - Detailed implementation guide

## Architecture in One Picture

```
Before: 1 Shared Database (polluted)
postgraphile_test
└── benchmark schema
    ├── tb_* (Trinity Pattern)
    ├── v_* views (FraiseQL)
    ├── tv_* views (FraiseQL)
    ├── Smart tags (PostGraphile)
    ├── Rails migrations
    ├── Triggers and functions (FraiseQL)
    └── Mix of 26 frameworks' features ❌

After: Per-Framework Databases (isolated)
postgraphile_test            fraiseql_test             rails_test
└── benchmark schema         └── benchmark schema      └── benchmark schema
    ├── tb_* only                ├── tb_*                  ├── tb_*
    └── Smart tags               ├── v_* views             └── AR config
                                 └── tv_* views
                                 
✅ Clean isolation ✅ No conflicts ✅ Fair benchmarks
```

## Core Concept: Trinity Pattern

Every table follows this structure:
```sql
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,   -- Internal, hidden
    id UUID UNIQUE,                -- Public API identifier  
    ... data ...
);
```

Why? Performance + API safety + Framework agnostic

## Quick Commands

### Setup
```bash
# All frameworks
python database/setup.py

# Specific frameworks
python database/setup.py postgraphile fraiseql
```

### Test
```bash
# All frameworks (sequential)
python scripts/run-benchmarks.py

# Specific frameworks
python scripts/run-benchmarks.py postgraphile fraiseql
```

### Debug
```bash
# Check a framework's database
psql postgresql://velocitybench:password@localhost/postgraphile_test

# List tables
\dt benchmark.*

# View a table
SELECT * FROM benchmark.tb_user LIMIT 5;

# Test FraiseQL views
SELECT * FROM benchmark.tv_user LIMIT 1;
```

## Files Structure

```
database/
├── schema-template.sql        ← Universal foundation (Trinity Pattern only)
└── setup.py                   ← Orchestration script

frameworks/
├── postgraphile/database/extensions.sql   ← Smart tags
├── fraiseql/database/extensions.sql       ← v_*/tv_* views
└── [24 more frameworks]/database/extensions.sql

scripts/
└── run-benchmarks.py          ← Sequential test runner

docs/
├── POSTGRAPHILE_TEST_ARCHITECTURE.md     ← Transaction isolation
├── DATABASE_ARCHITECTURE.md               ← Full design
├── IMPLEMENTATION_GUIDE.md                ← Detailed guide
└── QUICK_START.md (this file)
```

## Environment Variables

```bash
# Database setup
DB_HOST=localhost
DB_PORT=5432
DB_ADMIN_USER=postgres
DB_ADMIN_PASSWORD=postgres
DB_TEST_USER=velocitybench
DB_TEST_PASSWORD=password

# Test runner
BENCHMARK_TIMEOUT=300          # Seconds per framework
BENCHMARK_VERBOSE=false        # More output
```

## What Changed from Before

| Aspect | Before | After |
|--------|--------|-------|
| Databases | 1 shared (postgraphile_test) | 26 isolated ({framework}_test) |
| Schema | Mixed features | Trinity Pattern + extensions |
| Testing | Parallel (contended) | Sequential (fair) |
| Isolation | Table cleanup | Transaction rollback |
| Extensions | Hard to manage | Per-framework files |

## Next Steps

1. **Test the setup**
   ```bash
   python database/setup.py postgraphile
   psql postgresql://velocitybench:password@localhost/postgraphile_test
   \d benchmark.tb_user  # Check smart tags
   ```

2. **Run a test**
   ```bash
   python scripts/run-benchmarks.py postgraphile
   cat benchmark-results.json
   ```

3. **Add another framework**
   ```bash
   mkdir -p frameworks/fraiseql/database
   python database/setup.py fraiseql
   ```

## Resources

- **Full Architecture**: See `DATABASE_ARCHITECTURE.md`
- **Setup Details**: See `IMPLEMENTATION_GUIDE.md`  
- **Transaction Isolation**: See `POSTGRAPHILE_TEST_ARCHITECTURE.md`

## Troubleshooting

**Q: `psql: error: could not translate host name "localhost" to address`**
A: PostgreSQL not running. Start it: `brew services start postgresql` (macOS)

**Q: `permission denied` when running setup**
A: Check `DB_TEST_USER` and `DB_TEST_PASSWORD` environment variables

**Q: Tests timing out**
A: Increase timeout: `BENCHMARK_TIMEOUT=600 python scripts/run-benchmarks.py`

**Q: No test results**
A: Check framework has test runner (package.json, requirements.txt, etc.)

---

**Architecture Design Completed**: 2026-01-10
**Status**: Ready for implementation and testing
