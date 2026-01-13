# Phase 4 Implementation Roadmap - Full Framework Migration

**Status**: Planning Phase
**Date**: 2026-01-10
**Estimated Duration**: 2-3 weeks (24 frameworks)
**Depends On**: Phase 1-3 (Complete ✅)

---

## Executive Summary

Phase 4 involves migrating all remaining 24 frameworks from the legacy shared database approach to the new per-framework isolated database architecture. This document provides a detailed roadmap for systematic implementation.

**Goal**: Enable all 26 frameworks to use the multi-database architecture
**Target**: Complete framework extensions for all 26 frameworks
**Outcome**: Production-ready benchmark suite with fair, reproducible testing

---

## Frameworks to Migrate (24 Remaining)

### Node.js/JavaScript (5 frameworks)
- [ ] Apollo Server GraphQL
- [ ] GraphQL Yoga
- [ ] Fastify GraphQL
- [ ] Express GraphQL
- [ ] Mercurius (Fastify plugin)

### Python (4 frameworks)
- [ ] Strawberry GraphQL
- [ ] Graphene Django
- [ ] Ariadne
- [ ] ASGI GraphQL

### Ruby (2 frameworks)
- [ ] Rails GraphQL
- [ ] Hanami GraphQL

### Java (4 frameworks)
- [ ] Spring GraphQL
- [ ] Micronaut GraphQL
- [ ] Quarkus GraphQL
- [ ] Play Framework GraphQL

### C#/.NET (3 frameworks)
- [ ] Hot Chocolate
- [ ] Entity Framework Core
- [ ] GraphQL.NET

### Go (2 frameworks)
- [ ] gqlgen
- [ ] graphql-go

### PHP (2 frameworks)
- [ ] GraphQL-core PHP
- [ ] webonyx/graphql-php

### Rust (2 frameworks)
- [ ] Async-graphql
- [ ] Juniper

---

## Phase 4 Implementation Strategy

### Approach: Template-Driven Migration

**Pattern for Each Framework**:
```
1. Create framework extension file (5-15 min per framework)
2. Create .env.test configuration (2 min per framework)
3. Register framework in setup.py (1 min per framework)
4. Test database creation (2 min per framework)
5. Verify framework compatibility (5 min per framework)
```

**Total per framework**: ~15-25 minutes
**Total for 24 frameworks**: ~6-10 hours of actual work

---

## Detailed Implementation Steps

### Step 1: Create Framework Extension Template

**File**: `frameworks/{framework}/database/extensions.sql`

**Template for Minimal Framework** (no special views):
```sql
-- {Framework} Framework Extensions
-- Applied ONLY to the {framework}_test database
-- The Trinity Pattern tables are already created by schema-template.sql

SET search_path TO benchmark, public;

-- No framework-specific extensions required
-- {Framework} uses the Trinity Pattern tables directly
-- from the schema template

-- Future: Add framework-specific views, functions, or configurations here
```

**Template for Framework with Views** (like FraiseQL):
```sql
-- {Framework} Framework Extensions
-- Applied ONLY to the {framework}_test database

SET search_path TO benchmark, public;

-- Layer 2: Projection views (optional)
CREATE OR REPLACE VIEW v_user AS
SELECT u.pk_user, u.id, u.username, u.email, ...
FROM benchmark.tb_user u;

-- Layer 3: Composition views (optional, framework-specific)
CREATE OR REPLACE VIEW tv_user AS
SELECT u.id, jsonb_build_object(...) as data
FROM v_user u;

-- Framework-specific functions (optional)
CREATE OR REPLACE FUNCTION fn_sync_{framework}_user(...) AS ...;
```

### Step 2: Create Framework Configuration

**File**: `frameworks/{framework}/.env.test`

**Template**:
```bash
# {Framework} Test Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=velocitybench
DB_PASSWORD=password
DB_NAME={framework}_test
DB_SCHEMA=benchmark

# Framework-specific settings (if needed)
{FRAMEWORK_SETTING}={value}
```

### Step 3: Register Framework in Setup Script

**File**: `database/setup.py`

