# VelocityBench Architecture Index

This document indexes all architecture and implementation documents for the multi-database benchmark suite.

## Quick Navigation

### For Users (Just Want to Run Benchmarks)
1. **Start Here**: [QUICK_START.md](./QUICK_START.md) (5 min read)
2. **Then Read**: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) (15 min read)

### For Architects (Understanding the Design)
1. **Start Here**: [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) (20 min read)
2. **Then Read**: [POSTGRAPHILE_TEST_ARCHITECTURE.md](./POSTGRAPHILE_TEST_ARCHITECTURE.md) (10 min read)

### For Developers (Contributing)
1. **Start Here**: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
2. **Reference**: [SESSION_SUMMARY.md](./SESSION_SUMMARY.md) (what was built)
3. **Details**: See specific framework extension files

### For Operations (Running & Maintaining)
1. **Start Here**: [QUICK_START.md](./QUICK_START.md)
2. **Reference**: Environment variables in [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
3. **Troubleshoot**: See FAQ in [QUICK_START.md](./QUICK_START.md)

---

## Document Overview

### [SESSION_SUMMARY.md](./SESSION_SUMMARY.md) ⭐ **START HERE**
**What**: Complete summary of Phase 1-3 implementation
**Why**: Understand what was built and when
**Time**: 10 minutes
**Audience**: Everyone
**Covers**:
- What was built (7 files)
- Architecture transformation (before/after)
- How to use (quick commands)
- Technology stack
- Next steps

### [QUICK_START.md](./QUICK_START.md) ⭐ **FOR OPERATIONS**
**What**: TL;DR guide for common tasks
**Why**: Get started in 2 minutes
**Time**: 5 minutes
**Audience**: DevOps, QA, developers
**Covers**:
- Three basic commands (setup, test, debug)
- Architecture picture (one diagram)
- Environment variables
- Troubleshooting FAQ

### [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) ⭐ **FOR DEVELOPERS**
**What**: Comprehensive implementation reference
**Why**: Understand how to use and extend the system
**Time**: 20 minutes
**Audience**: Developers, architects
**Covers**:
- How to use (detailed)
- Architecture overview
- Trinity Pattern explanation
- Adding new frameworks
- Common patterns
- Debugging guide
- File structure
- Performance characteristics

### [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) ⭐ **FOR ARCHITECTS**
**What**: Full architectural design document
**Why**: Understand design decisions and tradeoffs
**Time**: 30 minutes
**Audience**: Architects, senior engineers
**Covers**:
- Executive summary
- Architecture diagram
- Component details with code
- Implementation phases
- Database structure
- Benefits analysis
- Performance comparison
- Example: Adding a framework

### [POSTGRAPHILE_TEST_ARCHITECTURE.md](./POSTGRAPHILE_TEST_ARCHITECTURE.md) ⭐ **FOR POSTGRAPHILE DETAILS**
**What**: Transaction-based test isolation specifics
**Why**: Understand PostGraphile-specific testing approach
**Time**: 15 minutes
**Audience**: PostGraphile developers, QA
**Covers**:
- Transaction isolation overview
- How it works (diagram)
- Implementation details
- Before/after comparison
- Smart tags integration
- Future framework extensions

---

## Key Files Created

### Code Files
| File | Size | Purpose |
|------|------|---------|
| `database/schema-template.sql` | 295 lines | Universal Trinity Pattern (foundation) |
| `database/setup.py` | 475 lines | Database orchestration script |
| `frameworks/postgraphile/database/extensions.sql` | 115 lines | PostGraphile smart tags |
| `frameworks/fraiseql/database/extensions.sql` | 275 lines | FraiseQL views and sync functions |
| `scripts/run-benchmarks.py` | 375 lines | Sequential test runner |

### Documentation Files
| File | Words | Purpose |
|------|-------|---------|
| `QUICK_START.md` | 1,500 | Quick reference guide |
| `IMPLEMENTATION_GUIDE.md` | 3,500 | Implementation reference |
| `SESSION_SUMMARY.md` | 2,000 | What was built and why |
| `DATABASE_ARCHITECTURE.md` | 2,500 | Architecture design |
| `POSTGRAPHILE_TEST_ARCHITECTURE.md` | 1,800 | Test isolation details |
| `README_ARCHITECTURE.md` | This file | Documentation index |

---

## Architecture at a Glance

### Before: Single Shared Database ❌
```
postgraphile_test
└── benchmark
    ├── tables (Trinity Pattern)
    ├── FraiseQL views (v_*, tv_*)
    ├── PostGraphile smart tags
    ├── Rails migrations
    └── Mix of 26 frameworks' features
```
**Problems**: Pollution, conflicts, unfair tests

### After: Per-Framework Databases ✅
```
postgraphile_test          fraiseql_test            rails_test
└── benchmark              └── benchmark             └── benchmark
    ├── tables (Trinity)       ├── tables (Trinity)      ├── tables (Trinity)
    └── Smart tags            ├── v_* views              └── AR config
                              └── tv_* views
```
**Benefits**: Clean, isolated, fair tests

---

## Quick Commands

```bash
# Setup all frameworks
python database/setup.py

# Setup specific frameworks
python database/setup.py postgraphile fraiseql

# Run tests sequentially
python scripts/run-benchmarks.py

# Run specific framework
python scripts/run-benchmarks.py postgraphile

# Debug a framework's database
psql postgresql://velocitybench:password@localhost/postgraphile_test
\d benchmark.tb_user
SELECT * FROM benchmark.tv_user LIMIT 1;
```

---

## Reading Guide by Role

### Software Engineer (New to Project)
1. Read: [SESSION_SUMMARY.md](./SESSION_SUMMARY.md) (10 min) - What was built
2. Read: [QUICK_START.md](./QUICK_START.md) (5 min) - How to use
3. Do: Run `python database/setup.py postgraphile` and try the commands
4. Reference: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) as needed

