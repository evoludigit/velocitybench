# VelocityBench FraiseQL Integration - Phase Plan

## Overview

This document outlines the phased approach to integrating FraiseQL v2 across VelocityBench, adapting existing Python frameworks and building new backends for TypeScript, Go, Java, and PHP.

**Start Date:** February 1, 2026
**Target Completion:** Phase 8 (Finalization)
**Status:** Planning → Phase 1

---

## Phase Roadmap

```
Phase 1: Foundation & Schema
    ↓
Phase 2: Python Framework Adaptation (FastAPI, Flask, Strawberry, Graphene)
    ↓
Phase 3: TypeScript/Node.js Backend (Express, Fastify, etc.)
    ↓
Phase 4: Go Backend (Gin, Echo, etc.)
    ↓
Phase 5: Java Backend (Spring Boot, Quarkus, etc.)
    ↓
Phase 6: PHP Backend (Laravel, Symfony, etc.)
    ↓
Phase 7: Cross-Language Testing & Validation
    ↓
Phase 8: Finalization (Documentation, Cleanup, Performance)
```

---

## Quick Status

| Phase | Title | Status | Progress |
|-------|-------|--------|----------|
| 1 | Foundation & Schema | [ ] Not Started | 0% |
| 2 | Python Adaptation | [ ] Not Started | 0% |
| 3 | TypeScript Backend | [ ] Not Started | 0% |
| 4 | Go Backend | [ ] Not Started | 0% |
| 5 | Java Backend | [ ] Not Started | 0% |
| 6 | PHP Backend | [ ] Not Started | 0% |
| 7 | Cross-Language Testing | [ ] Not Started | 0% |
| 8 | Finalization | [ ] Not Started | 0% |

---

## Key Principles

1. **Shared Test Infrastructure**: Common test suites for all backends
2. **FraiseQL-First Architecture**: All query/mutation logic in compiled schema
3. **Language Idiomaticity**: Each backend follows language conventions
4. **Deterministic Execution**: No runtime resolvers, all logic in database/schema
5. **Performance Parity**: All backends achieve equivalent performance

---

## File Structure (Target)

```
velocitybench/
├── .phases/
│   ├── README.md (this file)
│   ├── phase-01-foundation.md
│   ├── phase-02-python-adaptation.md
│   ├── phase-03-typescript-backend.md
│   ├── phase-04-go-backend.md
│   ├── phase-05-java-backend.md
│   ├── phase-06-php-backend.md
│   ├── phase-07-testing-validation.md
│   └── phase-08-finalize.md
│
├── fraiseql-schema/
│   ├── schema.fraiseql.py       # Python source of truth
│   ├── schema.fraiseql.ts       # TypeScript equivalent
│   ├── schema.fraiseql.go       # Go equivalent
│   ├── schema.fraiseql.java     # Java equivalent
│   ├── schema.fraiseql.php      # PHP equivalent
│   ├── schema.json              # Compiled intermediate
│   └── schema.compiled.json     # Optimized for runtime
│
├── frameworks/
│   ├── fraiseql-python/         # Shared Python base
│   │   ├── fastapi-rest/
│   │   ├── flask-rest/
│   │   ├── strawberry/
│   │   └── graphene/
│   ├── fraiseql-typescript/     # TypeScript backends
│   │   ├── express/
│   │   ├── fastify/
│   │   └── apollo-server/
│   ├── fraiseql-go/             # Go backends
│   │   ├── gin/
│   │   ├── echo/
│   │   └── fiber/
│   ├── fraiseql-java/           # Java backends
│   │   ├── spring-boot/
│   │   └── quarkus/
│   └── fraiseql-php/            # PHP backends
│       ├── laravel/
│       └── symfony/
│
└── tests/
    ├── common/                  # Shared test infrastructure
    │   ├── test_endpoints_base.py
    │   ├── test_mutations_base.py
    │   ├── test_security_*.py
    │   └── test_perf_*.py
    └── integration/
        └── test_fraiseql_parity.py
```

---

## Dependencies & Blockers

None at start. Each phase is relatively independent after Phase 1.

---

## Success Criteria (Overall)

- [ ] FraiseQL schema compiles without errors
- [ ] All 5 language generators produce identical type systems
- [ ] Python frameworks adapted and tests passing
- [ ] TypeScript backend fully functional
- [ ] Go backend fully functional
- [ ] Java backend fully functional
- [ ] PHP backend fully functional
- [ ] Cross-language parity tests passing
- [ ] Zero TODO/FIXME in code
- [ ] No .phases/ directory in final commit

---

## Time Investment Notes

- Phase 1: Schema design and validation
- Phases 2-6: Parallel backend implementation (language-specific)
- Phase 7: Integration testing
- Phase 8: Polish and cleanup

---

## References

- FraiseQL v2: `/home/lionel/code/fraiseql`
- Language Generators: `/home/lionel/code/fraiseql/docs/guides/language-generators.md`
- Current Python Frameworks: `frameworks/fastapi-rest`, `frameworks/flask-rest`, etc.
- VelocityBench Docs: This directory