**Modification**:
```python
FRAMEWORKS = [
    'postgraphile',      # ✅ Complete
    'fraiseql',          # ✅ Complete
    'apollo-server',     # Add here
    'graphql-yoga',      # Add here
    'strawberry',        # Add here
    # ... etc
]
```

### Step 4: Framework-Specific Customization

Some frameworks may need special handling:

**Rails**:
- Extensions can be minimal (Trinity Pattern only)
- Rails handles migrations separately
- May need `config/database.yml` integration

**Django**:
- Extensions can be minimal
- Django ORM handles relationships
- May need settings integration

**Spring GraphQL**:
- Extensions can be minimal
- Java/Spring handles object mapping
- May need entity class mapping

**Rust/Go**:
- Extensions can be minimal
- Static type systems require schema generation
- May need build script integration

---

## Migration Execution Plan

### Week 1: Node.js/JavaScript Frameworks (5 frameworks)
```
Day 1: Apollo, Yoga, Fastify (3 frameworks)
  • Create extensions.sql for each
  • Create .env.test for each
  • Register in setup.py
  • Test database creation

Day 2: Express, Mercurius (2 frameworks)
  • Same process as Day 1
  • Verify compatibility with existing tests
```

### Week 2: Python, Ruby, Java Frameworks (10 frameworks)
```
Day 1: Strawberry, Graphene, Ariadne, ASGI (4 Python frameworks)
  • Create framework extensions
  • Register and test

Day 2: Rails, Hanami (2 Ruby frameworks)
  • Create framework extensions
  • Handle migration differences

Day 3: Spring, Micronaut, Quarkus, Play (4 Java frameworks)
  • Create framework extensions
  • Register and test
```

### Week 3: C#/.NET, Go, PHP, Rust (9 frameworks)
```
Day 1: Hot Chocolate, EF Core, GraphQL.NET (3 C#/.NET)
  • Create framework extensions
  • Register and test

Day 2: gqlgen, graphql-go (2 Go)
  • Create framework extensions
  • Handle Go-specific configuration

Day 3: PHP frameworks (2)
  • Create framework extensions
  • Register and test

Day 4: async-graphql, Juniper (2 Rust)
  • Create framework extensions
  • Handle Rust build integration
```

---

## Framework-Specific Extensions Guide

### Minimal Extension (Most Frameworks)

**For frameworks that don't need custom views or functions:**

```sql
-- {Framework} Extensions
-- Trinity Pattern schema from schema-template.sql is sufficient

SET search_path TO benchmark, public;

-- Minimal framework-specific configuration
-- (most frameworks don't need anything special)
```

**Frameworks that use this approach**:
- Apollo Server, GraphQL Yoga, Fastify GraphQL
- Rails, Hanami, Django
- Spring GraphQL, Micronaut GraphQL
- gqlgen, graphql-go
- Hot Chocolate, GraphQL.NET
- async-graphql, Juniper

### View-Based Extension (Composition Frameworks)

**For frameworks that benefit from denormalized views:**

```sql
-- {Framework} Extensions
-- Three-layer view system for zero N+1 queries

SET search_path TO benchmark, public;

-- Projection views
CREATE OR REPLACE VIEW v_user AS SELECT ... FROM benchmark.tb_user;
CREATE OR REPLACE VIEW v_post AS SELECT ... FROM benchmark.tb_post;
CREATE OR REPLACE VIEW v_comment AS SELECT ... FROM benchmark.tb_comment;

-- Composition views (framework-specific format)
CREATE OR REPLACE VIEW tv_user AS SELECT ... FROM v_user;
```

**Frameworks that might use this approach**:
- Strawberry (if using CQRS patterns)
- Custom optimization projects

### Smart Tags Extension (GraphQL Schema Control)

**For frameworks that expose schema metadata:**

```sql
-- {Framework} Extensions
-- Schema control directives for GraphQL exposure

SET search_path TO benchmark, public;

-- Hide internal primary keys
COMMENT ON COLUMN benchmark.tb_user.pk_user IS E'@omit all\nInternal PK';

-- Hide internal foreign keys
COMMENT ON COLUMN benchmark.tb_post.fk_author IS E'@omit all\nUse author relation';
```