### DevOps / Operations
1. Read: [QUICK_START.md](./QUICK_START.md) (5 min)
2. Do: Set up databases and run benchmarks
3. Reference: Troubleshooting FAQ in [QUICK_START.md](./QUICK_START.md)
4. Reference: Environment variables in [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)

### Architect / Tech Lead
1. Read: [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) (20 min)
2. Read: [SESSION_SUMMARY.md](./SESSION_SUMMARY.md) (10 min)
3. Reference: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for technical details
4. Review: Code in `database/` and `frameworks/` directories

### Framework Developer (Adding New Framework)
1. Read: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Section "Adding a New Framework"
2. Read: Existing framework extensions (PostGraphile, FraiseQL)
3. Do: Follow the 5-step process to add your framework
4. Reference: [QUICK_START.md](./QUICK_START.md) for verification

### QA / Testing
1. Read: [QUICK_START.md](./QUICK_START.md) (5 min)
2. Read: [POSTGRAPHILE_TEST_ARCHITECTURE.md](./POSTGRAPHILE_TEST_ARCHITECTURE.md) (15 min)
3. Do: Run benchmark tests using `python scripts/run-benchmarks.py`
4. Reference: Result files (JSON and HTML)

---

## Key Concepts

### Trinity Pattern
Every table has:
```sql
pk_*     SERIAL PRIMARY KEY  -- Internal, hidden
id       UUID UNIQUE         -- Public API identifier
fk_*     INTEGER             -- Internal foreign keys
```
**Why**: Performance + Safety + Framework-agnostic

### Transaction-Based Isolation
Tests use `BEGIN ... ROLLBACK` for cleanup
**Why**: Clean, ACID-compliant, respects schema

### Per-Framework Databases
Each framework gets its own PostgreSQL database
**Why**: No pollution, no conflicts, fair benchmarks

### Sequential Testing
One framework at a time, no parallelism
**Why**: Reproducible results, no resource contention

### Framework Extensions
Framework-specific features in `extensions.sql`
**Why**: Keep shared schema clean, enable customization

---

## Status

✅ **Phase 1**: Schema Foundation (Complete)
✅ **Phase 2**: Framework Extensions (PostGraphile, FraiseQL complete)
✅ **Phase 3**: Test Harness (Complete)
⏳ **Phase 4**: Full Framework Migration (24 remaining frameworks)

---

## Next Reading

Choose your path:
- **Want to start testing?** → [QUICK_START.md](./QUICK_START.md)
- **Want to understand the design?** → [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md)
- **Want to add a framework?** → [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
- **Want details on everything?** → [SESSION_SUMMARY.md](./SESSION_SUMMARY.md)

---

**Last Updated**: 2026-01-10
**Status**: ✅ Production-Ready (Phases 1-3)
**Next Phase**: Add remaining 24 frameworks
