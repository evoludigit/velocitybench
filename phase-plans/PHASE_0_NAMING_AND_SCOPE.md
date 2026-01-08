# Phase 0: Naming & Scope Refinement

**Status**: Pre-implementation planning
**Duration**: 1-2 weeks (concurrent with Week 1)
**Owner**: Tech Lead + Community
**Impact**: Critical for project positioning and adoption

---

## Overview

Before launching Phase 9+ quality improvements, FraiseQL should consider transitioning to a more neutral, ecosystem-agnostic name that reflects its true purpose: **a comprehensive, framework-agnostic GraphQL/REST performance benchmarking suite**.

Current name `velocitybench` is:
- ✅ Descriptive of current work
- ✅ Technically accurate (for FraiseQL context)
- ❌ Implies FraiseQL is primary focus (only 1 of 28 frameworks)
- ❌ Misleading to new users (suggests FraiseQL benchmarking tool, not suite)
- ❌ Limits adoption (looks FraiseQL-specific)
- ❌ Confuses scope (28+ frameworks, not just FraiseQL)

---

## Naming Options

### Option A: GraphQL/REST Performance Suite (Recommended)

**Name Candidates**:
- `graphql-rest-benchmark-suite`
- `api-framework-benchmark-suite`
- `graphql-benchmark-suite`
- `rest-benchmark-suite`

**Advantages**:
- Neutral, ecosystem-agnostic
- Clear about scope (GraphQL + REST)
- Attracts ecosystem-wide audience
- Professional, publication-ready
- SEO-friendly
- Emphasizes performance aspect

**Disadvantages**:
- Loses FraiseQL origin context
- Requires rebranding effort

**Example**: `graphql-rest-performance-benchmark`

---

### Option B: Framework Comparison Suite

**Name Candidates**:
- `framework-performance-comparison`
- `graphql-framework-benchmark`
- `web-api-framework-benchmark`

**Advantages**:
- Emphasizes comparative aspect
- Clear about what it does
- Neutral to all frameworks
- Academic/publication friendly

**Disadvantages**:
- Generic (many "framework benchmarks" exist)
- Doesn't emphasize performance
- Longer names

---

### Option C: Keep FraiseQL but Expand Scope

**Name Candidates**:
- `fraiseql-benchmarking-framework`
- `fraiseql-suite` (with docs clarifying it benchmarks 28+ frameworks)
- `fraiseql` (as umbrella project for benchmarking)

**Advantages**:
- Leverages existing brand/work
- Shorter names
- Existing SEO/recognition
- Honors original development

**Disadvantages**:
- Still implies FraiseQL-focused
- Confuses new users about scope
- Limits appeal to broader GraphQL community

---

## Recommendation

**Option A: `graphql-rest-performance-benchmark`**

This positions the project as:
- **Independent**: Not tied to any single framework
- **Comprehensive**: Tests 28+ frameworks across 8 languages
- **Legitimate**: Suitable for academic papers, industry reports
- **Professional**: Publication-ready benchmarking suite
- **Community-focused**: Welcomes framework authors and users

---

## Implementation Plan

### Phase 0.1: Decision & Branding (Days 1-3)

**Tasks**:
1. **Community input** (if open source)
   - Post naming RFC (Request for Comments)
   - Gather feedback on options
   - Decide on final name

2. **Messaging refinement**
   - Define elevator pitch
   - Update project description
   - Clarify scope vs prior work

3. **Branding assets** (if going with new name)
   - Logo/icon (if needed)
   - Project banner
   - Social media descriptions

**Deliverables**:
- ✅ Final project name decision
- ✅ Updated tagline/description
- ✅ Messaging guidelines

---

### Phase 0.2: Repository Reorganization (Days 4-7)

**If renaming repository** (this requires planning):

**Option A: Fork/Clone** (Recommended for publications)
```bash
# Keep original velocitybench for history
git clone --mirror \
  https://github.com/user/velocitybench.git \
  graphql-rest-benchmark.git

# Create new repo with clean history or fresh start
git clone --bare graphql-rest-benchmark.git
```

**Option B: In-place Rename** (If no external references)
```bash
# GitHub: Settings → Danger Zone → Rename Repository
# Update local clones:
git remote set-url origin <new-url>
```

**Tasks**:
1. **Update repository metadata**
   - Rename repository (if applicable)
   - Update README title/description
   - Update GitHub topic tags

2. **Update documentation**
   - All docs reference correct project name
   - Update code references
   - Update CI/CD pipeline names

3. **Update references**
   - docker-compose service names (optional)
   - Docker image registry paths
   - CI/CD config files
   - Logging/metrics labels

4. **Update directory structure**
   - Rename main directory if needed
   - Update README in root
   - Update setup instructions