**Frameworks that might use this approach**:
- Strawberry (with directives)
- Custom implementations with directive support

---

## Quality Assurance for Phase 4

### Checklist Per Framework

For each framework:
- [ ] Extension file created with appropriate content
- [ ] .env.test file created with correct connection string
- [ ] Framework registered in `FRAMEWORKS` list in setup.py
- [ ] `python database/setup.py {framework}` succeeds
- [ ] Framework test runner auto-detected correctly
- [ ] Database tables present and accessible
- [ ] Framework-specific views/functions (if any) working
- [ ] Tests can connect to isolated database

### Automated Testing

```bash
# For each framework after registration:
python database/setup.py {framework}          # Setup database
python scripts/run-benchmarks.py {framework}  # Run tests
```

### Expected Output

```
✅ {framework} database ready ({framework}_test)
✅ Framework tests passed
✅ Results collected in benchmark-results.json
```

---

## Integration Points

### 1. CI/CD Updates Needed

**Current**: Tests run against shared database
**After Phase 4**: Tests run against isolated per-framework databases

```yaml
# Before Phase 4
test-suite:
  - npm test (all frameworks)
  - Database: postgraphile_test

# After Phase 4
test-suite:
  - for each framework:
      - setup framework database
      - run framework tests
      - collect results
```

### 2. GitHub Actions Updates

**Add to CI/CD pipeline**:
```yaml
- name: Setup Framework Databases
  run: python database/setup.py

- name: Run Sequential Benchmarks
  run: python scripts/run-benchmarks.py

- name: Publish Results
  uses: actions/upload-artifact@v2
  with:
    name: benchmark-results
    path: benchmark-results.json
```

### 3. Environment Configuration

**Required environment variables in CI/CD**:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_ADMIN_USER=postgres
DB_ADMIN_PASSWORD=postgres
DB_TEST_USER=velocitybench
DB_TEST_PASSWORD=password
BENCHMARK_TIMEOUT=300
```

---

## Automation Opportunity

### Python Script to Auto-Generate Extensions

**Create**: `scripts/generate-framework-extension.py`

```python
#!/usr/bin/env python3
"""Generate extension.sql template for a new framework"""

import sys
from pathlib import Path

def generate_extension(framework_name):
    """Generate minimal extension.sql for framework"""
    template = f"""-- {framework_name} Framework Extensions
-- Trinity Pattern schema from schema-template.sql is sufficient

SET search_path TO benchmark, public;

-- No framework-specific extensions required
-- {framework_name} uses Trinity Pattern tables directly
"""
    return template

if __name__ == '__main__':
    framework = sys.argv[1]
    ext_file = Path(f"frameworks/{framework}/database/extensions.sql")
    ext_file.parent.mkdir(parents=True, exist_ok=True)
    ext_file.write_text(generate_extension(framework))
    print(f"✅ Created {ext_file}")
