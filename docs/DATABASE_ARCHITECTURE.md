# VelocityBench Multi-Framework Database Architecture

**Date**: 2026-01-10
**Design**: Per-Framework PostgreSQL Databases with Shared Schema Template
**Testing**: Sequential (resource-efficient, clean benchmark results)
**Status**: Architecture Design Document

---

## Executive Summary

VelocityBench will use a **multi-database architecture** where each of the 26 frameworks gets its own isolated PostgreSQL database. This eliminates:
- ❌ Schema pollution from framework-specific features
- ❌ Interference between framework configurations
- ❌ Test isolation issues from shared state
- ❌ Parallel resource contention that skews benchmarks

Instead providing:
- ✅ True framework isolation
- ✅ Production-like testing environment
- ✅ Clean benchmark results (sequential execution)
- ✅ Framework-specific optimizations visible in schema
- ✅ Easy debugging (inspect each framework's database)

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   VELOCITYBENCH HARNESS                    │
│  (Orchestrates sequential framework testing)               │
└────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
        ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
        │   Schema    │ │Schema Setup │ │ Test Runner  │
        │  Template   │ │  Scripts    │ │  Harness     │
        │  (SQLite)   │ │  (Python)   │ │ (Node.js)    │
        └─────────────┘ └─────────────┘ └──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │PostgreSQL│  │PostgreSQL│  │PostgreSQL│
         │Database: │  │Database: │  │Database: │
         │postgraphile_test
         │          │  │ fraiseql_test
         │          │  │ rails_test  │
         │          │  │          │  │          │
         │benchmark │  │benchmark │  │benchmark │
         │schema +  │  │schema +  │  │schema +  │
         │smart tags│  │v_*/tv_*  │  │AR config │
         │          │  │views     │  │          │
         └──────────┘  └──────────┘  └──────────┘
              │              │              │
              ▼              ▼              ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │PostGraphile
         │ Tests    │  │ FraiseQL │  │  Rails   │
         │(Node.js) │  │ Tests    │  │  Tests   │
         │          │  │(Python)  │  │ (Ruby)   │
         └──────────┘  └──────────┘  └──────────┘
              │              │              │
              └──────────────┴──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌──────────────┐          ┌──────────────┐
        │ Benchmark    │          │ Performance  │
        │ Results (JSON)           │ Report       │
        └──────────────┘          └──────────────┘
```

---

## Component Details

### 1. Schema Template (SQLite)

**File**: `database/schema-template.sql`

Contains:
- Trinity Pattern table definitions (`tb_user`, `tb_post`, `tb_comment`)
- Column definitions (pk_*, id, fk_* pattern)
- Constraints (UNIQUE, FK, CHECK)
- Indexes (for performance)
- **No** framework-specific features:
  - No smart tags
  - No views (v_*, tv_*)
  - No triggers
  - No functions

```sql
-- Trinity Pattern: Universal across all frameworks
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    excerpt VARCHAR(500),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE tb_comment (
    pk_comment SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    fk_post INTEGER NOT NULL REFERENCES tb_post(pk_post) ON DELETE CASCADE,
    fk_author INTEGER NOT NULL REFERENCES tb_user(pk_user) ON DELETE CASCADE,
    fk_parent INTEGER REFERENCES tb_comment(pk_comment) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Schema Setup Scripts (Python)

**File**: `database/setup.py`

Orchestrates per-framework database setup:

```python
#!/usr/bin/env python3
"""
Setup per-framework PostgreSQL databases.
Each framework gets:
1. Fresh PostgreSQL database
2. Shared Trinity Pattern schema
3. Framework-specific extensions (views, smart tags, functions)
4. Seed data
"""

import subprocess
import os
from typing import List

FRAMEWORKS = [
    'postgraphile',
    'fraiseql',
    'rails',
    # ... 23 more frameworks
]

class DatabaseSetup:
    def __init__(self, postgres_host: str = 'localhost'):
        self.postgres_host = postgres_host
        self.postgres_port = 5432
        self.postgres_user = os.getenv('DB_USER', 'postgres')
        self.postgres_password = os.getenv('DB_PASSWORD', 'password')

    def create_framework_database(self, framework: str):
        """
        Create isolated database for a framework:
        1. Drop existing database (if present)
        2. Create fresh database
        3. Apply shared schema (Trinity Pattern)
        4. Apply framework-specific extensions
        5. Seed test data
        """
        db_name = f'{framework}_test'

        print(f"\n{'='*60}")
        print(f"Setting up: {framework}")
        print(f"{'='*60}")

        # 1. Drop existing
        self._run_sql(f'DROP DATABASE IF EXISTS {db_name}')

        # 2. Create fresh database
        self._run_sql(f'CREATE DATABASE {db_name}')

        # 3. Apply shared schema
        self._apply_file(db_name, 'database/schema-template.sql')

        # 4. Apply framework-specific extensions
        extensions_file = f'frameworks/{framework}/database/extensions.sql'
        if os.path.exists(extensions_file):
            self._apply_file(db_name, extensions_file)
        else:
            print(f"  ℹ️  No framework-specific extensions for {framework}")

        # 5. Seed test data
        self._apply_file(db_name, 'database/seed-data.sql')

        print(f"✅ {framework} database ready")

    def setup_all(self):
        """Setup all framework databases sequentially"""
        for framework in FRAMEWORKS:
            self.create_framework_database(framework)

        print(f"\n✅ All {len(FRAMEWORKS)} databases configured!")

    def _run_sql(self, sql: str):
        """Execute SQL command"""
        # Implementation
        pass

    def _apply_file(self, db_name: str, file_path: str):
        """Apply SQL file to database"""
        # Implementation
        pass

if __name__ == '__main__':
    setup = DatabaseSetup()
    setup.setup_all()
```

### 3. Framework-Specific Extensions

**File**: `frameworks/{framework}/database/extensions.sql`

Example for PostGraphile:
```sql
-- PostGraphile smart tags (only in postgraphile_test database)
COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\nInternal key';
COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\nUse author relation';
-- ... more smart tags
```

Example for FraiseQL:
```sql
-- FraiseQL v_* projection views (only in fraiseql_test database)
CREATE OR REPLACE VIEW v_user AS
SELECT pk_user, id, username, email, ...
FROM benchmark.tb_user;

-- FraiseQL tv_* composition views (only in fraiseql_test database)
CREATE OR REPLACE VIEW tv_user AS
SELECT id, jsonb_build_object(...) as data
FROM v_user;

-- FraiseQL sync functions (only in fraiseql_test database)
CREATE OR REPLACE FUNCTION fn_sync_tv_user(p_id UUID) AS ...
```

Example for Rails:
```sql
-- ActiveRecord schema migrations (only in rails_test database)
-- Rails will handle this via `rails db:migrate`
-- This file can be minimal or empty if Rails manages it
```

### 4. Test Configuration

Each framework's test config points to its own database:

**PostGraphile**: `frameworks/postgraphile/.env.test`
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=velocitybench
DB_PASSWORD=password
DB_NAME=postgraphile_test
DB_SCHEMA=benchmark
```

**FraiseQL**: `frameworks/fraiseql/.env.test`
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=velocitybench
DB_PASSWORD=password
DB_NAME=fraiseql_test
DB_SCHEMA=benchmark
```

**Rails**: `frameworks/rails/.env.test`
```
DATABASE_URL=postgresql://velocitybench:password@localhost:5432/rails_test
```

### 5. Test Runner Harness

**File**: `scripts/run-benchmarks.py`

Orchestrates sequential testing:

```python
#!/usr/bin/env python3
"""
Sequential benchmark runner for all frameworks.
Runs tests one at a time to avoid resource contention.
"""

import subprocess
import json
from datetime import datetime
from typing import Dict

FRAMEWORKS = [
    'postgraphile',
    'fraiseql',
    'rails',
    # ... 23 more
]

class BenchmarkRunner:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()

    def run_framework_tests(self, framework: str) -> Dict:
        """
        Run tests for a single framework:
        1. Setup transaction-based test isolation
        2. Run all tests
        3. Record results
        4. Cleanup

        Sequential ensures:
        - No resource contention
        - Clean benchmark results
        - Each framework gets full CPU/memory
        """
        print(f"\n{'='*60}")
        print(f"Testing: {framework}")
        print(f"{'='*60}")

        # Change to framework directory
        framework_dir = f'frameworks/{framework}'

        # Run tests
        try:
            result = subprocess.run(
                ['npm', 'test'],  # or 'pytest', 'bundle exec rspec', etc.
                cwd=framework_dir,
                capture_output=True,
                timeout=300,  # 5 minute timeout per framework
                text=True
            )

            # Parse results
            success = result.returncode == 0

            # Record metrics
            test_result = {
                'framework': framework,
                'success': success,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }

            return test_result

        except subprocess.TimeoutExpired:
            return {
                'framework': framework,
                'success': False,
                'error': 'Tests timed out after 300 seconds'
            }
        except Exception as e:
            return {
                'framework': framework,
                'success': False,
                'error': str(e)
            }

    def run_all_sequential(self):
        """Run all frameworks sequentially"""
        print(f"Starting sequential benchmark run")
        print(f"Frameworks to test: {len(FRAMEWORKS)}")

        for i, framework in enumerate(FRAMEWORKS, 1):
            print(f"\n[{i}/{len(FRAMEWORKS)}] {framework}")

            result = self.run_framework_tests(framework)
            self.results[framework] = result

            if result['success']:
                print(f"✅ {framework} passed")
            else:
                print(f"❌ {framework} failed")

        self._print_summary()

    def _print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results.values() if r['success'])
        failed = len(self.results) - passed

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {passed}/{len(self.results)}")
        print(f"Failed: {failed}/{len(self.results)}")
        print(f"Duration: {datetime.now() - self.start_time}")

        # Save results
        with open('benchmark-results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: benchmark-results.json")

if __name__ == '__main__':
    runner = BenchmarkRunner()
    runner.run_all_sequential()
```

---

## Implementation Steps

### Phase 1: Schema Foundation
1. Create `database/schema-template.sql` (Trinity Pattern only)
2. Create `database/setup.py` for database orchestration
3. Test with 2 frameworks (PostGraphile, FraiseQL)

### Phase 2: Framework Extensions
1. Create `frameworks/{framework}/database/extensions.sql` for each framework
2. Implement framework-specific setup
3. Verify isolated databases work

### Phase 3: Test Harness
1. Create `scripts/run-benchmarks.py`
2. Implement sequential execution
3. Add result collection and reporting

### Phase 4: Migration
1. Migrate existing tests to per-framework databases
2. Update CI/CD to use new setup
3. Remove old shared database references

---

## Database Directory Structure

```
database/
├── schema-template.sql          # Trinity Pattern (universal)
├── seed-data.sql                # Universal seed data
├── setup.py                     # Orchestration script
└── fraiseql_cqrs_schema.sql     # FraiseQL-specific (legacy, could move)

frameworks/
├── postgraphile/
│   ├── database/
│   │   └── extensions.sql       # Smart tags only
│   ├── src/
│   ├── tests/
│   └── .env.test
├── fraiseql/
│   ├── database/
│   │   └── extensions.sql       # v_*/tv_* views + sync functions
│   ├── main.py
│   ├── tests/
│   └── .env.test
├── rails/
│   ├── db/
│   │   └── migrate/             # Rails handles via migrations
│   ├── spec/
│   └── .env.test
└── [23 more frameworks...]

scripts/
└── run-benchmarks.py            # Sequential test runner
```

---

## Environment Variables

Global configuration: `DATABASE_SETUP_CONFIG`

```bash
# For setup phase
DB_HOST=localhost
DB_PORT=5432
DB_ADMIN_USER=postgres
DB_ADMIN_PASSWORD=postgres_admin_password
DB_TEST_USER=velocitybench
DB_TEST_PASSWORD=password

# Per-framework overrides (in .env.test files)
DB_NAME={framework}_test
DB_SCHEMA=benchmark
```

---

## Benefits of This Architecture

### 1. **True Isolation**
- Each framework has its own database
- Framework-specific features don't affect others
- Safe to run schema migrations

### 2. **Production-Like Testing**
- Tests run against real framework configuration
- Schema customizations are visible
- Optimizations are framework-specific

### 3. **Clean Benchmarks**
- Sequential execution = no resource contention
- Fair comparison between frameworks
- Results not affected by parallel processes

### 4. **Easy Debugging**
```bash
# Inspect PostGraphile's database
psql postgresql://velocitybench:password@localhost/postgraphile_test

# Inspect FraiseQL's database
psql postgresql://velocitybench:password@localhost/fraiseql_test

# Compare schema differences
diff postgraphile_test fraiseql_test
```

### 5. **Maintainability**
- Framework extensions in one place per framework
- Easy to add new frameworks
- Schema template is shared, extensions are isolated

---

## Performance Characteristics

```
Shared Database (Current)
├─ Setup Time: 1-2 min (once)
├─ Framework Addition: Slow (schema conflicts)
├─ Test Isolation: Medium (transactions only)
├─ Benchmark Validity: Low (resource contention)
└─ Debugging: Hard (mixed schema)

Per-Framework Databases (Proposed)
├─ Setup Time: 2-3 min (once, higher but one-time)
├─ Framework Addition: Fast (new DB, no conflicts)
├─ Test Isolation: Excellent (separate databases)
├─ Benchmark Validity: High (sequential, clean)
└─ Debugging: Easy (inspect each DB independently)
```

---

## Example: Adding a New Framework

### Step 1: Create Framework Directory
```bash
mkdir -p frameworks/new-framework/{database,tests,src}
```

### Step 2: Create Extensions File
**File**: `frameworks/new-framework/database/extensions.sql`
```sql
-- Framework-specific customizations only
-- Trinity Pattern schema already applied from template
```

### Step 3: Create Test Config
**File**: `frameworks/new-framework/.env.test`
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=velocitybench
DB_PASSWORD=password
DB_NAME=new_framework_test
```

### Step 4: Add to Setup Script
Update `FRAMEWORKS` list in `database/setup.py`:
```python
FRAMEWORKS = [
    # ... existing frameworks
    'new-framework',  # Add here
]
```

### Step 5: Add Tests
Create `frameworks/new-framework/tests/` with test files

That's it! The setup script now includes the new framework.

---

## Comparison: Shared vs Per-Framework Databases

### Shared Database (Current ❌)
```
postgraphile_test + fraiseql_test + rails_test + ...
│
└─ benchmark schema
   ├─ tb_user, tb_post, tb_comment (Trinity Pattern)
   ├─ v_user, v_post, v_comment (FraiseQL views)
   ├─ tv_user, tv_post, tv_comment (FraiseQL views)
   ├─ smart tags from PostGraphile
   ├─ fn_sync_tv_user, fn_sync_tv_post (FraiseQL functions)
   ├─ Rails migrations
   └─ Mix of all framework features!

Issues:
❌ Pollution: 26 frameworks' features in one schema
❌ Conflicts: Smart tags vs views vs functions
❌ Contention: Tests compete for connections
❌ Debugging: Can't see clean schema for one framework
```

### Per-Framework Databases (Proposed ✅)
```
postgraphile_test          fraiseql_test            rails_test
│                          │                        │
└─ benchmark schema        └─ benchmark schema      └─ benchmark schema
   ├─ tb_user, tb_post        ├─ tb_user, tb_post      ├─ tb_user, tb_post
   ├─ tb_comment              ├─ tb_comment            ├─ tb_comment
   └─ Smart tags only         ├─ v_user, v_post, ...   └─ Rails migrations
      (PostGraphile only)      ├─ tv_user, tv_post, ...
                               └─ Sync functions

Benefits:
✅ Clean: Each schema contains only what that framework needs
✅ Safe: Framework extensions don't conflict
✅ Fair: Sequential testing, no contention
✅ Debuggable: Inspect each framework's real schema
```

---

## Summary

This multi-database architecture:
- **Eliminates** schema pollution and framework interference
- **Enables** true framework-specific optimization
- **Provides** clean, valid benchmark results (sequential)
- **Simplifies** debugging (inspect each framework's DB)
- **Scales** easily to all 26 frameworks
- **Maintains** shared Trinity Pattern schema as the foundation

**Result**: VelocityBench becomes a legitimate benchmark suite where each framework is tested in its actual, optimized configuration.