**Deliverables**:
- ✅ Repository renamed/reorganized
- ✅ All documentation updated
- ✅ CI/CD pipelines functional
- ✅ Setup instructions accurate

---

### Phase 0.3: Documentation & Scope Clarity (Days 5-7)

**Critical documents to create/update**:

1. **Updated README.md** (Root level)
   - Clear description (not FraiseQL-specific)
   - Lists all 28+ frameworks
   - Emphasizes breadth of testing
   - Honest about scope and limitations

2. **SCOPE_AND_LIMITATIONS.md** (expanded)
   - What IS tested (syntax, throughput, latency, resources)
   - What ISN'T tested (network, business logic, security)
   - Why these boundaries matter
   - How results should/shouldn't be used

3. **PROJECT_HISTORY.md** (optional but good)
   - Origins in FraiseQL work
   - Evolution to comprehensive benchmark
   - Acknowledgments of original work
   - Relationship to FraiseQL project

**Example Updated README Section**:

```markdown
# GraphQL/REST Performance Benchmark Suite

A comprehensive, multi-framework benchmarking suite testing 28+ GraphQL and REST
frameworks across 8 programming languages (Python, Node.js, Go, Java, Rust, PHP,
Ruby, C#).

Originally developed as part of FraiseQL performance research, this project has
evolved into a neutral, framework-agnostic benchmarking infrastructure suitable
for comparative performance analysis, framework selection, and optimization research.

## What We Test

- **Syntax Complexity**: Simple queries → parameterized → complex → mixed workloads
- **Throughput**: RPS across 1-2000 concurrent users
- **Latency**: p50, p95, p99, p99.9 response times
- **Resource Usage**: CPU, memory, I/O under load
- **Cold vs Warm**: Startup performance vs steady-state

See [SCOPE_AND_LIMITATIONS.md](SCOPE_AND_LIMITATIONS.md) for complete boundaries.

## What We Don't Test

- Network latency (all on localhost)
- Business logic (synthetic workloads)
- Security/authentication
- Data correctness
- Long-term stability

## Frameworks Included

28 GraphQL and REST implementations across:

- Python: Strawberry, Graphene, FastAPI, Flask
- TypeScript: Apollo, Express, PostGraphile
- Go: gqlgen, gin, graphql-go
- Java: Spring Boot
- Rust: Async-graphql, Actix
- PHP: Laravel
- Ruby: Rails
- C#: .NET
- Managed: Hasura

Plus ORM variants and "naive" implementations for pattern comparison.
```

**Deliverables**:
- ✅ Crystal-clear README
- ✅ Comprehensive SCOPE_AND_LIMITATIONS.md
- ✅ Optional PROJECT_HISTORY.md
- ✅ Framework list clearly displayed

---

## Risks & Mitigation

### Risk: Breaking changes if renaming repository

**Mitigation**:
- Create GitHub redirect (auto-forwards old URLs)
- Update all CI/CD references before rename
- Test that clone/pull still works
- Document migration in release notes

**Actions**:
```bash
# Before rename:
git remote add origin-backup <old-url>
git tag v1.0-old-name

# After rename:
# GitHub handles redirects automatically
# Update docs/CI to point to new URL
```

### Risk: Community confusion about scope change

**Mitigation**:
- Create CHANGELOG entry explaining transition
- Clear messaging about what hasn't changed
- Honest about relationship to FraiseQL
- Emphasize continued neutrality

**Example CHANGELOG**:
```markdown
## v1.0: Transition to Framework-Neutral Benchmarking Suite

### What Changed
- Repository renamed from `velocitybench`
  to `graphql-rest-performance-benchmark`
- Project scope clarified (tests 28+ frameworks, not just FraiseQL)
- Documentation expanded with comprehensive scope/limitations
- Messaging updated to reflect comprehensive nature

### What Didn't Change
- All 28 framework implementations
- Complete test infrastructure
- Performance testing methodology
- Quality standards

### Why?
The project has evolved beyond its origins as FraiseQL-specific work
into a comprehensive, neutral benchmarking suite. This rename better
reflects the project's true purpose and breadth.

See PROJECT_HISTORY.md for full context.
```

### Risk: Loss of FraiseQL attribution

**Mitigation**:
- Create PROJECT_HISTORY.md
- Credit FraiseQL in README
- Link back to original FraiseQL project
- Acknowledge FraiseQL as origin

**Example**:
```markdown
## Project History

Originally developed as the FraiseQL Performance Assessment project
(see [fraiseql](https://github.com/...)), this benchmarking suite
has expanded into a comprehensive, framework-agnostic testing framework.

We acknowledge FraiseQL as the origin of this work and maintain
a neutral stance toward all frameworks tested.

[See PROJECT_HISTORY.md for details](PROJECT_HISTORY.md)
```

---

## Timeline Integration