```

**Usage**:
```bash
python scripts/generate-framework-extension.py apollo-server
python scripts/generate-framework-extension.py strawberry
# ... etc
```

---

## Validation Checklist - Phase 4 Complete

- [ ] All 26 frameworks registered in `FRAMEWORKS` list
- [ ] All 26 frameworks have extension files
- [ ] All 26 frameworks have .env.test files
- [ ] `python database/setup.py` works for all frameworks
- [ ] All framework databases created successfully
- [ ] All framework tests can connect to isolated databases
- [ ] `python scripts/run-benchmarks.py` runs all 26 frameworks
- [ ] Results collected for all frameworks
- [ ] CI/CD pipeline updated
- [ ] Documentation updated
- [ ] Performance baseline established

---

## Risk Assessment & Mitigation

### Risk 1: Framework Test Incompatibility
**Mitigation**: Start with well-known frameworks (Apollo, Rails, Spring), test migration approach
**Fallback**: Keep legacy tests as reference during migration

### Risk 2: Custom Framework Configurations
**Mitigation**: Create framework-specific extension templates, document special cases
**Fallback**: Minimal extensions work for all frameworks as baseline

### Risk 3: Database Permission Issues
**Mitigation**: Verify database user and password in setup.py
**Fallback**: Clear documentation of environment variable setup

### Risk 4: CI/CD Integration Complexity
**Mitigation**: Implement incrementally, test 5 frameworks first, then scale
**Fallback**: Maintain separate test scripts for legacy and new approaches

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Frameworks Migrated | 24/24 | Count in FRAMEWORKS list |
| Setup Success Rate | 100% | `python database/setup.py` for all |
| Test Execution | All pass | `run-benchmarks.py` results |
| Benchmark Validity | ✅ | Sequential execution, no contention |
| Documentation | Complete | Phase 4 docs added to project |
| CI/CD Integration | Working | Automated in GitHub Actions |

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Planning (current) | 1 day | ✅ Complete |
| Node.js (5 frameworks) | 1 day | Planning complete |
| Python/Ruby/Java (10 frameworks) | 2 days | Node.js complete |
| C#/.NET/Go/PHP/Rust (9 frameworks) | 2 days | Python/Ruby/Java complete |
| Testing & Validation | 1-2 days | All frameworks migrated |
| CI/CD Integration | 1 day | Testing complete |
| Documentation | 0.5 days | All work complete |
| **Total** | **7-8 days** | |

---

## Deliverables for Phase 4

Upon completion:
- ✅ 24 new framework extension files
- ✅ 24 new .env.test configuration files
- ✅ Updated setup.py with all frameworks registered
- ✅ Updated run-benchmarks.py with all frameworks tested
- ✅ Updated CI/CD pipeline configuration
- ✅ Updated documentation with Phase 4 results
- ✅ benchmark-results.json with all 26 frameworks
- ✅ benchmark-results.html with visual comparison

---

## Getting Started - First Framework

### Example: Migrate Apollo Server

**Step 1**: Create extension file
```bash
mkdir -p frameworks/apollo-server/database
```

**Step 2**: Create `frameworks/apollo-server/database/extensions.sql`
```sql
-- Apollo Server Framework Extensions
-- Trinity Pattern schema from schema-template.sql is sufficient

SET search_path TO benchmark, public;

-- No framework-specific extensions required
-- Apollo Server uses Trinity Pattern tables directly
```

**Step 3**: Create `frameworks/apollo-server/.env.test`
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=velocitybench
DB_PASSWORD=password
DB_NAME=apollo_server_test
DB_SCHEMA=benchmark
```

**Step 4**: Add to `database/setup.py`
```python
FRAMEWORKS = [
    'postgraphile',
    'fraiseql',
    'apollo-server',  # Add here
    # ... rest
]
```

**Step 5**: Test
```bash
python database/setup.py apollo-server
python scripts/run-benchmarks.py apollo-server
```

---

## Next Actions

1. **Immediate** (Today):
   - Review this roadmap
   - Confirm framework list is complete
   - Identify any missing frameworks

2. **Day 1-2**:
   - Start with Node.js frameworks (quickest wins)
   - Create extension templates
   - Register in setup.py
   - Test database creation

3. **Day 3-7**:
   - Complete remaining frameworks
   - Test each migration
   - Update CI/CD

4. **Day 8+**:
   - Final validation
   - Performance baseline
   - Documentation update
   - Production deployment

---

## Sign-Off & Approval

**Phase 4 Roadmap Status**: Ready for Implementation

- Created: 2026-01-10
- Estimated Start: 2026-01-11
- Estimated Completion: 2026-01-20
- Approved for Execution: [ ] Yes [ ] No

**Notes**: This roadmap is detailed, actionable, and designed for systematic execution. Each framework follows the same process, allowing for parallel work if needed.

---

## Appendix: Framework Auto-Detection Reference

**setup.py** will automatically detect framework type and add to test runner.

**Framework detection logic** (auto-detect by files present):
```
package.json → npm test (Node.js)
requirements.txt → pytest (Python)
Gemfile → bundle exec rspec (Ruby)
pom.xml → mvn test (Java Maven)
build.gradle → ./gradlew test (Java Gradle)
Cargo.toml → cargo test (Rust)
go.mod → go test (Go)
composer.json → vendor/bin/phpunit (PHP)
```

All frameworks should include appropriate test runner configuration files.

