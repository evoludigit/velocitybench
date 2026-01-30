# Architecture Decision Records (ADRs)

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made during the project. This directory contains all ADRs for VelocityBench.

## Format

Each ADR follows the template:

```markdown
# ADR-001: Title of Decision

## Status
Accepted | Proposed | Deprecated | Superseded

## Context
Why did we need to make this decision?

## Decision
What we decided to do and why

## Consequences
What are the positive and negative impacts?

## Alternatives
What other options did we consider?
```

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-trinity-pattern.md) | Trinity Pattern for Data Layer | Accepted | 2024-01-15 |
| [002](002-framework-isolation.md) | Framework Isolation via Virtual Environments | Accepted | 2024-01-16 |
| [003](003-multi-language-support.md) | Multi-Language Framework Support | Accepted | 2024-01-17 |
| [004](004-synthetic-data-generation.md) | Synthetic Data Generation with vLLM | Accepted | 2024-01-18 |
| [005](005-ruff-linting.md) | Python Code Quality with Ruff | Accepted | 2024-01-19 |
| [006](006-authentication-exclusion.md) | Authentication-by-Design Exclusion | Accepted | 2025-01-30 |
| [007](007-framework-selection-criteria.md) | Framework Selection Criteria | Accepted | 2025-01-30 |
| [008](008-multi-venv-architecture.md) | Multi-Virtual Environment Architecture | Accepted | 2025-01-30 |
| [009](009-six-dimensional-qa-testing.md) | Six-Dimensional QA Testing Strategy | Accepted | 2025-01-30 |
| [010](010-benchmarking-methodology.md) | Performance Benchmarking Methodology | Accepted | 2025-01-30 |
| [011](011-trinity-pattern-implementation.md) | Trinity Pattern Implementation Deep Dive | Accepted | 2025-01-30 |
| [012](012-synthetic-data-reproducibility.md) | Synthetic Data Reproducibility | Accepted | 2025-01-30 |

## Rationale

### Core Architecture (ADR 001-003)
- **Trinity Pattern**: Separates write-optimized tables, projection views, and composition views for flexible API design
- **Isolation**: Each framework gets its own database, venv, and dependencies for fair benchmarking
- **Multi-Language**: Support 8+ languages to provide comprehensive framework comparison

### Data & Quality (ADR 004-005, 012)
- **Synthetic Data**: Use AI to generate realistic comment and persona data for realistic workloads
- **Modern Tooling**: Use Ruff for Python quality (faster, more comprehensive than flake8)
- **Reproducibility**: Seed-based generation with quality filtering ensures consistent datasets

### Security & Scope (ADR 006-007)
- **Authentication Exclusion**: Intentionally exclude auth for fair benchmarking and clear security model
- **Framework Selection**: 39 frameworks across 8 languages selected by popularity and architectural diversity

### Python Infrastructure (ADR 008)
- **Multi-Venv Architecture**: 8 isolated virtual environments for clean dependency management

### Testing & Performance (ADR 009-010)
- **Six-Dimensional QA**: Comprehensive validation (schema, query, N+1, consistency, config, performance)
- **Benchmarking Methodology**: JMeter-based testing with warm-up cycles and regression detection

### Implementation Details (ADR 011)
- **Trinity Pattern Deep Dive**: Materialized views, indexing strategies, and query optimization techniques

## Recommended Reading Order

### For New Contributors
Start here to understand VelocityBench's architecture:

1. **[ADR-001: Trinity Pattern](001-trinity-pattern.md)** - Core data layer design
2. **[ADR-007: Framework Selection Criteria](007-framework-selection-criteria.md)** - Which frameworks and why
3. **[ADR-006: Authentication Exclusion](006-authentication-exclusion.md)** - Security model and intended use
4. **[ADR-002: Framework Isolation](002-framework-isolation.md)** - How frameworks are isolated

### For Framework Developers
If you're implementing a new framework:

1. **[ADR-001: Trinity Pattern](001-trinity-pattern.md)** - Required data access pattern
2. **[ADR-011: Trinity Pattern Implementation](011-trinity-pattern-implementation.md)** - Detailed implementation guide
3. **[ADR-009: Six-Dimensional QA Testing](009-six-dimensional-qa-testing.md)** - How your implementation will be validated
4. **[ADR-008: Multi-Venv Architecture](008-multi-venv-architecture.md)** - Python dependency management (Python frameworks only)

### For Performance Analysis
If you're analyzing or running benchmarks:

1. **[ADR-010: Benchmarking Methodology](010-benchmarking-methodology.md)** - How benchmarks are run
2. **[ADR-004: Synthetic Data Generation](004-synthetic-data-generation.md)** - Understanding the test data
3. **[ADR-012: Synthetic Data Reproducibility](012-synthetic-data-reproducibility.md)** - How data consistency is ensured
4. **[ADR-009: Six-Dimensional QA Testing](009-six-dimensional-qa-testing.md)** - Validation before benchmarking

### For Infrastructure/DevOps
If you're setting up or maintaining VelocityBench:

1. **[ADR-002: Framework Isolation](002-framework-isolation.md)** - Database and environment isolation
2. **[ADR-003: Multi-Language Support](003-multi-language-support.md)** - Language runtime requirements
3. **[ADR-008: Multi-Venv Architecture](008-multi-venv-architecture.md)** - Python virtual environment structure
4. **[ADR-010: Benchmarking Methodology](010-benchmarking-methodology.md)** - Performance testing infrastructure

## Adding a New ADR

1. Create a new file: `docs/adr/NNN-title.md`
2. Use the template above
3. Update this README with the new ADR entry
4. Open a PR with the ADR for discussion

## References

- [ADR GitHub](https://adr.github.io/)
- [MADR Format](https://adr.github.io/madr/)
- [VelocityBench DEVELOPMENT.md](../../DEVELOPMENT.md)
