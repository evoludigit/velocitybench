# Master Index & Documentation Map

## Quick Navigation by Need

### "I'm an AI agent just arriving"
→ **START HERE**: [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md)
- 5-minute overview
- Essential concepts
- Common tasks quick reference
- Learning path

### "I need to understand the code structure"
→ [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md)
- Directory structure explained
- 35+ frameworks taxonomy
- Module dependency map
- Entry points by task
- Files to modify by task type

### "I need to look something up quickly"
→ **REFERENCE DOCS**:
- Database structure: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- API operations: [API_SCHEMAS.md](API_SCHEMAS.md)
- Error meanings: [ERROR_CATALOG.md](ERROR_CATALOG.md)
- SQL query patterns: [QUERY_PATTERNS.md](QUERY_PATTERNS.md)

### "I'm going to modify/add code"
→ **STEP-BY-STEP GUIDES**:
- How to modify: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md)
  - Adding endpoints (REST/GraphQL)
  - Adding database fields
  - Fixing bugs across frameworks
  - Writing tests
- Keeping code clean: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)

### "I need to write tests"
→ **TESTING GUIDES**:
- Test infrastructure: [TESTING_README.md](TESTING_README.md)
- Fixtures and factories: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
- Test isolation: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)
- Naming conventions: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)

### "I need to write SQL queries"
→ [QUERY_PATTERNS.md](QUERY_PATTERNS.md)
- Common query patterns
- Performance optimization
- Anti-patterns to avoid
- Testing query patterns

### "Something failed and I don't know why"
→ [ERROR_CATALOG.md](ERROR_CATALOG.md)
- Database errors
- REST API errors
- GraphQL errors
- Test errors
- Framework-specific errors
- Performance issues
- Debugging strategy

### "I'm optimizing performance"
→ **PERFORMANCE DOCS**:
- Baseline management: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)
- Tuning guide: [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)
- Query patterns: [QUERY_PATTERNS.md](QUERY_PATTERNS.md)

### "I need to keep code clean"
→ [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)
- Code standards
- Commit practices
- Documentation standards
- Checklists
- Regular maintenance

---

## Documentation Organization

### For AI Agents (Agent Experience - AX)

| Document | Purpose | Key Content |
|----------|---------|-------------|
| [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md) | Onboarding path | Concepts, tasks, navigation, tips |
| [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md) | Code structure map | Directory layout, entry points, file guide |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Database reference | Tables, fields, constraints, patterns |
| [API_SCHEMAS.md](API_SCHEMAS.md) | API reference | REST/GraphQL specs, examples, differences |
| [QUERY_PATTERNS.md](QUERY_PATTERNS.md) | SQL examples | Common queries, optimization, testing |
| [ERROR_CATALOG.md](ERROR_CATALOG.md) | Error solutions | Errors, causes, solutions, debugging |
| [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md) | How-to guide | Add endpoints, fields, fix bugs, tests |
| [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md) | Code standards | Quality, cleanliness, checklists |

### For Testing

| Document | Purpose | Key Content |
|----------|---------|-------------|
| [TESTING_README.md](TESTING_README.md) | Test overview | Test types, coverage, quick start |
| [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md) | Test data | Factory usage, examples, patterns |
| [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md) | Test cleanup | Transaction isolation, debugging |
| [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md) | Test naming | File, function, class naming patterns |
| [CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md) | Consistency | Same data across frameworks |

### For Performance

| Document | Purpose | Key Content |
|----------|---------|-------------|
| [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md) | Baselines | Capture, compare, track baselines |
| [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md) | Optimization | Query optimization, tuning, load testing |

### For Architecture

| Document | Purpose | Key Content |
|----------|---------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design | Components, flows, patterns |
| [ADD_FRAMEWORK_GUIDE.md](ADD_FRAMEWORK_GUIDE.md) | New framework | Step-by-step framework addition |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Setup guide | Environment, dependencies, commands |

---

## Search by Concept

