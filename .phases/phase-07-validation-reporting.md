# Phase 7: Validation & Reporting

## Objective

Run the complete benchmark suite with all frameworks working, produce publication-ready results, and add quality-of-life improvements for ongoing maintenance.

## Prerequisites

- Phases 1-6 complete (all 33 frameworks passing smoke tests with <1% errors)

## Tasks

### 7.1 Full Benchmark Run

**Steps:**
1. Ensure medium dataset is loaded: `DATA_VOLUME=medium docker compose up -d postgres`
2. Wait for PostgreSQL to fully initialize with seed data
3. Run full sequential benchmark:
   ```bash
   python tests/benchmark/bench_sequential.py --duration 20 --concurrency 40
   ```
4. Review results for any remaining issues
5. If any framework has >1% errors, investigate and fix before proceeding

**Expected duration:** ~45 minutes (33 frameworks x ~80s each including startup/cooldown)

### 7.2 Auto-Categorized Results

**File:** `tests/benchmark/bench_sequential.py` (report generation section)

**Add category metadata to FRAMEWORKS dict:**
```python
"strawberry": {
    "category": "graphql",
    "language": "python",
    "compose_service": "strawberry",
    ...
}
```

**Categories:**
- `rest` — REST API frameworks
- `graphql` — Standard GraphQL (with DataLoaders or equivalent)
- `graphql-precomputed` — FraiseQL and similar pre-computation patterns
- `graphql-schema-first` — Schema-first GraphQL (Ariadne, PostGraphile)

**Report output changes:**
- Add separate leaderboard tables per category
- Add language column to each table
- Add overall cross-category comparison with category label
- Keep existing per-query tables for detailed analysis

**Example output:**
```markdown
## REST Frameworks — Q1 (sorted by RPS)
| Framework | Language | RPS | p50 ms | p99 ms |
|-----------|----------|----:|-------:|-------:|
| gin-rest | Go | 5850 | 6.6 | 11.6 |
| actix-web-rest | Rust | 5501 | 7.0 | 12.0 |
| spring-boot-orm | Java | 4693 | 7.7 | 20.1 |
| express-rest | Node.js | ... | ... | ... |
| fastapi-rest | Python | ... | ... | ... |
| flask-rest | Python | ... | ... | ... |

## GraphQL Frameworks — Q1 (sorted by RPS)
| Framework | Language | RPS | p50 ms | p99 ms |
...
```

### 7.3 Framework Health Dashboard (`make status`)

Already defined in Phase 1 (task 1.4). In this phase, polish and finalize:

- Color output (green/red/yellow)
- Show last benchmark date and RPS for each framework
- Show which queries are supported (Q1/Q2/Q2b/Q3/M1)
- Export to JSON for CI consumption

### 7.4 Update Benchmark Registry

**File:** `tests/benchmark/bench_sequential.py`

Ensure all 33 frameworks are registered with:
- Correct service names matching docker-compose.yml
- Correct URLs and ports
- Correct query format (GraphQL POST vs REST GET)
- Correct health endpoint paths
- No `None` entries for Q2b (all known bugs should be fixed)

**Also update:**
- `tests/qa/framework_registry.yaml` — if it exists, ensure all frameworks listed
- `docker-compose.yml` — ensure all frameworks in benchmark profile
- `.github/workflows/unit-tests.yml` — ensure all frameworks in CI matrix

### 7.5 N+1 Guard Update

**File:** `tests/qa/test_n1_detection.py`

Extend N+1 detection to cover newly fixed frameworks:
- Add test entries for all GraphQL frameworks
- Verify DataLoader patterns work correctly
- Set appropriate thresholds per framework

### 7.6 Parity Test Update

**File:** `tests/qa/test_parity.py`

Extend cross-framework parity validation:
- All 33 frameworks should return consistent data for identical queries
- Account for framework-specific response shapes (REST vs GraphQL)
- Add tolerance for field ordering differences

### 7.7 Final Report Generation

Generate the definitive benchmark report:

```bash
# Full run with all frameworks
python tests/benchmark/bench_sequential.py --duration 30 --concurrency 40

# Validate results
make validate

# Generate categorized report
# (Report saved to reports/bench-sequential-YYYY-MM-DD.md)
```

**Report should include:**
1. Executive summary with key findings
2. Per-category leaderboards (REST, GraphQL, Pre-computed)
3. Per-query detailed tables (Q1, Q2, Q2b, Q3)
4. Mutation performance table (M1)
5. Framework metadata (language, version, async model, N+1 strategy)
6. Methodology notes (dataset size, concurrency, measurement duration)

### 7.8 Documentation Update

**Files to update:**
- `README.md` — Update framework count, add latest results summary
- `CHANGELOG.md` — Add entry for this work
- `docs/FRAMEWORK_SELECTION_GUIDE.md` — Update with latest benchmark data

## Verification

- [ ] All 33 frameworks start and pass health checks
- [ ] All 33 frameworks achieve <1% error rate on all supported queries
- [ ] Categorized report generated with REST/GraphQL/Pre-computed leaderboards
- [ ] `make status` shows 33/33 healthy
- [ ] `make validate` passes (smoke + parity + N+1)
- [ ] CI pipelines pass for all 33 frameworks
- [ ] README updated with accurate framework count and latest results
