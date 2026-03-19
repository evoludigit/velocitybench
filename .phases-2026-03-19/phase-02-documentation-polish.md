# Phase 2: Documentation Polish

## Objective

Update outdated references, fix broken URLs, and ensure all documentation reflects the current state of the project.

## Success Criteria

- [ ] README.md references latest benchmark results (March 2026, not February)
- [ ] CONTRIBUTING.md uses correct GitHub remote URL
- [ ] All internal doc cross-references are consistent

## Tasks

### 2.1 Update README.md benchmark date and link

**File:** `README.md`

**Line 5 — current:**
```
> **Latest run**: February 2026 · sequential isolation · 40 workers · 20s per framework · dataset: 10 000 users / 50 000 posts / 200 000 comments
```

**Action:** Update to March 2026. Verify worker count and duration match `bench_sequential.py` defaults.

**Line 11 — current:**
```
Full tables: [reports/bench-sequential-2026-02-22.md](reports/bench-sequential-2026-02-22.md)
```

**Action:** Update link to `reports/bench-sequential-2026-03-04.md`.

**Additionally:** Review the benchmark results table in README.md. If it shows February numbers, update the top performers with March data from `reports/bench-sequential-2026-03-04.md`.

### 2.2 Fix CONTRIBUTING.md GitHub URL

**File:** `CONTRIBUTING.md` line 42

**Current:**
```bash
git clone https://github.com/velocitybench/velocitybench.git
```

**Action:** Replace with:
```bash
git clone https://github.com/evoludigit/velocitybench.git
```

**Also:** Search all .md files for `velocitybench/velocitybench` to catch any other occurrences:
```bash
grep -r "velocitybench/velocitybench" *.md docs/*.md
```

### 2.3 Cross-reference consistency check

**Action:** Run a sweep for broken internal links in markdown files:
```bash
grep -roh '\[.*\](docs/[^)]*\|reports/[^)]*)' *.md docs/*.md | sort -u
```

Verify each referenced file exists. Fix or remove dead links.

## Verification

- `grep "February 2026" README.md` returns no hits
- `grep "2026-02-22" README.md` returns no hits
- `grep "velocitybench/velocitybench" *.md docs/*.md` returns no hits
- All markdown links in README.md resolve to existing files

## Status
[x] Complete