### Database Operations
- **Schema reference**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- **Query examples**: [QUERY_PATTERNS.md](QUERY_PATTERNS.md)
- **Adding fields**: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md#adding-a-database-field)
- **Errors**: [ERROR_CATALOG.md](ERROR_CATALOG.md#database-errors)

### API Development
- **REST endpoints**: [API_SCHEMAS.md](API_SCHEMAS.md#rest-api-operations)
- **GraphQL operations**: [API_SCHEMAS.md](API_SCHEMAS.md#graphql-operations)
- **Adding endpoints**: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md#adding-a-new-api-endpoint)
- **Errors**: [ERROR_CATALOG.md](ERROR_CATALOG.md#rest-api-errors)

### Code Quality
- **Standards**: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#code-cleanliness-standards)
- **Commits**: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#git-practices)
- **Cleanup checklists**: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#checklists)

### Testing
- **Getting started**: [TESTING_README.md](TESTING_README.md#quick-start)
- **Writing tests**: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md#writing-tests-for-new-features)
- **Fixtures**: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
- **Debugging**: [ERROR_CATALOG.md](ERROR_CATALOG.md#test-errors)

### Performance
- **Query optimization**: [QUERY_PATTERNS.md](QUERY_PATTERNS.md#performance-optimization-patterns)
- **Baselines**: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)
- **Tuning**: [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)
- **Issues**: [ERROR_CATALOG.md](ERROR_CATALOG.md#performance-issues)

### Debugging
- **Errors**: [ERROR_CATALOG.md](ERROR_CATALOG.md)
- **Test failures**: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md#debugging-test-failures)
- **Queries**: [QUERY_PATTERNS.md](QUERY_PATTERNS.md#testing-query-patterns)

---

## By Use Case

### Adding a New Feature
1. Understand needs: [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md)
2. Plan implementation: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md)
3. Write code: [QUERY_PATTERNS.md](QUERY_PATTERNS.md), API examples
4. Add tests: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
5. Keep clean: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)

### Fixing a Bug
1. Understand error: [ERROR_CATALOG.md](ERROR_CATALOG.md)
2. Locate code: [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md)
3. Fix it: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md#fixing-a-bug-across-frameworks)
4. Test: [TESTING_README.md](TESTING_README.md)
5. Commit: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#git-practices)

### Optimizing Performance
1. Identify bottleneck: [ERROR_CATALOG.md](ERROR_CATALOG.md#performance-issues)
2. Optimize query: [QUERY_PATTERNS.md](QUERY_PATTERNS.md#performance-optimization-patterns)
3. Measure baseline: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)
4. Compare: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md#comparing-against-baselines)
5. Document: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md#baseline-update-policy)

### Writing Tests
1. Understand fixtures: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
2. Learn patterns: [TESTING_README.md](TESTING_README.md)
3. Use naming: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)
4. Ensure isolation: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)
5. Write test: [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md#writing-tests-for-new-features)

---

## Documentation Statistics

| Document | Lines | Size | Topics |
|----------|-------|------|--------|
| AGENT_QUICKSTART.md | 500+ | 20 KB | Onboarding, essentials, quick ref |
| CODEBASE_NAVIGATION.md | 600+ | 23 KB | Structure, entry points, patterns |
| DATABASE_SCHEMA.md | 700+ | 27 KB | Schema, fields, queries, ERD |
| API_SCHEMAS.md | 600+ | 24 KB | REST, GraphQL, examples |
| QUERY_PATTERNS.md | 600+ | 22 KB | Queries, optimization, testing |
| ERROR_CATALOG.md | 700+ | 26 KB | All errors, solutions, debugging |
| MODIFICATION_GUIDE.md | 700+ | 28 KB | Add endpoints, fields, fix bugs |
| REPOSITORY_HEALTH.md | 600+ | 25 KB | Standards, checklists, cleanup |
| TESTING_README.md | 300+ | 12 KB | Test overview, quick start |
| FIXTURE_FACTORY_GUIDE.md | 450+ | 18 KB | Factory usage, examples |
| TEST_ISOLATION_STRATEGY.md | 350+ | 13 KB | Isolation, debugging, patterns |
| TEST_NAMING_CONVENTIONS.md | 400+ | 14 KB | Naming patterns, markers, docstrings |
| CROSS_FRAMEWORK_TEST_DATA.md | 350+ | 13 KB | Consistency across frameworks |
| PERFORMANCE_BASELINE_MANAGEMENT.md | 400+ | 16 KB | Baselines, tracking, CI/CD |
| PERFORMANCE_TUNING_GUIDE.md | (existing) | 15 KB | Optimization strategies |
| ARCHITECTURE.md | (existing) | 15 KB | System design |
| ADD_FRAMEWORK_GUIDE.md | (existing) | 18 KB | Framework addition |
| DEVELOPMENT.md | (existing) | 16 KB | Setup and development |
| CONTRIBUTING.md | (existing) | 20 KB | Contribution guidelines |

**Total**: 5,000+ lines, 350+ KB of documentation

---

## Key Information by Type

### Trinity Pattern (Database)
- Definition: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#trinity-pattern-explained)
- Usage: [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md#key-rules-for-agents)
- Queries: [QUERY_PATTERNS.md](QUERY_PATTERNS.md)

### API Consistency
- REST spec: [API_SCHEMAS.md](API_SCHEMAS.md#rest-api-operations)
- GraphQL spec: [API_SCHEMAS.md](API_SCHEMAS.md#graphql-operations)
- Cross-framework: [CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md)

### Code Quality
- Standards: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)
- Pre-commit: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#pre-commit-checklist)
- Checklists: [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md#checklists)

### Testing Infrastructure
- Overview: [TESTING_README.md](TESTING_README.md)
- Fixtures: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
- Isolation: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)

---

## Common Patterns by Type

| Pattern | Document | Section |
|---------|----------|---------|
| User queries | [QUERY_PATTERNS.md](QUERY_PATTERNS.md#user-queries) | Get, list, create |
| Post queries | [QUERY_PATTERNS.md](QUERY_PATTERNS.md#post-queries) | With author, list, publish |
| Comment queries | [QUERY_PATTERNS.md](QUERY_PATTERNS.md#comment-queries) | On post, nested, create |
| N+1 fix | [QUERY_PATTERNS.md](QUERY_PATTERNS.md#n1-query-problem) | Use JOIN not loop |
| Test setup | [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md#real-world-test-examples) | Real-world examples |
| Error handling | [ERROR_CATALOG.md](ERROR_CATALOG.md) | Solutions for each error |
| Code addition | [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md) | Step-by-step guides |

---

## How to Use This Index

1. **Find your question** in "Quick Navigation by Need" or "By Use Case"
2. **Click the recommended document**
3. **Search within document** (Ctrl+F) for specific keyword
4. **Follow cross-references** to related docs for deeper info
5. **Bookmark these 3 docs** for frequent reference:
   - [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md) - Entry point
   - [ERROR_CATALOG.md](ERROR_CATALOG.md) - Debugging
   - [QUERY_PATTERNS.md](QUERY_PATTERNS.md) - Code patterns

---

## Document Update Timeline

**Created in this session** (Jan 31, 2025):
- AGENT_QUICKSTART.md - Agent onboarding
- CODEBASE_NAVIGATION.md - Code structure
- DATABASE_SCHEMA.md - Schema reference
- API_SCHEMAS.md - API reference
- QUERY_PATTERNS.md - Query examples
- ERROR_CATALOG.md - Error solutions
- MODIFICATION_GUIDE.md - How-to guide
- REPOSITORY_HEALTH.md - Code standards
- MASTER_INDEX.md - This file

**Existing documentation**:
- TESTING_README.md - Testing overview
- FIXTURE_FACTORY_GUIDE.md - Test fixtures
- TEST_ISOLATION_STRATEGY.md - Test isolation
- TEST_NAMING_CONVENTIONS.md - Test naming
- CROSS_FRAMEWORK_TEST_DATA.md - Cross-framework tests
- PERFORMANCE_BASELINE_MANAGEMENT.md - Performance tracking
- PERFORMANCE_TUNING_GUIDE.md - Performance optimization
- ARCHITECTURE.md - System architecture
- ADD_FRAMEWORK_GUIDE.md - Add framework
- DEVELOPMENT.md - Development setup
- CONTRIBUTING.md - Contributing guidelines

---

## Getting Started Path

1. **Right now**: Read [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md) (5 min)
2. **Next**: Read [CODEBASE_NAVIGATION.md](CODEBASE_NAVIGATION.md) (10 min)
3. **Then**: Pick a task from [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md)
4. **While coding**: Reference [QUERY_PATTERNS.md](QUERY_PATTERNS.md) and [ERROR_CATALOG.md](ERROR_CATALOG.md)
5. **When writing tests**: Use [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)
6. **Before committing**: Check [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)

---

## Quick Links by Framework

### Python Frameworks
- FastAPI: `frameworks/fastapi-rest/README.md`
- Flask: `frameworks/flask-rest/README.md`
- Strawberry: `frameworks/strawberry/README.md`
- Graphene: `frameworks/graphene/README.md`
- Ariadne: `frameworks/ariadne/README.md`

### Node.js Frameworks
- Express: `frameworks/express-rest/README.md`
- Apollo: `frameworks/apollo-server/README.md`
- GraphQL Yoga: `frameworks/graphql-yoga/README.md`

### Other Frameworks
- Go: `frameworks/gin-rest/`, `frameworks/go-gqlgen/`
- Java: `frameworks/java-spring-boot/`
- Rust: `frameworks/rust-actix-web/`, `frameworks/async-graphql/`

---

## Next Steps

**For agents new to project**:
→ [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md)

**For questions**:
→ Find relevant doc above

**For code examples**:
→ [QUERY_PATTERNS.md](QUERY_PATTERNS.md), [MODIFICATION_GUIDE.md](MODIFICATION_GUIDE.md)

**For debugging**:
→ [ERROR_CATALOG.md](ERROR_CATALOG.md)

**For cleanup**:
→ [REPOSITORY_HEALTH.md](REPOSITORY_HEALTH.md)

---

**Happy coding!** 🚀