This phase runs **concurrently with Week 1** of the main improvement plan:

```
Week 1 Timeline:

Days 1-2: Phase 0 (naming/scope)
  └─ Decide on name
  └─ Update documentation
  └─ Clarify messaging

Days 1-2: Phase 9 (quality) - PARALLEL
  └─ Create TESTING_STANDARDS.md
  └─ Setup CI/CD pipeline

Days 3-7: Both phases continue in parallel
  └─ Phase 0: Complete documentation
  └─ Phase 9: Start Python tests
```

**No blocking dependencies** - both can proceed simultaneously.

---

## Deliverables Summary

### Renamed Project (Option A example)

```
graphql-rest-performance-benchmark/
├── README.md (updated - neutral, framework-agnostic)
├── SCOPE_AND_LIMITATIONS.md (expanded, comprehensive)
├── PROJECT_HISTORY.md (explains FraiseQL origin)
├── CONTRIBUTING.md (framework-neutral guidelines)
├── frameworks/ (all 28+ implementations)
├── tests/ (comprehensive test infrastructure)
└── ... (rest of project)

GitHub:
  Repository: graphql-rest-performance-benchmark
  Description: "Comprehensive GraphQL/REST framework performance benchmarking suite"
  Topics: benchmark, graphql, rest, performance, framework-comparison
  Redirects: velocitybench → graphql-rest-performance-benchmark
```

### Documentation Changes

**New/Updated Files**:
- ✅ README.md (completely rewritten, framework-neutral)
- ✅ SCOPE_AND_LIMITATIONS.md (expanded, clear boundaries)
- ✅ PROJECT_HISTORY.md (explains origins and evolution)
- ✅ CONTRIBUTING.md (updated for neutral stance)
- ✅ All framework READMEs (framework-specific, part of Phase 9)

**Messaging Key Points**:
- Clear: This tests 28+ frameworks, not just one
- Honest: What IS and ISN'T tested
- Neutral: No advocacy for any framework
- Professional: Publication and research ready
- Community: Welcoming to framework authors

---

## Success Criteria

Phase 0 is complete when:

✅ Project name decided (or kept as-is with updated messaging)
✅ Repository organized/renamed (if applicable)
✅ README clearly describes scope (framework-neutral)
✅ SCOPE_AND_LIMITATIONS.md comprehensive and accessible
✅ All team members understand messaging
✅ CI/CD pipelines and references updated
✅ No confusion about project scope/purpose

---

## Decision Matrix

### Should You Rename?

**Rename (Option A) if**:
- ✅ Planning to publish research/paper
- ✅ Want to position as neutral benchmarking tool
- ✅ Targeting broad GraphQL/REST community
- ✅ Want to deemphasize FraiseQL origins

**Keep Name (Option C) if**:
- ✅ Want to maintain FraiseQL brand connection
- ✅ Limited external distribution planned
- ✅ Want to emphasize FraiseQL context
- ✅ Community feedback prefers status quo

**Recommendation**: **Option A** if you want production-quality publication. **Option C** if internal/research tool.

---

## Next Steps

1. **Decision** (Day 1-2):
   - Review options with team
   - Get community input (if applicable)
   - Decide: rename or enhanced messaging

2. **Execution** (Days 3-7):
   - If renaming: update repo, docs, CI/CD
   - If keeping: enhance messaging and scope clarity
   - Create/update critical documents

3. **Validation** (End of Week 1):
   - New users can quickly understand scope
   - Project description is clear and neutral
   - No confusion about what is/isn't tested
   - CI/CD all working with new names

---

## Appendix: Alternative Naming Ideas

If you want other options to consider:

### Academic/Research Focus
- `graphql-rest-performance-analysis`
- `framework-performance-evaluation-suite`
- `comparative-api-framework-benchmark`

### Community/Ecosystem Focus
- `api-framework-benchmark` (broadest)
- `web-framework-benchmark` (includes all REST)
- `query-language-benchmark` (emphasizes GraphQL)

### Specific Use Case Focus
- `framework-selection-benchmark` (helps choose frameworks)
- `performance-optimization-suite` (helps optimize)
- `api-implementation-benchmark` (generic, safe)

### Playful/Branded
- `framebench` (too generic)
- `api-perf-league` (comparative feel)
- `framework-olympics` (competitive feel)

**Recommendation remains**: **`graphql-rest-performance-benchmark`** - clear, neutral, professional.

---

## Conclusion

Phase 0 is optional but **highly recommended** before Phase 9+ execution, especially if:
- You plan to publish results
- You want to attract framework authors
- You need broad ecosystem adoption
- This will be a long-term project

If you skip Phase 0:
- Phase 9+ proceeds unchanged
- Can rename later (more effort)
- Current name works for internal use

**Decision**: Make in Day 1-2, proceed with Phase 9 either way.

